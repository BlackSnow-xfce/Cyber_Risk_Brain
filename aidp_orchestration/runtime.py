"""Machine-readable local persistence for runner results and audit events."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from .contracts import (
    AIDPState, ArchitectReviewDisposition, ArchitectReviewRequest, ArchitectReviewResult,
    AuditEvent, AuthenticatedProductOwner, CodexExecutionResult, ProductOwnerApprovalContext,
    ProductOwnerAuthorizationEvidence, ProductOwnerDecision, ProductOwnerDecisionEvent,
    ProductOwnerDecisionState, ProductOwnerOperation, ReworkContract,
    ExternalStatusProjectionV1, ExternalWatcherHealth, ExternalWatcherOutcome,
    WatcherHeartbeatV1, ExecutionStatus, ScopeCompliance, ValidationResult,
    canonical_digest, utc_now,
)


class LocalRuntimeStore:
    """Stores orchestration runtime data outside the versioned worktree."""

    def __init__(self, root: Path):
        self.root = root

    @classmethod
    def for_repository(cls, repository_root: Path) -> "LocalRuntimeStore":
        git_path = subprocess.check_output(
            ("git", "rev-parse", "--git-path", "aidp-orchestration/runtime"),
            cwd=repository_root,
            text=True,
        ).strip()
        path = Path(git_path)
        return cls(path if path.is_absolute() else repository_root / path)

    def persist_result(self, result: CodexExecutionResult) -> Path:
        path = self.root / "results" / f"{result.execution_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"timestamp": utc_now(), "codex_execution_result": result}
        with path.open("x", encoding="utf-8") as stream:
            stream.write(_json(payload) + "\n")
        return path

    def latest_execution_result(self, task_id: str) -> CodexExecutionResult | None:
        directory = self.root / "results"
        paths = tuple(directory.glob("*.json")) if directory.exists() else ()
        matches: list[tuple[datetime, CodexExecutionResult]] = []
        for path in paths:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
            value = wrapper.get("codex_execution_result") if isinstance(wrapper, dict) else None
            if not isinstance(value, dict) or value.get("task_id") != task_id:
                continue
            validations = value.get("validation_results")
            if not isinstance(validations, list):
                raise ValueError("execution validation evidence is malformed")
            result = CodexExecutionResult(
                execution_id=_string(value, "execution_id"),
                task_id=_string(value, "task_id"),
                start_commit=_string(value, "start_commit"),
                resulting_commit=(str(value["resulting_commit"]) if value.get("resulting_commit") is not None else None),
                changed_files=_string_tuple(value.get("changed_files")),
                validation_results=tuple(
                    ValidationResult(
                        name=_string(item, "name"),
                        passed=(item["passed"] if isinstance(item.get("passed"), bool) else _invalid_boolean()),
                        detail=_string(item, "detail"),
                    )
                    for item in validations if isinstance(item, dict)
                ),
                status=ExecutionStatus(_string(value, "status")),
                failure_reason=(str(value["failure_reason"]) if value.get("failure_reason") is not None else None),
                scope_compliance=ScopeCompliance(_string(value, "scope_compliance")),
            )
            if len(result.validation_results) != len(validations):
                raise ValueError("execution validation evidence is malformed")
            timestamp = datetime.fromisoformat(_string(wrapper, "timestamp"))
            matches.append((timestamp, result))
        if not matches:
            return None
        matches.sort(key=lambda item: item[0])
        return matches[-1][1]

    def append_audit(self, event: AuditEvent) -> Path:
        path = self.root / "audit.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(_json(event) + "\n")
        return path

    def persist_external_status(self, projection: ExternalStatusProjectionV1) -> Path:
        path = self.root / "external-status" / "current.json"
        return self._atomic_projection(path, _json({"external_status_projection": projection}))

    def persist_watcher_heartbeat(self, heartbeat: WatcherHeartbeatV1) -> Path:
        path = self.root / "external-status-internal" / "watcher-heartbeat.json"
        if path.exists():
            previous = self.watcher_heartbeat()
            if previous is None or heartbeat.watcher_instance_id != previous.watcher_instance_id or heartbeat.sequence != previous.sequence + 1 or heartbeat.previous_heartbeat_digest != previous.heartbeat_digest or heartbeat.observed_at < previous.observed_at:
                raise ValueError("watcher heartbeat replay or rollback")
        elif heartbeat.sequence != 0 or heartbeat.previous_heartbeat_digest is not None:
            raise ValueError("first watcher heartbeat is invalid")
        return self._atomic_projection(path, _json({"watcher_heartbeat": heartbeat}))

    def watcher_heartbeat(self) -> WatcherHeartbeatV1 | None:
        path = self.root / "external-status-internal" / "watcher-heartbeat.json"
        if not path.exists(): return None
        value = self._read_exact(path, "watcher_heartbeat")
        return WatcherHeartbeatV1(
            schema_version=_string(value,"schema_version"), watcher_instance_id=_string(value,"watcher_instance_id"),
            sequence=int(value["sequence"]), started_at=datetime.fromisoformat(_string(value,"started_at")),
            observed_at=datetime.fromisoformat(_string(value,"observed_at")), expected_interval_seconds=float(value["expected_interval_seconds"]),
            status=ExternalWatcherHealth(_string(value,"status")),
            last_outcome=ExternalWatcherOutcome(_string(value,"last_outcome")),
            previous_heartbeat_digest=value.get("previous_heartbeat_digest"), heartbeat_digest=_string(value,"heartbeat_digest"))

    @staticmethod
    def _atomic_projection(path: Path, serialized: str) -> Path:
        if path.is_symlink() or path.parent.is_symlink(): raise ValueError("status path cannot be symbolic link")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        encoded = serialized.rstrip("\n") + "\n"
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, path); _sync_parent(path.parent)
            if path.read_text(encoding="utf-8") != encoded: raise RuntimeError("status persistence verification failed")
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def persist_architect_request(self, request: ArchitectReviewRequest) -> Path:
        return self._persist_immutable(
            self.root / "architect-review-requests" / f"{request.review_request_id}.json",
            _json({"architect_review_request": request}), request.review_request_id,
        )

    def persist_architect_result(self, result: ArchitectReviewResult) -> Path:
        return self._persist_immutable(
            self.root / "architect-review-results" / f"{result.review_result_id}.json",
            _json({"architect_review_result": result}), result.review_result_id,
        )

    def persist_architect_attempt(self, request_id: str, payload: dict[str, object]) -> Path:
        path = self.root / "architect-review-attempts" / f"{request_id}.json"
        return self._persist_immutable(path, _json({"architect_review_attempt": payload}), request_id)

    def architect_attempt_exists(self, request_id: str) -> bool:
        return (self.root / "architect-review-attempts" / f"{request_id}.json").is_file()

    def latest_architect_result(self, task_id: str) -> ArchitectReviewResult | None:
        from .architect_review import parse_architect_review_result

        candidates: list[ArchitectReviewResult] = []
        directory = self.root / "architect-review-results"
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                envelope = json.loads(path.read_text(encoding="utf-8"))
                payload = envelope.get("architect_review_result") if isinstance(envelope, dict) else None
                if isinstance(payload, dict) and payload.get("task_id") == task_id:
                    candidates.append(parse_architect_review_result(json.dumps(payload)))
        if not candidates:
            return None
        ordered = sorted(candidates, key=lambda item: item.review_iteration)
        if len({item.review_iteration for item in ordered}) != len(ordered):
            raise ValueError("Architect result history is ambiguous")
        return ordered[-1]

    def persist_product_owner_approval_context(self, context: ProductOwnerApprovalContext) -> Path:
        return self._persist_immutable(
            self.root / "approval-contexts" / f"{context.approval_context_id}.json",
            _json({"product_owner_approval_context": context}), context.approval_context_id,
        )

    def product_owner_approval_context(self, context_id: str) -> ProductOwnerApprovalContext:
        _identity(context_id, "approval_context_id")
        value = self._read_exact(
            self.root / "approval-contexts" / f"{context_id}.json",
            "product_owner_approval_context",
        )
        required = {
            "schema_version", "approval_context_id", "task_id", "repository_identity",
            "repository_remote_identity", "expected_state", "expected_lifecycle_version",
            "policy_version", "implementation_execution_id", "architect_review_id",
            "architect_result_digest", "product_commit", "issued_at", "expires_at",
            "nonce_digest", "context_digest",
        }
        if set(value) != required:
            raise ValueError("approval context fields do not match schema")
        context = ProductOwnerApprovalContext(
            schema_version=_string(value, "schema_version"),
            approval_context_id=_string(value, "approval_context_id"),
            task_id=_string(value, "task_id"),
            repository_identity=_string(value, "repository_identity"),
            repository_remote_identity=_string(value, "repository_remote_identity"),
            expected_state=AIDPState(_string(value, "expected_state")),
            expected_lifecycle_version=_string(value, "expected_lifecycle_version"),
            policy_version=_string(value, "policy_version"),
            implementation_execution_id=_string(value, "implementation_execution_id"),
            architect_review_id=_string(value, "architect_review_id"),
            architect_result_digest=_string(value, "architect_result_digest"),
            product_commit=_string(value, "product_commit"),
            issued_at=datetime.fromisoformat(_string(value, "issued_at")),
            expires_at=datetime.fromisoformat(_string(value, "expires_at")),
            nonce_digest=_string(value, "nonce_digest"),
            context_digest=_string(value, "context_digest"),
        )
        if context.approval_context_id != context_id:
            raise ValueError("approval context filename identity mismatch")
        return context

    def product_owner_approval_contexts(self) -> tuple[ProductOwnerApprovalContext, ...]:
        directory = self.root / "approval-contexts"
        if not directory.exists():
            return ()
        return tuple(self.product_owner_approval_context(path.stem) for path in sorted(directory.glob("*.json")))

    def persist_product_owner_decision(self, decision: ProductOwnerDecision) -> Path:
        return self._persist_immutable(
            self.root / "product-owner-decisions" / f"{decision.decision_id}.json",
            _json({"product_owner_decision": decision}), decision.decision_id,
        )

    def product_owner_decision(self, decision_id: str) -> ProductOwnerDecision:
        _identity(decision_id, "decision_id")
        value = self._read_exact(
            self.root / "product-owner-decisions" / f"{decision_id}.json",
            "product_owner_decision",
        )
        principal_value = _mapping(value, "principal")
        authorization_value = _mapping(value, "authorization")
        if set(value) != {
            "schema_version", "decision_id", "approval_context_id", "approval_context_digest",
            "principal", "authorization", "operation", "reason", "decided_at",
            "client_identity", "command_id", "command_payload_digest", "nonce_digest",
            "integrity_digest",
        }:
            raise ValueError("Product Owner decision fields do not match schema")
        if set(principal_value) != {
            "principal_id", "issuer", "subject", "authentication_event_id", "authenticated_at",
            "authentication_method", "assurance_level", "session_reference",
        }:
            raise ValueError("authenticated Product Owner fields do not match schema")
        if set(authorization_value) != {
            "authorization_reference", "principal_id", "operation", "task_id",
            "repository_identity", "policy_version", "evaluated_at", "valid_until",
        }:
            raise ValueError("Product Owner authorization fields do not match schema")
        principal = AuthenticatedProductOwner(
            principal_id=_string(principal_value, "principal_id"),
            issuer=_string(principal_value, "issuer"),
            subject=_string(principal_value, "subject"),
            authentication_event_id=_string(principal_value, "authentication_event_id"),
            authenticated_at=datetime.fromisoformat(_string(principal_value, "authenticated_at")),
            authentication_method=_string(principal_value, "authentication_method"),
            assurance_level=_string(principal_value, "assurance_level"),
            session_reference=_string(principal_value, "session_reference"),
        )
        valid_until = authorization_value.get("valid_until")
        authorization = ProductOwnerAuthorizationEvidence(
            authorization_reference=_string(authorization_value, "authorization_reference"),
            principal_id=_string(authorization_value, "principal_id"),
            operation=ProductOwnerOperation(_string(authorization_value, "operation")),
            task_id=_string(authorization_value, "task_id"),
            repository_identity=_string(authorization_value, "repository_identity"),
            policy_version=_string(authorization_value, "policy_version"),
            evaluated_at=datetime.fromisoformat(_string(authorization_value, "evaluated_at")),
            valid_until=datetime.fromisoformat(valid_until) if isinstance(valid_until, str) else None,
        )
        decision = ProductOwnerDecision(
            schema_version=_string(value, "schema_version"),
            decision_id=_string(value, "decision_id"),
            approval_context_id=_string(value, "approval_context_id"),
            approval_context_digest=_string(value, "approval_context_digest"),
            principal=principal,
            authorization=authorization,
            operation=ProductOwnerOperation(_string(value, "operation")),
            reason=value.get("reason") if isinstance(value.get("reason"), str) else None,
            decided_at=datetime.fromisoformat(_string(value, "decided_at")),
            client_identity=_string(value, "client_identity"),
            command_id=_string(value, "command_id"),
            command_payload_digest=_string(value, "command_payload_digest"),
            nonce_digest=_string(value, "nonce_digest"),
            integrity_digest=_string(value, "integrity_digest"),
        )
        if decision.decision_id != decision_id:
            raise ValueError("Product Owner decision filename identity mismatch")
        return decision

    def persist_product_owner_idempotency(
        self, principal_id: str, command_id: str, payload_digest: str, decision_id: str,
    ) -> Path:
        identity = canonical_digest({"principal_id": principal_id, "command_id": command_id})
        payload = {
            "principal_id": principal_id, "command_id": command_id,
            "payload_digest": payload_digest, "decision_id": decision_id,
        }
        return self._persist_immutable(
            self.root / "product-owner-idempotency" / f"{identity}.json",
            _json({"product_owner_idempotency": payload}), identity,
        )

    def product_owner_idempotency(self, principal_id: str, command_id: str) -> tuple[str, str] | None:
        identity = canonical_digest({"principal_id": principal_id, "command_id": command_id})
        path = self.root / "product-owner-idempotency" / f"{identity}.json"
        if not path.exists():
            return None
        value = self._read_exact(path, "product_owner_idempotency")
        if value.get("principal_id") != principal_id or value.get("command_id") != command_id:
            raise ValueError("idempotency identity mismatch")
        return _string(value, "payload_digest"), _string(value, "decision_id")

    def append_product_owner_decision_event(self, event: ProductOwnerDecisionEvent) -> Path:
        directory = self.root / "product-owner-decision-events" / event.decision_id
        existing = tuple(sorted(directory.glob("*.json"))) if directory.exists() else ()
        if any(path.name.endswith(f"-{event.event_id}.json") for path in existing):
            raise ValueError("Product Owner decision event identity already exists")
        sequence = len(existing)
        if sequence == 0 and event.previous_event_digest is not None:
            raise ValueError("first decision event cannot have a predecessor")
        if sequence > 0:
            previous = self.product_owner_decision_events(event.decision_id)[-1]
            if event.previous_event_digest != previous.event_digest:
                raise ValueError("decision event chain mismatch")
        return self._persist_immutable(
            directory / f"{sequence:04d}-{event.event_id}.json",
            _json({"product_owner_decision_event": event}), event.event_id,
        )

    def product_owner_decision_events(self, decision_id: str) -> tuple[ProductOwnerDecisionEvent, ...]:
        _identity(decision_id, "decision_id")
        directory = self.root / "product-owner-decision-events" / decision_id
        paths = tuple(sorted(directory.glob("*.json"))) if directory.exists() else ()
        events: list[ProductOwnerDecisionEvent] = []
        previous: ProductOwnerDecisionEvent | None = None
        for index, path in enumerate(paths):
            value = self._read_exact(path, "product_owner_decision_event")
            if set(value) != {
                "event_id", "decision_id", "approval_context_id", "previous_state",
                "current_state", "event_type", "binding_digest", "timestamp",
                "reason_code", "previous_event_digest", "event_digest",
            }:
                raise ValueError("Product Owner decision event fields do not match schema")
            event = ProductOwnerDecisionEvent(
                event_id=_string(value, "event_id"),
                decision_id=_string(value, "decision_id"),
                approval_context_id=_string(value, "approval_context_id"),
                previous_state=(ProductOwnerDecisionState(_string(value, "previous_state")) if value.get("previous_state") is not None else None),
                current_state=ProductOwnerDecisionState(_string(value, "current_state")),
                event_type=_string(value, "event_type"),
                binding_digest=_string(value, "binding_digest"),
                timestamp=datetime.fromisoformat(_string(value, "timestamp")),
                reason_code=_string(value, "reason_code"),
                previous_event_digest=(str(value["previous_event_digest"]) if value.get("previous_event_digest") is not None else None),
                event_digest=_string(value, "event_digest"),
            )
            if event.decision_id != decision_id or (previous is None) != (event.previous_event_digest is None):
                raise ValueError("decision event lineage mismatch")
            if previous is not None and event.previous_event_digest != previous.event_digest:
                raise ValueError("decision event digest chain mismatch")
            if not path.name.startswith(f"{index:04d}-") or not path.name.endswith(f"{event.event_id}.json"):
                raise ValueError("decision event filename identity mismatch")
            events.append(event)
            previous = event
        return tuple(events)

    def recorded_product_owner_decisions(self) -> tuple[ProductOwnerDecision, ...]:
        directory = self.root / "product-owner-decisions"
        decisions: list[ProductOwnerDecision] = []
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                decision = self.product_owner_decision(path.stem)
                events = self.product_owner_decision_events(decision.decision_id)
                if len(events) == 1 and events[0].current_state is ProductOwnerDecisionState.RECORDED:
                    decisions.append(decision)
        return tuple(decisions)

    def product_owner_decisions(self) -> tuple[ProductOwnerDecision, ...]:
        directory = self.root / "product-owner-decisions"
        if not directory.exists():
            return ()
        return tuple(self.product_owner_decision(path.stem) for path in sorted(directory.glob("*.json")))

    def append_product_owner_confirmation_attempt(self, payload: dict[str, object]) -> Path:
        path = self.root / "product-owner-confirmation-attempts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = _json({"product_owner_confirmation_attempt": payload}) + "\n"
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_parent(path.parent)
        return path

    def append_product_owner_transaction(self, decision_id: str, payload: dict[str, object]) -> Path:
        path = self.root / "product-owner-transactions" / f"{decision_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = _json({"product_owner_transaction": payload}) + "\n"
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_parent(path.parent)
        return path

    def product_owner_transaction(self, decision_id: str) -> tuple[dict[str, object], ...]:
        _identity(decision_id, "decision_id")
        path = self.root / "product-owner-transactions" / f"{decision_id}.jsonl"
        if not path.exists():
            return ()
        events: list[dict[str, object]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            envelope = _strict_json_loads(line)
            if not isinstance(envelope, dict) or set(envelope) != {"product_owner_transaction"}:
                raise ValueError("Product Owner transaction envelope is malformed")
            event = envelope["product_owner_transaction"]
            required = {
                "schema_version", "decision_id", "approval_context_id", "binding_digest",
                "operation", "state", "timestamp", "projection_commit",
                "previous_event_digest", "event_digest",
            }
            if not isinstance(event, dict) or set(event) != required or event.get("decision_id") != decision_id:
                raise ValueError("Product Owner transaction identity mismatch")
            if event.get("schema_version") != "product-owner-transaction-v1":
                raise ValueError("Product Owner transaction schema is unsupported")
            if event.get("operation") not in {item.value for item in ProductOwnerOperation}:
                raise ValueError("Product Owner transaction operation is invalid")
            try:
                timestamp = datetime.fromisoformat(str(event.get("timestamp")))
            except ValueError as exc:
                raise ValueError("Product Owner transaction timestamp is malformed") from exc
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Product Owner transaction timestamp must be timezone-aware")
            digest = event.get("event_digest")
            previous_digest = event.get("previous_event_digest")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("Product Owner transaction digest is malformed")
            if previous_digest is not None and (
                not isinstance(previous_digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", previous_digest) is None
            ):
                raise ValueError("Product Owner transaction predecessor is malformed")
            unsigned = dict(event)
            unsigned.pop("event_digest")
            if canonical_digest(unsigned) != digest:
                raise ValueError("Product Owner transaction digest mismatch")
            if events:
                prior = events[-1]
                if (
                    previous_digest != prior["event_digest"]
                    or event["approval_context_id"] != prior["approval_context_id"]
                    or event["binding_digest"] != prior["binding_digest"]
                    or event["operation"] != prior["operation"]
                ):
                    raise ValueError("Product Owner transaction lineage mismatch")
            elif previous_digest is not None:
                raise ValueError("first Product Owner transaction has a predecessor")
            events.append(event)
        states = tuple(event.get("state") for event in events)
        allowed = ((), ("INTENT",), ("INTENT", "COMMITTED"), ("INTENT", "COMMITTED", "PUBLISHED"))
        if states not in allowed:
            raise ValueError("Product Owner transaction sequence is invalid")
        for event in events:
            commit = event["projection_commit"]
            if event["state"] == "INTENT" and commit is not None:
                raise ValueError("Product Owner INTENT cannot claim a projection commit")
            if event["state"] != "INTENT" and (
                not isinstance(commit, str)
                or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is None
            ):
                raise ValueError("Product Owner transaction projection commit is invalid")
        if len(events) == 3 and events[1]["projection_commit"] != events[2]["projection_commit"]:
            raise ValueError("Product Owner transaction projection commit changed")
        return tuple(events)

    @staticmethod
    def _read_exact(path: Path, envelope_name: str) -> dict[str, object]:
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError(f"{envelope_name} path cannot traverse a symbolic link")
        envelope = _strict_json_loads(path.read_text(encoding="utf-8"))
        if not isinstance(envelope, dict) or set(envelope) != {envelope_name}:
            raise ValueError(f"{envelope_name} envelope is malformed")
        value = envelope[envelope_name]
        if not isinstance(value, dict):
            raise ValueError(f"{envelope_name} payload is malformed")
        return value

    def persist_rework_contract(
        self, contract_id: str, contract: ReworkContract,
        authorizing_review_result_id: str | None = None,
    ) -> Path:
        path = self.root / "rework-contracts" / contract.task_id / f"{contract.review_iteration}-{contract_id}.json"
        payload: dict[str, object] = {"contract_id": contract_id, "rework_contract": contract}
        if authorizing_review_result_id is not None:
            if contract.canonical_id(authorizing_review_result_id) != contract_id:
                raise ValueError("ReworkContract identity does not match canonical authority")
            payload["authorizing_review_result_id"] = authorizing_review_result_id
        return self._persist_immutable(path, _json(payload), contract_id)

    def rework_contract_id(self, task_id: str, iteration: int, *, expected_head: str) -> str:
        root = self.root / "rework-contracts" / task_id
        candidates = tuple(sorted(root.glob(f"{iteration}-*.json"))) if root.exists() else ()
        if len(candidates) != 1:
            raise ValueError("preceding ReworkContract identity is missing or ambiguous")
        value = json.loads(candidates[0].read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {
            "contract_id", "authorizing_review_result_id", "rework_contract",
        }:
            raise ValueError("persisted ReworkContract envelope is malformed")
        contract_id = value.get("contract_id")
        authorizing = value.get("authorizing_review_result_id")
        payload = value.get("rework_contract")
        if not isinstance(contract_id, str) or not isinstance(authorizing, str) or not isinstance(payload, dict):
            raise ValueError("persisted ReworkContract authority is malformed")
        required = {
            "task_id", "review_iteration", "expected_head", "allowed_rework_scope",
            "findings", "required_validations", "created_at",
        }
        if set(payload) != required:
            raise ValueError("persisted ReworkContract payload is malformed")
        try:
            contract = ReworkContract(
                str(payload["task_id"]), int(payload["review_iteration"]), str(payload["expected_head"]),
                _string_tuple(payload["allowed_rework_scope"]), _string_tuple(payload["findings"]),
                _string_tuple(payload["required_validations"]), datetime.fromisoformat(str(payload["created_at"])),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("persisted ReworkContract payload is invalid") from exc
        if contract.task_id != task_id or contract.review_iteration != iteration or contract.expected_head != expected_head:
            raise ValueError("persisted ReworkContract lineage binding mismatch")
        if contract.canonical_id(authorizing) != contract_id:
            raise ValueError("persisted ReworkContract content identity mismatch")
        if candidates[0].name != f"{iteration}-{contract_id}.json":
            raise ValueError("persisted ReworkContract filename identity mismatch")
        result = self._authorizing_fail_result(authorizing)
        expected_findings = tuple(
            f"{finding.fingerprint}:{finding.rule_id}:{finding.action_id}"
            for finding in result.findings
        )
        if (
            contract.task_id != result.task_id
            or contract.review_iteration != result.review_iteration + 1
            or contract.findings != expected_findings
            or contract.allowed_rework_scope != result.allowed_rework_scope
            or contract.required_validations != result.required_validations
            or contract.created_at != result.created_at
        ):
            raise ValueError("persisted ReworkContract does not match authorizing FAIL result")
        self._validate_published_fail_projection(result, contract)
        return contract_id

    def _authorizing_fail_result(self, result_id: str) -> ArchitectReviewResult:
        from .architect_review import parse_architect_review_result

        path = self.root / "architect-review-results" / f"{result_id}.json"
        if not path.is_file():
            raise ValueError("authorizing ArchitectReviewResult is missing")
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(envelope, dict) or set(envelope) != {"architect_review_result"}:
                raise ValueError("result envelope fields do not match authority")
            payload = envelope["architect_review_result"]
            if not isinstance(payload, dict):
                raise ValueError("result payload is not an object")
            result = parse_architect_review_result(json.dumps(payload))
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("authorizing ArchitectReviewResult is malformed") from exc
        values = asdict(result)
        values.pop("review_result_id")
        canonical_id = canonical_digest({"schema": "architect-review-result-v1", **values})
        if result.review_result_id != result_id or canonical_id != result_id:
            raise ValueError("authorizing ArchitectReviewResult identity mismatch")
        if result.disposition is not ArchitectReviewDisposition.FAIL:
            raise ValueError("only ArchitectReviewResult.FAIL may authorize rework")
        return result

    def _validate_published_fail_projection(
        self, result: ArchitectReviewResult, contract: ReworkContract,
    ) -> None:
        path = self.root / "lifecycle-projections" / f"{result.review_result_id}.jsonl"
        if not path.is_file():
            raise ValueError("authorizing FAIL projection evidence is missing")
        published: list[dict[str, object]] = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                wrapper = json.loads(line)
                if not isinstance(wrapper, dict) or set(wrapper) != {"projection_event"}:
                    raise ValueError("projection event envelope is malformed")
                event = wrapper["projection_event"]
                if not isinstance(event, dict):
                    raise ValueError("projection event is not an object")
                if event.get("state") == "PUBLISHED":
                    published.append(event)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("authorizing FAIL projection evidence is malformed") from exc
        if len(published) != 1:
            raise ValueError("authorizing FAIL projection is missing or ambiguous")
        event = published[0]
        required = {
            "task_id", "review_result_id", "branch", "expected_parent",
            "projection_commit", "disposition", "state", "timestamp",
        }
        if set(event) != required:
            raise ValueError("published FAIL projection fields do not match authority")
        try:
            timestamp = datetime.fromisoformat(str(event["timestamp"]))
        except ValueError as exc:
            raise ValueError("published FAIL projection timestamp is malformed") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("published FAIL projection timestamp must be timezone-aware")
        if (
            event["task_id"] != result.task_id
            or event["review_result_id"] != result.review_result_id
            or event["disposition"] != ArchitectReviewDisposition.FAIL.value
            or event["state"] != "PUBLISHED"
            or event["expected_parent"] != result.expected_head
            or event["projection_commit"] != contract.expected_head
            or not isinstance(event["branch"], str)
            or not event["branch"].strip()
        ):
            raise ValueError("published FAIL projection does not match rework authority")

    def append_lifecycle(self, payload: dict[str, object]) -> Path:
        path = self.root / "lifecycle-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(_json({"lifecycle_event": payload}) + "\n")
        return path

    def append_projection_event(self, result_id: str, payload: dict[str, object]) -> Path:
        path = self.root / "lifecycle-projections" / f"{result_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(_json({"projection_event": payload}) + "\n")
        return path

    def pending_projection(self, task_id: str) -> dict[str, object] | None:
        root = self.root / "lifecycle-projections"
        candidates: list[dict[str, object]] = []
        if root.exists():
            for path in sorted(root.glob("*.jsonl")):
                events = [json.loads(line).get("projection_event") for line in path.read_text(encoding="utf-8").splitlines()]
                if not events or any(not isinstance(event, dict) for event in events):
                    raise ValueError("malformed lifecycle projection ledger")
                latest = events[-1]
                if latest.get("task_id") == task_id and latest.get("state") != "PUBLISHED":
                    candidates.append(latest)
        if len(candidates) > 1:
            raise ValueError("multiple pending lifecycle projections")
        return candidates[0] if candidates else None

    @staticmethod
    def _persist_immutable(path: Path, serialized: str, identity: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = serialized.rstrip("\n") + "\n"
        try:
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            if path.read_text(encoding="utf-8") != encoded:
                raise RuntimeError(f"immutable identity collision: {identity}") from None
        if path.read_bytes() != encoded.encode("utf-8"):
            raise RuntimeError(f"immutable persistence verification failed: {identity}")
        _sync_parent(path.parent)
        return path


def _json(value: object) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True, separators=(",", ":"))


def _strict_json_loads(payload: str) -> object:
    def reject_duplicate_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for name, item in pairs:
            if name in value:
                raise ValueError(f"duplicate JSON field: {name}")
            value[name] = item
        return value

    return json.loads(payload, object_pairs_hook=reject_duplicate_fields)


def _json_default(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, (datetime, Enum)):
        return value.isoformat() if isinstance(value, datetime) else value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("ReworkContract sequence must contain strings")
    return tuple(value)


def _string(value: dict[str, object], name: str) -> str:
    item = value.get(name)
    if not isinstance(item, str):
        raise ValueError(f"{name} must be a string")
    return item


def _invalid_boolean() -> bool:
    raise ValueError("passed must be a boolean")


def _mapping(value: dict[str, object], name: str) -> dict[str, object]:
    item = value.get(name)
    if not isinstance(item, dict):
        raise ValueError(f"{name} must be an object")
    return item


def _identity(value: str, name: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 identity")


def _sync_parent(directory: Path) -> None:
    """Sync directory metadata where the platform exposes directory handles."""
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
