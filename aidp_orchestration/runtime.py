"""Machine-readable local persistence for runner results and audit events."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from .contracts import AuditEvent, CodexExecutionResult, utc_now


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
