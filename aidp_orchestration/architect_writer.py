"""Fail-closed materialization of explicitly authorized Architect contracts."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from .contracts import (
    AIDPState,
    ArchitectTaskContract,
    ReworkContract,
    TaskMetadata,
    WriterAction,
    WriterDecision,
    WriterResult,
)
from .control_plane import scope_is_subset, serialize_rework_contract
from .executor import GitInspector
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .validators import ValidatorRegistry


class ArchitectContractWriter:
    """Materializes contracts without selecting tasks or granting approval."""

    def __init__(
        self,
        repository: AIDPRepository,
        *,
        validator_registry: ValidatorRegistry | None = None,
        is_worktree_clean: Callable[[], bool] | None = None,
        runtime_root: Path | None = None,
    ):
        self.repository = repository
        self.validator_registry = validator_registry or ValidatorRegistry()
        self.is_worktree_clean = is_worktree_clean or GitInspector(repository.root).is_clean
        self.runtime_root = runtime_root or LocalRuntimeStore.for_repository(repository.root).root

    def materialize_task(self, contract: ArchitectTaskContract) -> WriterResult:
        decision = self.decide_task(contract)
        if decision.action is WriterAction.BLOCKED:
            return WriterResult(decision, failure_reason=decision.reason)
        task_path = self.repository.ai_root / "tasks" / "ready" / f"{contract.task_id}.md"
        if task_path.is_file():
            return WriterResult(decision)
        codex_handoff = self.repository.ai_root / "handoff" / "TO-CODEX.md"
        architect_handoff = self.repository.ai_root / "handoff" / "TO-ARCHITECT.md"
        contents = {
            task_path: _task_document(contract),
            codex_handoff: _codex_handoff(contract),
            architect_handoff: _architect_handoff(contract),
        }
        try:
            self._materialize_files(contents)
        except (OSError, RuntimeError) as exc:
            reason = f"READY materialization failed: {exc.__class__.__name__}"
            blocked = WriterDecision(WriterAction.BLOCKED, contract.task_id, decision.branch, decision.commit, reason)
            return WriterResult(blocked, failure_reason=reason)
        paths = tuple(sorted(path.relative_to(self.repository.root).as_posix() for path in contents))
        return WriterResult(decision, paths)

    def decide_task(self, contract: ArchitectTaskContract) -> WriterDecision:
        branch, head = self.repository.branch, self.repository.head
        if head != contract.expected_head:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "contract expected_head is stale")
        cleanliness = self._cleanliness_reason()
        if cleanliness is not None:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, cleanliness)
        unknown = self.validator_registry.unknown(contract.validation_requirements)
        if unknown:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, f"unknown validator: {unknown[0]}")
        repository_decision = self.repository.inspect()
        ready = self.repository.task_paths("ready")
        review = self.repository.task_paths("review")
        active = (*ready, *review)
        if len(active) > 1:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "another active READY or REVIEW task exists")
        if active:
            existing = active[0]
            if existing.stem != contract.task_id:
                return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "another active READY or REVIEW task exists")
            if existing in review:
                return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "matching task is in REVIEW and is not executable as a READY task")
            if repository_decision.state is not AIDPState.READY_FOR_CODEX or repository_decision.task_id != contract.task_id:
                return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "matching READY task state is ambiguous or not executable")
            metadata = self.repository.parse_metadata(existing)
            if metadata is None or not _same_execution_authority(contract, metadata):
                return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "contract authority does not match existing READY task")
            return WriterDecision(WriterAction.MATERIALIZE_READY, contract.task_id, branch, head, "contract reauthorizes the matching READY task")
        if repository_decision.state is not AIDPState.WAITING:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "repository state is not eligible for READY materialization")
        if any(self.repository.ai_root.joinpath("tasks").glob(f"**/{contract.task_id}.md")):
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "task_id already exists")
        return WriterDecision(WriterAction.MATERIALIZE_READY, contract.task_id, branch, head, "contract is authorized for READY materialization")

    def materialize_rework(self, contract: ReworkContract) -> WriterResult:
        decision = self.decide_rework(contract)
        if decision.action is WriterAction.BLOCKED:
            return WriterResult(decision, failure_reason=decision.reason)
        path = self.runtime_root / "rework-contracts" / f"{contract.task_id}.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                stream.write(serialize_rework_contract(contract) + "\n")
            persisted = json.loads(path.read_text(encoding="utf-8"))
            if persisted.get("rework_contract", {}).get("task_id") != contract.task_id:
                raise RuntimeError("rework contract persistence validation failed")
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            reason = f"rework contract persistence failed: {exc.__class__.__name__}"
            blocked = WriterDecision(WriterAction.BLOCKED, contract.task_id, decision.branch, decision.commit, reason)
            return WriterResult(blocked, failure_reason=reason)
        return WriterResult(decision, rework_contract_path=str(path))

    def decide_rework(self, contract: ReworkContract) -> WriterDecision:
        branch, head = self.repository.branch, self.repository.head
        if head != contract.expected_head:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "rework expected_head is stale")
        cleanliness = self._cleanliness_reason()
        if cleanliness is not None:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, cleanliness)
        repository_decision = self.repository.inspect()
        if repository_decision.state is not AIDPState.REWORK_REQUIRED or repository_decision.task_id != contract.task_id:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "matching existing rework task is required")
        paths = tuple(path for path in self.repository.task_paths("review") if path.stem == contract.task_id)
        metadata = self.repository.parse_metadata(paths[0]) if len(paths) == 1 else None
        if metadata is None or metadata.task_id != contract.task_id:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "existing task metadata is invalid")
        if not scope_is_subset(contract.allowed_rework_scope, metadata.allowed_scope):
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "rework scope widens original authority")
        unknown = self.validator_registry.unknown(contract.required_validations)
        if unknown:
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, f"unknown validator: {unknown[0]}")
        if any(item not in metadata.validation_requirements for item in contract.required_validations):
            return WriterDecision(WriterAction.BLOCKED, contract.task_id, branch, head, "rework validators exceed task authority")
        return WriterDecision(WriterAction.MATERIALIZE_REWORK, contract.task_id, branch, head, "rework contract is authorized for persistence")

    def _cleanliness_reason(self) -> str | None:
        try:
            return None if self.is_worktree_clean() else "worktree is dirty"
        except (OSError, RuntimeError):
            return "worktree cleanliness could not be established"

    @staticmethod
    def _materialize_files(contents: dict[Path, str]) -> None:
        original = {path: path.read_bytes() if path.exists() else None for path in contents}
        try:
            for path, content in contents.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                _atomic_write(path, content.encode("utf-8"))
        except OSError:
            for path, previous in original.items():
                if previous is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write(path, previous)
            raise


def load_architect_task_contract(path: Path) -> ArchitectTaskContract:
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get("architect_task_contract") if isinstance(payload, dict) else None
    if not isinstance(value, dict):
        raise ValueError("invalid ArchitectTaskContract envelope")
    return ArchitectTaskContract(
        task_id=_string(value, "task_id"),
        title=_string(value, "title"),
        phase=_string(value, "phase"),
        expected_head=_string(value, "expected_head"),
        allowed_scope=_strings(value, "allowed_scope"),
        prohibited_actions=_strings(value, "prohibited_actions"),
        validation_requirements=_strings(value, "validation_requirements"),
        acceptance_criteria=_strings(value, "acceptance_criteria"),
        product_owner_gate=_boolean(value, "product_owner_gate"),
        created_at=datetime.fromisoformat(_string(value, "created_at")),
    )


def serialize_architect_task_contract(contract: ArchitectTaskContract) -> str:
    return json.dumps({"architect_task_contract": asdict(contract)}, default=_json_default, sort_keys=True)


def serialize_writer_decision(decision: WriterDecision) -> str:
    return json.dumps({"writer_decision": asdict(decision)}, default=_json_default, sort_keys=True)


def serialize_writer_result(result: WriterResult) -> str:
    return json.dumps({"writer_result": asdict(result)}, default=_json_default, sort_keys=True)


def blocked_writer_result(reason: str) -> WriterResult:
    decision = WriterDecision(WriterAction.BLOCKED, None, "UNKNOWN", "UNKNOWN", reason)
    return WriterResult(decision, failure_reason=reason)


def _task_document(contract: ArchitectTaskContract) -> str:
    criteria = "\n".join(f"- {item}" for item in contract.acceptance_criteria)
    return (
        "---\n"
        f"task_id: {contract.task_id}\n"
        f"phase: {contract.phase}\n"
        f"allowed_scope: {', '.join(contract.allowed_scope)}\n"
        f"prohibited_actions: {', '.join(contract.prohibited_actions)}\n"
        f"validation_requirements: {', '.join(contract.validation_requirements)}\n"
        f"product_owner_gate: {str(contract.product_owner_gate).lower()}\n"
        "---\n"
        f"# {contract.task_id} - {contract.title}\n\n"
        "Status: READY\n\n"
        "## Acceptance Criteria\n\n"
        f"{criteria}\n"
    )


def _codex_handoff(contract: ArchitectTaskContract) -> str:
    return (
        "# Handoff - Architect to Codex\n\n"
        "Status: OPEN\n"
        f"Current AIDP Task: {contract.task_id}\n"
        "Current Phase: READY / IMPLEMENTATION\n"
        "Task Status: READY\n"
    )


def _architect_handoff(contract: ArchitectTaskContract) -> str:
    return (
        f"# Handoff - Architecture Review {contract.task_id}\n\n"
        "Status: WAITING\n"
        f"Task: {contract.task_id}\n"
        "Task Status: READY\n"
        "Reviewer: Architect\n"
    )


def _atomic_write(path: Path, content: bytes) -> None:
    temporary = path.with_name(f".{path.name}.aidp-writer.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _same_execution_authority(contract: ArchitectTaskContract, metadata: TaskMetadata) -> bool:
    return (
        contract.task_id == metadata.task_id
        and contract.phase == metadata.phase
        and contract.allowed_scope == metadata.allowed_scope
        and contract.prohibited_actions == metadata.prohibited_actions
        and contract.validation_requirements == metadata.validation_requirements
        and contract.product_owner_gate == metadata.product_owner_gate
    )


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")


def _string(value: dict[str, object], name: str) -> str:
    item = value.get(name)
    if not isinstance(item, str):
        raise ValueError(f"{name} must be a string")
    return item


def _strings(value: dict[str, object], name: str) -> tuple[str, ...]:
    item = value.get(name)
    if not isinstance(item, list) or any(not isinstance(entry, str) for entry in item):
        raise ValueError(f"{name} must be a string array")
    return tuple(item)


def _boolean(value: dict[str, object], name: str) -> bool:
    item = value.get(name)
    if not isinstance(item, bool):
        raise ValueError(f"{name} must be boolean")
    return item
