"""Fail-closed AIDP Automation Control Plane 1.0."""

from __future__ import annotations

import fnmatch
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

from .contracts import (
    AIDPState,
    ArchitectInboxEntry,
    ControlPlaneAction,
    ControlPlaneDecision,
    ControlPlaneResult,
    OrchestrationDecision,
    ReworkContract,
    RunnerResult,
    RunnerStatus,
    TaskMetadata,
    utc_now,
)
from .executor import GitInspector
from .repository import AIDPRepository
from .runner import AIDPRunner
from .runtime import LocalRuntimeStore
from .validators import ValidatorRegistry
from .worktree import cleanliness_adapter, worktree_admission_reason


class RunnerBoundary(Protocol):
    def run_ready(self) -> RunnerResult: ...


class ReworkContractBoundary(Protocol):
    def load(self, task_id: str) -> ReworkContract | None: ...


class ArchitectInboxBoundary(Protocol):
    def persist(self, entry: ArchitectInboxEntry) -> Path: ...


class LocalReworkContractStore:
    """Read-only contract source in local orchestration runtime storage."""

    def __init__(self, root: Path):
        self.root = root

    def load(self, task_id: str) -> ReworkContract | None:
        legacy = self.root / "rework-contracts" / f"{task_id}.json"
        directory = self.root / "rework-contracts" / task_id
        paths = tuple(directory.glob("*.json")) if directory.exists() else ()
        if legacy.exists():
            paths = (*paths, legacy)
        if not paths:
            return None
        contracts = tuple(self._read(path) for path in paths)
        highest = max(contract.review_iteration for contract in contracts)
        selected = tuple(contract for contract in contracts if contract.review_iteration == highest)
        if len({serialize_rework_contract(contract) for contract in selected}) != 1:
            raise ValueError("ambiguous rework contracts for active iteration")
        return selected[0]

    @staticmethod
    def _read(path: Path) -> ReworkContract:
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = payload.get("rework_contract") if isinstance(payload, dict) else None
        if not isinstance(value, dict):
            raise ValueError("invalid rework contract envelope")
        return ReworkContract(
            task_id=_string(value, "task_id"),
            review_iteration=_integer(value, "review_iteration"),
            expected_head=_string(value, "expected_head"),
            allowed_rework_scope=_strings(value, "allowed_rework_scope"),
            findings=_strings(value, "findings"),
            required_validations=_strings(value, "required_validations"),
            created_at=datetime.fromisoformat(_string(value, "created_at")),
        )


class LocalArchitectInbox:
    """Persists review evidence only; inbox entries grant no approval authority."""

    def __init__(self, root: Path):
        self.root = root

    def persist(self, entry: ArchitectInboxEntry) -> Path:
        path = self.root / "architect-inbox" / f"{entry.execution_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = serialize_architect_inbox_entry(entry)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(serialized + "\n")
        persisted = json.loads(path.read_text(encoding="utf-8"))
        if persisted.get("architect_inbox_entry", {}).get("execution_id") != entry.execution_id:
            raise RuntimeError("architect inbox persistence validation failed")
        return path


class AIDPControlPlane:
    def __init__(
        self,
        repository: AIDPRepository,
        *,
        runner: RunnerBoundary | None = None,
        contract_store: ReworkContractBoundary | None = None,
        architect_inbox: ArchitectInboxBoundary | None = None,
        validator_registry: ValidatorRegistry | None = None,
        is_worktree_clean: Callable[[], bool] | None = None,
        worktree_changed_files: Callable[[], tuple[str, ...]] | None = None,
        timeout_seconds: float = 900.0,
    ):
        runtime_root = (
            LocalRuntimeStore.for_repository(repository.root).root
            if contract_store is None or architect_inbox is None
            else None
        )
        self.repository = repository
        self.runner = runner or AIDPRunner(repository, timeout_seconds=timeout_seconds)
        self.contract_store = contract_store or LocalReworkContractStore(_required_root(runtime_root))
        self.architect_inbox = architect_inbox or LocalArchitectInbox(_required_root(runtime_root))
        self.validator_registry = validator_registry or ValidatorRegistry()
        inspector = GitInspector(repository.root)
        self.worktree_changed_files = (
            worktree_changed_files
            or (cleanliness_adapter(is_worktree_clean) if is_worktree_clean is not None else inspector.changed_files)
        )

    def decide(self) -> ControlPlaneDecision:
        decision = self.repository.inspect()
        state = decision.state
        if state is AIDPState.WAITING:
            return self._decision(decision, ControlPlaneAction.NO_ACTION, "no active AIDP task")
        if state is AIDPState.READY_FOR_ARCHITECT:
            return self._decision(decision, ControlPlaneAction.READY_FOR_ARCHITECT, "task awaits Architect review")
        if state is AIDPState.WAITING_FOR_PRODUCT_OWNER:
            return self._decision(decision, ControlPlaneAction.WAITING_FOR_PRODUCT_OWNER, "Product Owner gate is authoritative")
        if state in {AIDPState.DONE, AIDPState.ARCHITECT_APPROVED}:
            return self._decision(decision, ControlPlaneAction.NO_ACTION, "no automated transition is authorized")
        if state is AIDPState.READY_FOR_CODEX:
            reason = self._ready_admission(decision.task_id, state_dir="ready", allow_authorized_dirty=True)
            return self._execution_decision(decision, reason)
        if state is AIDPState.REWORK_REQUIRED:
            reason = self._rework_admission(decision.task_id, decision.commit)
            return self._execution_decision(decision, reason)
        return self._decision(
            decision,
            ControlPlaneAction.BLOCKED,
            "; ".join(decision.reasons) or f"state {state} has no execution authority",
        )

    def run_once(self) -> ControlPlaneResult:
        try:
            decision = self.decide()
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            fallback = ControlPlaneDecision(
                ControlPlaneAction.BLOCKED,
                None,
                AIDPState.BLOCKED,
                "UNKNOWN",
                "UNKNOWN",
                f"control-plane inspection failed: {exc.__class__.__name__}",
            )
            return ControlPlaneResult(fallback, ControlPlaneAction.BLOCKED, failure_reason=fallback.reason)
        if decision.action is not ControlPlaneAction.EXECUTE:
            return ControlPlaneResult(decision, decision.action)

        try:
            runner_result = self.runner.run_ready()
        except Exception as exc:
            reason = f"runner failed: {exc.__class__.__name__}"
            return ControlPlaneResult(decision, ControlPlaneAction.BLOCKED, failure_reason=reason)
        execution = runner_result.execution_result
        if runner_result.status is not RunnerStatus.EXECUTED or execution is None:
            reason = "runner did not produce an execution result"
            return ControlPlaneResult(decision, ControlPlaneAction.BLOCKED, runner_result, failure_reason=reason)

        entry = ArchitectInboxEntry(
            execution.task_id,
            execution.execution_id,
            decision.repository_state,
            runner_result.intended_next_state,
            execution.status,
            execution.changed_files,
            execution.scope_compliance,
            execution.validation_results,
            execution.failure_reason,
            decision.branch,
            execution.start_commit,
            execution.resulting_commit,
            utc_now(),
        )
        try:
            inbox_path = self.architect_inbox.persist(entry)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            reason = f"architect inbox persistence failed: {exc.__class__.__name__}"
            return ControlPlaneResult(
                decision,
                ControlPlaneAction.BLOCKED,
                runner_result,
                entry,
                failure_reason=reason,
            )
        final_action = (
            ControlPlaneAction.READY_FOR_ARCHITECT
            if execution.is_review_ready and runner_result.intended_next_state is AIDPState.READY_FOR_ARCHITECT
            else ControlPlaneAction.BLOCKED
        )
        return ControlPlaneResult(decision, final_action, runner_result, entry, str(inbox_path))

    def _ready_admission(self, task_id: str | None, *, state_dir: str, allow_authorized_dirty: bool = False) -> str | None:
        metadata = self._metadata(task_id, state_dir)
        if metadata is None:
            return "execution metadata is missing or inconsistent"
        unknown = self.validator_registry.unknown(metadata.validation_requirements)
        if unknown:
            return f"unknown validator: {unknown[0]}"
        return worktree_admission_reason(
            self.worktree_changed_files,
            allowed_scope=metadata.allowed_scope if allow_authorized_dirty else None,
            prohibited_actions=metadata.prohibited_actions,
        )

    def _rework_admission(self, task_id: str | None, expected_head: str) -> str | None:
        base_reason = self._ready_admission(task_id, state_dir="review")
        if base_reason is not None:
            return base_reason
        if task_id is None:
            return "rework task id is missing"
        metadata = self._metadata(task_id, "review")
        if metadata is None:
            return "rework metadata is missing"
        try:
            contract = self.contract_store.load(task_id)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            return f"rework contract is invalid: {exc.__class__.__name__}"
        if contract is None:
            return "rework contract is missing"
        if contract.task_id != task_id:
            return "rework task and contract task_id do not match"
        if contract.expected_head != expected_head:
            return "rework contract expected_head is stale"
        if not scope_is_subset(contract.allowed_rework_scope, metadata.allowed_scope):
            return "rework contract widens the authorized scope"
        unknown = self.validator_registry.unknown(contract.required_validations)
        if unknown:
            return f"unknown rework validator: {unknown[0]}"
        if any(item not in metadata.validation_requirements for item in contract.required_validations):
            return "rework validators are not authorized by task metadata"
        return None

    def _metadata(self, task_id: str | None, state_dir: str) -> TaskMetadata | None:
        if task_id is None:
            return None
        paths = tuple(path for path in self.repository.task_paths(state_dir) if path.stem == task_id)
        if len(paths) != 1:
            return None
        metadata = self.repository.parse_metadata(paths[0])
        return metadata if metadata is not None and metadata.task_id == task_id else None

    def _execution_decision(self, decision: OrchestrationDecision, blocked_reason: str | None) -> ControlPlaneDecision:
        if blocked_reason is not None:
            return self._decision(decision, ControlPlaneAction.BLOCKED, blocked_reason)
        return self._decision(decision, ControlPlaneAction.EXECUTE, "repository state explicitly authorizes execution")

    @staticmethod
    def _decision(decision: OrchestrationDecision, action: ControlPlaneAction, reason: str) -> ControlPlaneDecision:
        return ControlPlaneDecision(action, decision.task_id, decision.state, decision.branch, decision.commit, reason)


def scope_is_subset(candidate: tuple[str, ...], authorized: tuple[str, ...]) -> bool:
    for item in candidate:
        if item in authorized:
            continue
        if any(character in item for character in "*?["):
            return False
        if not any(fnmatch.fnmatchcase(item, pattern) for pattern in authorized):
            return False
    return True


def _required_root(root: Path | None) -> Path:
    if root is None:
        raise RuntimeError("local orchestration runtime root is unavailable")
    return root


def serialize_control_plane_result(result: ControlPlaneResult) -> str:
    return json.dumps({"control_plane_result": asdict(result)}, default=_json_default, sort_keys=True)


def serialize_control_plane_decision(decision: ControlPlaneDecision) -> str:
    return json.dumps({"control_plane_decision": asdict(decision)}, default=_json_default, sort_keys=True)


def serialize_rework_contract(contract: ReworkContract) -> str:
    return json.dumps({"rework_contract": asdict(contract)}, default=_json_default, sort_keys=True)


def serialize_architect_inbox_entry(entry: ArchitectInboxEntry) -> str:
    return json.dumps({"architect_inbox_entry": asdict(entry)}, default=_json_default, sort_keys=True)


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


def _integer(value: dict[str, object], name: str) -> int:
    item = value.get(name)
    if not isinstance(item, int) or isinstance(item, bool):
        raise ValueError(f"{name} must be an integer")
    return item


def _strings(value: dict[str, object], name: str) -> tuple[str, ...]:
    item = value.get(name)
    if not isinstance(item, list) or any(not isinstance(entry, str) for entry in item):
        raise ValueError(f"{name} must be a string array")
    return tuple(item)
