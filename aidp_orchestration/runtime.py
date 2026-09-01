"""Machine-readable local persistence for runner results and audit events."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from .contracts import (
    ArchitectReviewRequest, ArchitectReviewResult, AuditEvent, CodexExecutionResult,
    ReworkContract, canonical_digest, utc_now,
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

    def persist_rework_contract(self, contract_id: str, contract: ReworkContract) -> Path:
        path = self.root / "rework-contracts" / contract.task_id / f"{contract.review_iteration}-{contract_id}.json"
        return self._persist_immutable(path, _json({"contract_id": contract_id, "rework_contract": contract}), contract_id)

    def append_lifecycle(self, payload: dict[str, object]) -> Path:
        path = self.root / "lifecycle-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(_json({"lifecycle_event": payload}) + "\n")
        return path

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
