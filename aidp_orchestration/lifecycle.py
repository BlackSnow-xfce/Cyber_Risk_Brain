"""Single-iteration supervisor for Codex and autonomous Architect work."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Protocol

from .architect_review import (
    ArchitectReviewCoordinator, architect_result_schema, create_review_request,
    parse_architect_review_request, parse_architect_review_result, validate_review_result,
)
from .contracts import (
    AIDPState, ArchitectReviewDisposition, ArchitectReviewRequest, ArchitectReviewResult, AuditEvent,
    ArchitectTaskContract, ContractInboxItem, ExecutionStatus, LifecycleResult, LifecycleStatus,
    ProductOwnerAcceptanceStatus, ReworkContract, ScopeCompliance,
    TriggerStatus, ValidationResult, canonical_digest, utc_now,
)
from .lifecycle_projection import LifecycleProjection
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .trigger_publisher import AIDPWatchOnce, LocalContractInbox


MAX_AUTONOMOUS_REWORKS = 3


class CodexBoundary(Protocol):
    def run_once(self): ...


class ArchitectBoundary(Protocol):
    def review(self, request: ArchitectReviewRequest, *, schema_path: Path) -> ArchitectReviewResult: ...
    def revalidate(self, request: ArchitectReviewRequest) -> None: ...


class ProductOwnerAcceptanceBoundary(Protocol):
    def consume(self): ...


class AIDPLifecycleOnce:
    def __init__(
        self,
        repository: AIDPRepository,
        *,
        codex: CodexBoundary | None = None,
        architect: ArchitectBoundary | None = None,
        runtime_store: LocalRuntimeStore | None = None,
        projection: LifecycleProjection | None = None,
        request_factory=None,
        product_owner_acceptance: ProductOwnerAcceptanceBoundary | None = None,
        authority_inbox_root: Path | None = None,
        clock=utc_now,
    ) -> None:
        self.repository = repository
        self.codex = codex or AIDPWatchOnce(repository)
        self.architect = architect
        self.runtime = runtime_store or LocalRuntimeStore.for_repository(repository.root)
        self.projection = projection or LifecycleProjection(repository.root)
        self.request_factory = request_factory or self._build_request
        self.product_owner_acceptance = product_owner_acceptance
        self.authority_inbox_root = authority_inbox_root or self.runtime.root
        self.clock = clock

    def run_once(self) -> LifecycleResult:
        try:
            decision = self.repository.inspect()
        except Exception as exc:
            return self._blocked(None, AIDPState.BLOCKED, f"lifecycle inspection failed: {exc.__class__.__name__}")
        if decision.task_id is not None:
            try:
                recovered = self._recover_projection(decision.task_id, decision.state)
            except Exception as exc:
                return LifecycleResult(
                    LifecycleStatus.ESCALATION_REQUIRED, decision.task_id, decision.state,
                    f"lifecycle projection recovery failed closed: {exc.__class__.__name__}: {exc}",
                )
            if recovered is not None:
                return recovered
        if decision.state is AIDPState.WAITING_FOR_PRODUCT_OWNER:
            if self.product_owner_acceptance is not None:
                try:
                    acceptance = self.product_owner_acceptance.consume()
                except Exception as exc:
                    return self._blocked(
                        decision.task_id, decision.state,
                        f"Product Owner acceptance boundary failed closed: {exc.__class__.__name__}",
                    )
                if acceptance is not None:
                    if acceptance.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED:
                        return LifecycleResult(
                            LifecycleStatus.ADVANCED, acceptance.task_id,
                            acceptance.lifecycle_state,
                            f"Product Owner {acceptance.operation.value} consumed",
                        )
                    if acceptance.status not in {
                        ProductOwnerAcceptanceStatus.CONFIRMATION_REQUIRED,
                        ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION,
                    }:
                        return self._blocked(
                            decision.task_id, decision.state,
                            f"Product Owner acceptance failed closed: {acceptance.reason_code}",
                        )
            return LifecycleResult(LifecycleStatus.NO_ACTION, decision.task_id, decision.state, "Product Owner hard gate")
        if decision.state is AIDPState.PRODUCT_OWNER_REWORK_REQUESTED:
            return LifecycleResult(
                LifecycleStatus.NO_ACTION, decision.task_id, decision.state,
                "Product Owner rework requires Architect planning authority",
            )
        if decision.state in {AIDPState.WAITING, AIDPState.READY_FOR_CODEX, AIDPState.REWORK_REQUIRED}:
            if decision.state is AIDPState.REWORK_REQUIRED and decision.task_id is not None:
                try:
                    self._ensure_rework_authority(decision.task_id)
                except Exception as exc:
                    return self._blocked(decision.task_id, decision.state, f"rework recovery failed closed: {exc.__class__.__name__}")
            result = self.codex.run_once()
            if result.status is TriggerStatus.PUBLISHED:
                execution = result.control_plane_result.runner_result.execution_result
                return LifecycleResult(
                    LifecycleStatus.ADVANCED, execution.task_id, AIDPState.READY_FOR_ARCHITECT,
                    "Codex execution and review projection published", execution.execution_id,
                )
            if result.status is TriggerStatus.NO_ACTION:
                reason = "no pending Architect contract" if decision.state is AIDPState.WAITING else "no eligible Codex contract"
                return LifecycleResult(LifecycleStatus.NO_ACTION, decision.task_id, decision.state, reason)
            reason = result.failure_reason or "Codex lifecycle failed closed"
            status = LifecycleStatus.ESCALATION_REQUIRED if "abandoned" in reason or "execution" in reason else LifecycleStatus.BLOCKED
            return LifecycleResult(status, decision.task_id, decision.state, reason)
        if decision.state is AIDPState.READY_FOR_ARCHITECT:
            return self._review(decision.task_id)
        return self._blocked(decision.task_id, decision.state, "; ".join(decision.reasons) or "unsafe lifecycle state")

    def _review(self, task_id: str | None) -> LifecycleResult:
        if task_id is None or self.architect is None:
            return self._blocked(task_id, AIDPState.READY_FOR_ARCHITECT, "Architect review boundary is unavailable")
        try:
            request = self.request_factory(task_id)
            self.runtime.persist_architect_request(request)
            previous = tuple(
                value for value in self._previous_results(task_id)
                if value.review_iteration < request.review_iteration
            )
            persisted = self._persisted_result(request.review_request_id)
            if persisted is None and self.runtime.architect_attempt_exists(request.review_request_id):
                return LifecycleResult(
                    LifecycleStatus.ESCALATION_REQUIRED, task_id, AIDPState.READY_FOR_ARCHITECT,
                    "Architect attempt has no persisted result; duplicate launch is forbidden",
                    request.execution_id, request.review_request_id,
                )
            self.runtime.persist_architect_attempt(request.review_request_id, {
                "review_request_id": request.review_request_id,
                "execution_id": request.execution_id,
                "state": "LAUNCH_AUTHORIZED",
                "created_at": request.created_at,
            })
            result = persisted or self.architect.review(request, schema_path=self._schema_path())
            validate_review_result(request, result)
            self._validate_sequence(request, result, previous)
            self.runtime.persist_architect_result(result)
            intended = (
                AIDPState.ARCHITECT_APPROVED if result.disposition is ArchitectReviewDisposition.PASS
                else AIDPState.REWORK_REQUIRED if result.disposition is ArchitectReviewDisposition.FAIL
                else None
            )
            self.runtime.append_audit(AuditEvent(
                self.clock(), task_id, AIDPState.READY_FOR_ARCHITECT, AIDPState.READY_FOR_ARCHITECT,
                intended, "autonomous-architect-review", request.branch, request.expected_current_head,
                request.execution_id, f"Architect review {result.disposition.value}",
            ))
            self.runtime.append_lifecycle({
                "task_id": task_id, "previous_state": AIDPState.READY_FOR_ARCHITECT,
                "review_request_id": request.review_request_id, "review_result_id": result.review_result_id,
                "disposition": result.disposition, "timestamp": self.clock(),
            })
        except Exception as exc:
            return self._blocked(
                task_id, AIDPState.READY_FOR_ARCHITECT,
                f"Architect review failed closed: {exc.__class__.__name__}: {exc}",
            )
        if result.disposition is ArchitectReviewDisposition.BLOCKED:
            revalidation = self._revalidate_before_mutation(request)
            if revalidation is not None:
                return revalidation
            self.projection.publish_result_only(result)
            self.projection.push(request.branch)
            return LifecycleResult(
                LifecycleStatus.BLOCKED, task_id, AIDPState.READY_FOR_ARCHITECT,
                result.failure_reason or "Architect review blocked", request.execution_id,
                request.review_request_id, result.review_result_id,
            )
        escalation = self._loop_guard(request, result, previous)
        if escalation is not None:
            revalidation = self._revalidate_before_mutation(request)
            if revalidation is not None:
                return revalidation
            self.projection.publish_result_only(result)
            self.projection.push(request.branch)
            return LifecycleResult(
                LifecycleStatus.ESCALATION_REQUIRED, task_id, AIDPState.READY_FOR_ARCHITECT,
                escalation, request.execution_id, request.review_request_id, result.review_result_id,
            )
        revalidation = self._revalidate_before_mutation(request)
        if revalidation is not None:
            return revalidation
        self.runtime.append_projection_event(result.review_result_id, {
            "task_id": task_id, "review_result_id": result.review_result_id,
            "branch": request.branch, "expected_parent": result.expected_head,
            "disposition": result.disposition, "state": "INTENT", "timestamp": self.clock(),
        })
        projected_head = self.projection.project_architect_result(result)
        self.runtime.append_projection_event(result.review_result_id, {
            "task_id": task_id, "review_result_id": result.review_result_id,
            "branch": request.branch, "expected_parent": result.expected_head,
            "projection_commit": projected_head, "disposition": result.disposition,
            "state": "COMMITTED", "timestamp": self.clock(),
        })
        self.projection.push(request.branch)
        self.runtime.append_projection_event(result.review_result_id, {
            "task_id": task_id, "review_result_id": result.review_result_id,
            "branch": request.branch, "expected_parent": result.expected_head,
            "projection_commit": projected_head, "disposition": result.disposition,
            "state": "PUBLISHED", "timestamp": self.clock(),
        })
        if result.disposition is ArchitectReviewDisposition.PASS:
            state = self.repository.inspect().state
            if state is not AIDPState.WAITING_FOR_PRODUCT_OWNER:
                return self._blocked(task_id, state, "PASS projection did not reach Product Owner gate")
            return LifecycleResult(
                LifecycleStatus.ADVANCED, task_id, state, "Architect approved; Product Owner hard gate reached",
                request.execution_id, request.review_request_id, result.review_result_id,
            )
        self._persist_rework_authority(result, projected_head)
        return LifecycleResult(
            LifecycleStatus.ADVANCED, task_id, AIDPState.REWORK_REQUIRED,
            f"Architect requires authorized rework {result.review_iteration + 1}", request.execution_id,
            request.review_request_id, result.review_result_id,
        )

    def _recover_projection(self, task_id: str, state: AIDPState) -> LifecycleResult | None:
        pending = self.runtime.pending_projection(task_id)
        if pending is None:
            return None
        result_id = str(pending.get("review_result_id", ""))
        result = self._result_by_id(result_id)
        expected_parent = str(pending.get("expected_parent", ""))
        if result.expected_head != expected_parent:
            raise ValueError("pending projection result binding mismatch")
        head = self.repository.head
        if head == expected_parent:
            if state is not AIDPState.READY_FOR_ARCHITECT:
                raise ValueError("projection intent exists in an incompatible lifecycle state")
            return None
        commit = str(pending.get("projection_commit") or head)
        self.projection.verify_result_projection_commit(result, commit)
        branch = str(pending.get("branch", ""))
        self.projection.push(branch)
        self.runtime.append_projection_event(result.review_result_id, {
            "task_id": task_id, "review_result_id": result.review_result_id,
            "branch": branch, "expected_parent": expected_parent,
            "projection_commit": commit, "disposition": result.disposition,
            "state": "PUBLISHED", "timestamp": self.clock(),
        })
        target = (
            AIDPState.WAITING_FOR_PRODUCT_OWNER
            if result.disposition is ArchitectReviewDisposition.PASS else AIDPState.REWORK_REQUIRED
        )
        return LifecycleResult(
            LifecycleStatus.ADVANCED, task_id, target,
            "existing lifecycle projection commit published during recovery",
            result.execution_id, result.review_request_id, result.review_result_id,
        )

    def _revalidate_before_mutation(self, request: ArchitectReviewRequest) -> LifecycleResult | None:
        try:
            if self.architect is None:
                raise ValueError("Architect boundary is unavailable")
            self.architect.revalidate(request)
        except Exception as exc:
            return LifecycleResult(
                LifecycleStatus.ESCALATION_REQUIRED, request.task_id, AIDPState.READY_FOR_ARCHITECT,
                f"Product identity changed before lifecycle mutation: {exc.__class__.__name__}: {exc}",
                request.execution_id, request.review_request_id,
            )
        return None

    def _result_by_id(self, result_id: str) -> ArchitectReviewResult:
        path = self.runtime.root / "architect-review-results" / f"{result_id}.json"
        if not path.is_file():
            raise ValueError("pending projection has no persisted Architect result")
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        value = wrapper.get("architect_review_result") if isinstance(wrapper, dict) else None
        if not isinstance(value, dict):
            raise ValueError("pending projection Architect result is malformed")
        return parse_architect_review_result(json.dumps(value))

    def _ensure_rework_authority(self, task_id: str) -> None:
        previous = self._previous_results(task_id)
        if not previous:
            return
        result = previous[-1]
        if result.disposition is not ArchitectReviewDisposition.FAIL:
            raise ValueError("REWORK_REQUIRED has no persisted FAIL authority")
        self._persist_rework_authority(result, self.repository.head)

    def _persist_rework_authority(self, result: ArchitectReviewResult, expected_head: str) -> None:
        rework_iteration = result.review_iteration + 1
        contract = ReworkContract(
            result.task_id, rework_iteration, expected_head, result.allowed_rework_scope,
            tuple(f"{finding.fingerprint}:{finding.rule_id}:{finding.action_id}" for finding in result.findings),
            result.required_validations, result.created_at,
        )
        contract_id = contract.canonical_id(result.review_result_id)
        self.runtime.persist_rework_contract(contract_id, contract, result.review_result_id)
        LocalContractInbox(self.authority_inbox_root).persist(
            ContractInboxItem(contract_id, contract, result.created_at),
        )

    def _build_request(self, task_id: str) -> ArchitectReviewRequest:
        envelopes = []
        for path in (self.repository.ai_root / "orchestration" / "review-inbox").glob(f"{task_id}-*.json"):
            payload = json.loads(path.read_text(encoding="utf-8")).get("architect_review_envelope")
            if isinstance(payload, dict):
                envelopes.append((datetime.fromisoformat(str(payload["published_at"])), path, payload))
        if not envelopes:
            raise ValueError("review envelope is missing")
        _, envelope_path, envelope = sorted(envelopes, key=lambda value: value[0])[-1]
        contracts = [
            item for item in LocalContractInbox(self.authority_inbox_root).pending()
            if isinstance(item.contract, ArchitectTaskContract) and item.contract.task_id == task_id
        ]
        if len(contracts) != 1:
            raise ValueError("original immutable task authority is unavailable or ambiguous")
        authority_item = contracts[0]
        authority = authority_item.contract
        previous = self._previous_results(task_id)
        if previous and str(envelope["execution_id"]) == previous[-1].execution_id:
            return self._persisted_request(previous[-1].review_request_id)
        if previous and previous[-1].disposition is ArchitectReviewDisposition.BLOCKED:
            raise ValueError("blocked Architect review requires escalation")
        iteration = len(previous)
        if iteration > MAX_AUTONOMOUS_REWORKS:
            raise ValueError("Architect review iteration exceeds policy")
        head = self.repository.head
        reviewed_head = str(envelope["resulting_commit"])
        tree = self.repository._git("rev-parse", f"{reviewed_head}^{{tree}}")
        common = self.repository._git("rev-parse", "--git-common-dir")
        common_path = Path(common)
        common_path = (self.repository.root / common_path).resolve() if not common_path.is_absolute() else common_path.resolve()
        remote = self.repository._git("remote", "get-url", "origin")
        validations = tuple(ValidationResult(str(item["name"]), bool(item["passed"]), str(item.get("detail", ""))) for item in envelope["validation_results"])
        relative_envelope = envelope_path.relative_to(self.repository.root).as_posix()
        values = dict(
            task_id=task_id, review_iteration=iteration, execution_id=str(envelope["execution_id"]),
            repository=str(self.repository.root), git_common_dir=str(common_path), branch=str(envelope["branch"]),
            remote_url=remote, authority_contract_id=authority_item.contract_id,
            authority_contract_digest=canonical_digest(authority), original_allowed_scope=authority.allowed_scope,
            original_prohibited_actions=authority.prohibited_actions,
            original_validation_requirements=authority.validation_requirements,
            original_acceptance_criteria=authority.acceptance_criteria, product_owner_gate=authority.product_owner_gate,
            review_envelope_path=relative_envelope, review_envelope_digest=canonical_digest(envelope_path.read_bytes()),
            execution_status=ExecutionStatus(str(envelope["execution_status"])), start_commit=str(envelope["start_commit"]),
            resulting_commit=reviewed_head, review_envelope_commit=head,
            changed_files=tuple(sorted(str(value) for value in envelope["changed_files"])),
            validation_results=validations, scope_compliance=ScopeCompliance(str(envelope["scope_compliance"])),
            expected_current_head=head, current_head=head, reviewed_head=reviewed_head, reviewed_tree_hash=tree,
            previous_review_result_id=previous[-1].review_result_id if previous else None,
            previous_rework_contract_id=(
                self.runtime.rework_contract_id(
                    task_id, iteration, expected_head=str(envelope["start_commit"]),
                ) if iteration > 0 else None
            ),
            previous_finding_fingerprints=tuple(finding.fingerprint for finding in previous[-1].findings) if previous else (),
            created_at=datetime.fromisoformat(str(envelope["published_at"])),
        )
        return create_review_request(**values)

    def _persisted_request(self, request_id: str) -> ArchitectReviewRequest:
        path = self.runtime.root / "architect-review-requests" / f"{request_id}.json"
        if not path.is_file():
            raise ValueError("reviewed execution has no persisted Architect request")
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        payload = wrapper.get("architect_review_request") if isinstance(wrapper, dict) else None
        if not isinstance(payload, dict):
            raise ValueError("persisted Architect request is malformed")
        return parse_architect_review_request(json.dumps(payload))

    def _previous_results(self, task_id: str) -> tuple[ArchitectReviewResult, ...]:
        values = []
        root = self.runtime.root / "architect-review-results"
        if root.exists():
            for path in sorted(root.glob("*.json")):
                payload = json.loads(path.read_text(encoding="utf-8")).get("architect_review_result")
                if isinstance(payload, dict) and payload.get("task_id") == task_id:
                    values.append(parse_architect_review_result(json.dumps(payload)))
        return tuple(sorted(values, key=lambda value: value.review_iteration))

    def _persisted_result(self, request_id: str) -> ArchitectReviewResult | None:
        candidates = []
        root = self.runtime.root / "architect-review-results"
        if root.exists():
            for path in root.glob("*.json"):
                payload = json.loads(path.read_text(encoding="utf-8")).get("architect_review_result")
                if isinstance(payload, dict) and payload.get("review_request_id") == request_id:
                    candidates.append(parse_architect_review_result(json.dumps(payload)))
        if len(candidates) > 1:
            raise ValueError("duplicate Architect result for request")
        return candidates[0] if candidates else None

    @staticmethod
    def _validate_sequence(request: ArchitectReviewRequest, result: ArchitectReviewResult, previous: tuple[ArchitectReviewResult, ...]) -> None:
        if result.review_iteration != len(previous) or request.review_iteration != len(previous):
            raise ValueError("Architect review iteration replay or jump")
        execution_ids = {value.execution_id for value in previous}
        request_ids = {value.review_request_id for value in previous}
        result_ids = {value.review_result_id for value in previous}
        if request.execution_id in execution_ids or request.review_request_id in request_ids or result.review_result_id in result_ids:
            raise ValueError("duplicate execution or review identity")

    @staticmethod
    def _loop_guard(
        request: ArchitectReviewRequest,
        result: ArchitectReviewResult,
        previous: tuple[ArchitectReviewResult, ...],
    ) -> str | None:
        if result.disposition is not ArchitectReviewDisposition.FAIL:
            return None
        if result.review_iteration >= MAX_AUTONOMOUS_REWORKS:
            return "maximum three autonomous reworks reached; Rework 4 is forbidden"
        if previous:
            prior = previous[-1]
            if request.reviewed_tree_hash == prior.reviewed_tree_hash:
                return "no progress: reviewed tree is unchanged after rework"
            relevant = {path for finding in prior.findings for path in finding.evidence_paths}
            if relevant and not relevant.intersection(request.changed_files):
                return "no progress: finding-relevant authorized files did not change"
            current = {finding.fingerprint for finding in result.findings}
            prior_fingerprints = {finding.fingerprint for finding in prior.findings}
            if current and current == prior_fingerprints:
                return "consecutive identical canonical Architect findings"
        return None

    def _schema_path(self) -> Path:
        path = self.runtime.root / "schemas" / "architect-review-result-v1.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(architect_result_schema(), sort_keys=True, separators=(",", ":")) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != serialized:
            raise RuntimeError("Architect output schema content changed")
        if not path.exists():
            with path.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        return path

    @staticmethod
    def _blocked(task_id: str | None, state: AIDPState, reason: str) -> LifecycleResult:
        return LifecycleResult(LifecycleStatus.BLOCKED, task_id, state, reason)
