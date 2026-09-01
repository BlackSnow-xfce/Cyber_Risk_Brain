"""Machine-readable local persistence for runner results and audit events."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from .contracts import (
    ArchitectReviewDisposition, ArchitectReviewRequest, ArchitectReviewResult, AuditEvent,
    CodexExecutionResult, ReworkContract, canonical_digest, utc_now,
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

    def append_audit(self, event: AuditEvent) -> Path:
        path = self.root / "audit.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(_json(event) + "\n")
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
        except FileExistsError:
            if path.read_text(encoding="utf-8") != encoded:
                raise RuntimeError(f"immutable identity collision: {identity}") from None
        if path.read_bytes() != encoded.encode("utf-8"):
            raise RuntimeError(f"immutable persistence verification failed: {identity}")
        return path


def _json(value: object) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True, separators=(",", ":"))


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
