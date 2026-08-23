"""Read-only Git transport from an explicit Architect branch to the local inbox."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from .contracts import (
    ArchitectIngressResult, ArchitectTaskContract, IngressStatus, ReworkContract,
    utc_now,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .trigger_publisher import LocalContractInbox
from .validators import ValidatorRegistry


CONTRACT_PATH = ".ai/orchestration/architect-contracts"
LOCAL_FETCH_REF = "refs/aidp-orchestration/architect-contracts"


class ArchitectGitIngress:
    def __init__(self, repository: AIDPRepository, *, branch: str,
                 runtime_root: Path | None = None, validator_registry: ValidatorRegistry | None = None):
        if not _valid_branch(branch):
            raise ValueError("Architect contract branch must be explicit and valid")
        self.repository = repository
        self.branch = branch
        self.runtime_root = runtime_root or LocalRuntimeStore.for_repository(repository.root).root
        self.inbox = LocalContractInbox(self.runtime_root)
        self.validator_registry = validator_registry or ValidatorRegistry()
        self.state_path = self.runtime_root / "architect-ingress.jsonl"

    def run_once(self) -> ArchitectIngressResult:
        try:
            self._fetch()
            commit = self._git("rev-parse", LOCAL_FETCH_REF)
            candidates = self._discover(commit)
            parsed = [(path, blob, LocalContractInbox.parse(content)) for path, blob, content in candidates]
            ids = [item.contract_id for _, _, item in parsed]
            if len(ids) != len(set(ids)):
                return self._blocked(None, commit, None, "duplicate contract_id in remote branch")
            history = self._history()
            new: list[tuple[str, str, object]] = []
            for path, blob, item in parsed:
                previous = history.get(item.contract_id)
                if previous is not None:
                    if previous != blob:
                        return self._blocked(item.contract_id, commit, blob, "contract_id content mutated")
                    continue
                self._validate(item.contract)
                new.append((path, blob, item))
            if not new:
                return ArchitectIngressResult(IngressStatus.NO_ACTION, None, commit, None)
            _, blob, item = sorted(new, key=lambda value: value[0])[0]
            path = self.inbox.persist(item)
            self._append(item.contract_id, commit, blob, IngressStatus.MATERIALIZED, "remote contract materialized")
            return ArchitectIngressResult(IngressStatus.MATERIALIZED, item.contract_id, commit, blob, str(path))
        except (OSError, RuntimeError, ValueError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
            return ArchitectIngressResult(IngressStatus.BLOCKED, None, None, None, failure_reason=f"Architect ingress failed: {exc.__class__.__name__}")

    def _fetch(self) -> None:
        try:
            self._git("remote", "get-url", "origin")
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("origin remote is missing") from exc
        self._git("fetch", "--no-tags", "origin", f"refs/heads/{self.branch}:{LOCAL_FETCH_REF}")

    def _discover(self, commit: str) -> tuple[tuple[str, str, bytes], ...]:
        output = subprocess.check_output(
            ("git", "ls-tree", "-r", "--name-only", "-z", commit, "--", CONTRACT_PATH),
            cwd=self.repository.root,
        )
        if output and not output.endswith(b"\0"):
            raise RuntimeError("malformed Git path output")
        paths = output[:-1].decode("utf-8", errors="strict").split("\0") if output else []
        prefix = f"{CONTRACT_PATH}/"
        for path in paths:
            relative = path.removeprefix(prefix)
            if not path.startswith(prefix) or "/" in relative or not relative.endswith(".json"):
                raise ValueError("contract exists outside the exact ingress path")
        values = []
        for path in sorted(paths):
            blob = self._git("rev-parse", f"{commit}:{path}")
            content = subprocess.check_output(("git", "show", f"{commit}:{path}"), cwd=self.repository.root)
            values.append((path, blob, content))
        return tuple(values)

    def _validate(self, contract: ArchitectTaskContract | ReworkContract) -> None:
        requirements = contract.validation_requirements if isinstance(contract, ArchitectTaskContract) else contract.required_validations
        unknown = self.validator_registry.unknown(requirements)
        if unknown:
            raise ValueError(f"unknown validator: {unknown[0]}")

    def _history(self) -> dict[str, str]:
        history: dict[str, str] = {}
        if not self.state_path.exists():
            return history
        for line in self.state_path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line).get("architect_ingress_event")
            if not isinstance(value, dict) or not isinstance(value.get("contract_id"), str) or not isinstance(value.get("blob_id"), str):
                raise ValueError("malformed Architect ingress state")
            contract_id, blob = value["contract_id"], value["blob_id"]
            if contract_id in history and history[contract_id] != blob:
                raise ValueError("inconsistent Architect ingress state")
            history[contract_id] = blob
        return history

    def _blocked(self, contract_id: str | None, commit: str, blob: str | None, reason: str) -> ArchitectIngressResult:
        if contract_id is not None and blob is not None:
            self._append(contract_id, commit, blob, IngressStatus.BLOCKED, reason)
        return ArchitectIngressResult(IngressStatus.BLOCKED, contract_id, commit, blob, failure_reason=reason)

    def _append(self, contract_id: str, commit: str, blob: str, status: IngressStatus, reason: str) -> None:
        event = {"architect_ingress_event": {
            "contract_id": contract_id, "remote_commit": commit, "blob_id": blob,
            "status": status, "timestamp": utc_now(), "reason": reason,
        }}
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, default=_json_default, sort_keys=True, separators=(",", ":")) + "\n")

    def _git(self, *args: str) -> str:
        return subprocess.check_output(("git", *args), cwd=self.repository.root, text=True, stderr=subprocess.STDOUT).strip()


def serialize_architect_ingress_result(result: ArchitectIngressResult) -> str:
    return json.dumps({"architect_ingress_result": asdict(result)}, default=_json_default, sort_keys=True, separators=(",", ":"))


def _valid_branch(branch: str) -> bool:
    return (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", branch) is not None
        and ".." not in branch and "//" not in branch and not branch.endswith(("/", "."))
    )


def _json_default(value: object) -> object:
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, Enum): return value.value
    raise TypeError(type(value).__name__)
