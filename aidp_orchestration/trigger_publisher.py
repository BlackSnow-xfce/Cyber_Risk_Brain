"""Fail-closed local contract trigger and Git review publisher."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

from .architect_writer import ArchitectContractWriter
from .contracts import (
    AIDPState, ArchitectTaskContract, ConsumptionEvent, ConsumptionState,
    ContractInboxItem, ControlPlaneAction, ControlPlaneResult, ExecutionStatus,
    PublishResult, ReworkContract, ReviewEnvelope, ScopeCompliance, TriggerResult,
    TriggerStatus, WriterAction, WriterResult, utc_now,
)
from .control_plane import AIDPControlPlane
from .executor import GitInspector
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .lifecycle_projection import LifecycleProjection


class WriterBoundary(Protocol):
    def materialize_task(self, contract: ArchitectTaskContract) -> WriterResult: ...
    def materialize_rework(self, contract: ReworkContract) -> WriterResult: ...


class ControlPlaneBoundary(Protocol):
    def decide(self): ...
    def run_once(self) -> ControlPlaneResult: ...


class PublisherBoundary(Protocol):
    def commit_materialization(self, result: WriterResult) -> str: ...
    def publish(self, result: ControlPlaneResult, expected_branch: str) -> PublishResult: ...


class LocalContractInbox:
    def __init__(self, root: Path):
        self.root = root / "contract-inbox"

    def pending(self) -> tuple[ContractInboxItem, ...]:
        if not self.root.exists():
            return ()
        items = tuple(self._load(path) for path in sorted(self.root.glob("*.json")))
        ids = [item.contract_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate contract_id")
        return items

    def persist(self, item: ContractInboxItem) -> Path:
        path = self.root / f"{item.contract_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = serialize_contract_inbox_item(item) + "\n"
        try:
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(serialized)
        except FileExistsError:
            if path.read_text(encoding="utf-8") != serialized:
                raise RuntimeError("immutable contract inbox identity collision") from None
        if self._load(path) != item:
            raise RuntimeError("contract inbox persistence validation failed")
        return path

    @staticmethod
    def _load(path: Path) -> ContractInboxItem:
        return LocalContractInbox.parse(path.read_bytes())

    @staticmethod
    def parse(content: bytes) -> ContractInboxItem:
        payload = json.loads(content.decode("utf-8-sig", errors="strict"))
        value = payload.get("contract_inbox_item") if isinstance(payload, dict) else None
        if not isinstance(value, dict) or set(value) != {"contract_id", "contract_type", "contract", "received_at"}:
            raise ValueError("malformed contract inbox item")
        contract_value = value["contract"]
        if not isinstance(contract_value, dict):
            raise ValueError("contract must be an object")
        contract_type = _string(value, "contract_type")
        contract = _architect_contract(contract_value) if contract_type == "architect_task" else (
            _rework_contract(contract_value) if contract_type == "rework" else None
        )
        if contract is None:
            raise ValueError("unknown contract type")
        return ContractInboxItem(_string(value, "contract_id"), contract, datetime.fromisoformat(_string(value, "received_at")))


class ConsumptionStore:
    _allowed = {
        None: {ConsumptionState.RECEIVED},
        ConsumptionState.RECEIVED: {ConsumptionState.MATERIALIZED, ConsumptionState.BLOCKED},
        ConsumptionState.MATERIALIZED: {ConsumptionState.EXECUTING, ConsumptionState.BLOCKED},
        ConsumptionState.EXECUTING: {ConsumptionState.REVIEW_PUBLISHED, ConsumptionState.BLOCKED},
        ConsumptionState.REVIEW_PUBLISHED: set(), ConsumptionState.BLOCKED: set(),
    }

    def __init__(self, root: Path):
        self.path = root / "consumption-events.jsonl"

    def current(self, contract_id: str) -> ConsumptionState | None:
        states: dict[str, ConsumptionState] = {}
        if not self.path.exists():
            return None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line).get("consumption_event")
            if not isinstance(value, dict):
                raise ValueError("malformed consumption log")
            event_id = value.get("contract_id")
            if not isinstance(event_id, str):
                raise ValueError("malformed consumption contract_id")
            candidate = ConsumptionState(value.get("state"))
            previous = states.get(event_id)
            if candidate not in self._allowed[previous]:
                raise ValueError("inconsistent consumption transition")
            states[event_id] = candidate
        return states.get(contract_id)

    def append(self, contract_id: str, state: ConsumptionState, reason: str) -> None:
        previous = self.current(contract_id)
        if state not in self._allowed[previous]:
            raise ValueError("invalid consumption transition")
        event = ConsumptionEvent(contract_id, state, utc_now(), reason)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(_json({"consumption_event": event}) + "\n")


class GitReviewPublisher:
    def __init__(self, repository: AIDPRepository, *, projection: LifecycleProjection | None = None):
        self.repository = repository
        self.git = GitInspector(repository.root)
        self.projection = projection or LifecycleProjection(repository.root)

    def commit_materialization(self, result: WriterResult) -> str:
        paths = tuple(sorted(result.materialized_paths))
        task_id = result.decision.task_id
        expected = tuple(sorted((
            f".ai/tasks/ready/{task_id}.md",
            ".ai/handoff/TO-ARCHITECT.md",
            ".ai/handoff/TO-CODEX.md",
        ))) if task_id else ()
        if result.decision.action is not WriterAction.MATERIALIZE_READY or paths != expected:
            raise RuntimeError("writer materialization paths are not authorized")
        if self.git.changed_files() != paths:
            raise RuntimeError("writer materialization contains additional files")
        self._commit_exact(paths, f"aidp({result.decision.task_id}): materialize architect contract")
        return self.git.head()

    def publish(self, result: ControlPlaneResult, expected_branch: str) -> PublishResult:
        execution = result.runner_result.execution_result if result.runner_result else None
        branch = self.git.branch()
        try:
            if branch != expected_branch:
                raise RuntimeError("branch mismatch")
            if result.final_action is not ControlPlaneAction.READY_FOR_ARCHITECT or execution is None:
                raise RuntimeError("execution is not review-ready")
            if not result.architect_inbox_path or not Path(result.architect_inbox_path).is_file():
                raise RuntimeError("architect inbox is missing")
            if execution.status is not ExecutionStatus.SUCCESS or execution.scope_compliance is not ScopeCompliance.COMPLIANT:
                raise RuntimeError("execution result is not successful and compliant")
            if not execution.validation_results or any(not item.passed for item in execution.validation_results):
                raise RuntimeError("validation did not pass")
            paths = tuple(sorted(execution.changed_files))
            if not paths or self.git.changed_files() != paths:
                raise RuntimeError("publisher detected additional files")
            if any(path.startswith(".ai/tasks/") or path.startswith(".ai/handoff/") for path in paths):
                raise RuntimeError("execution may not commit task or handoff files")
            self._commit_exact(paths, f"aidp({execution.task_id}): execution {execution.execution_id}")
            execution_commit = self.git.head()
            envelope = ReviewEnvelope(
                execution.task_id, execution.execution_id, branch, execution.start_commit,
                execution_commit, execution.status, paths, execution.scope_compliance,
                execution.validation_results, execution.failure_reason, AIDPState.READY_FOR_ARCHITECT, utc_now(),
            )
            relative = f".ai/orchestration/review-inbox/{execution.task_id}-{execution.execution_id}.json"
            path = self.repository.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                stream.write(serialize_review_envelope(envelope) + "\n")
            envelope_commit = (
                self.projection.project_rework_ready_for_architect(execution.task_id, relative)
                if result.runner_result and result.runner_result.current_state is AIDPState.REWORK_REQUIRED
                else self.projection.project_ready_for_architect(execution.task_id, relative)
            )
            self._git("remote", "get-url", "origin")
            self._git("push", "origin", branch)
            return PublishResult(branch, execution_commit, relative, envelope_commit, "PUSHED", AIDPState.READY_FOR_ARCHITECT)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            return PublishResult(branch, None, None, None, "NOT_PUSHED", None, str(exc))

    def _commit_exact(self, paths: tuple[str, ...], message: str) -> None:
        self._git("add", "--", *paths)
        staged = self._nul("diff", "--cached", "--name-only", "-z")
        if tuple(sorted(staged)) != paths:
            raise RuntimeError("staged paths differ from authorized paths")
        self._git("commit", "-m", message)

    def _git(self, *args: str) -> str:
        return subprocess.check_output(("git", *args), cwd=self.repository.root, text=True, stderr=subprocess.STDOUT).strip()

    def _nul(self, *args: str) -> tuple[str, ...]:
        output = subprocess.check_output(("git", *args), cwd=self.repository.root)
        if output and not output.endswith(b"\0"):
            raise RuntimeError("malformed Git path output")
        return tuple(output[:-1].decode("utf-8").split("\0")) if output else ()


class AIDPWatchOnce:
    def __init__(self, repository: AIDPRepository, *, writer: WriterBoundary | None = None,
                 control_plane: ControlPlaneBoundary | None = None, publisher: PublisherBoundary | None = None,
                 runtime_root: Path | None = None, timeout_seconds: float = 900.0,
                 execution_lock_active: Callable[[], bool] | None = None):
        root = runtime_root or LocalRuntimeStore.for_repository(repository.root).root
        self.inbox = LocalContractInbox(root)
        self.consumption = ConsumptionStore(root)
        self.repository = repository
        self.execution_lock_active = execution_lock_active or self._execution_lock_active
        self.writer = writer or ArchitectContractWriter(repository)
        self.control_plane = control_plane or AIDPControlPlane(repository, timeout_seconds=timeout_seconds)
        self.publisher = publisher or GitReviewPublisher(repository)

    def run_once(self) -> TriggerResult:
        item: ContractInboxItem | None = None
        lifecycle_state: ConsumptionState | None = None
        writer_result = None
        control_result = None
        publish_result = None
        try:
            try:
                items = self.inbox.pending()
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                return TriggerResult(TriggerStatus.BLOCKED, None, None, failure_reason=f"contract inbox is invalid: {exc.__class__.__name__}")
            if not items:
                return TriggerResult(TriggerStatus.NO_ACTION, None, None)
            candidates = tuple(
                candidate for candidate in items
                if self.consumption.current(candidate.contract_id)
                not in {ConsumptionState.BLOCKED, ConsumptionState.REVIEW_PUBLISHED}
            )
            if not candidates:
                return TriggerResult(TriggerStatus.NO_ACTION, None, None)
            if len(candidates) != 1:
                return TriggerResult(TriggerStatus.BLOCKED, None, None, failure_reason="contract inbox is ambiguous")
            item = candidates[0]
            current = self.consumption.current(item.contract_id)
            if current in {ConsumptionState.RECEIVED, ConsumptionState.MATERIALIZED, ConsumptionState.EXECUTING}:
                if current is ConsumptionState.EXECUTING and self.execution_lock_active():
                    return TriggerResult(TriggerStatus.BLOCKED, item.contract_id, current, failure_reason="contract execution is still locally active")
                return self._block(
                    item.contract_id, current,
                    f"recovered abandoned {current.value} consumption as terminal BLOCKED",
                )
            if current is not None:
                return TriggerResult(TriggerStatus.BLOCKED, item.contract_id, current, failure_reason="contract_id was already consumed")
            if self.execution_lock_active():
                return TriggerResult(TriggerStatus.BLOCKED, item.contract_id, None, failure_reason="local execution lock is active")
            self.consumption.append(item.contract_id, ConsumptionState.RECEIVED, "immutable contract received")
            lifecycle_state = ConsumptionState.RECEIVED
            writer_result = (self.writer.materialize_task(item.contract) if isinstance(item.contract, ArchitectTaskContract)
                             else self.writer.materialize_rework(item.contract))
            if writer_result.decision.action is WriterAction.BLOCKED:
                return self._block(item.contract_id, ConsumptionState.RECEIVED, writer_result.failure_reason or writer_result.decision.reason, writer_result)
            if writer_result.materialized_paths:
                self.publisher.commit_materialization(writer_result)
            self.consumption.append(item.contract_id, ConsumptionState.MATERIALIZED, "contract materialized")
            lifecycle_state = ConsumptionState.MATERIALIZED
            decision = self.control_plane.decide()
            if decision.action is not ControlPlaneAction.EXECUTE:
                return self._block(item.contract_id, ConsumptionState.MATERIALIZED, f"control plane decided {decision.action.value}", writer_result)
            self.consumption.append(item.contract_id, ConsumptionState.EXECUTING, "control plane authorized execution")
            lifecycle_state = ConsumptionState.EXECUTING
            control_result = self.control_plane.run_once()
            publish_result = self.publisher.publish(control_result, decision.branch)
            if publish_result.push_status != "PUSHED":
                blocked = self._block(item.contract_id, ConsumptionState.EXECUTING, publish_result.failure_reason or "publication failed", writer_result, control_result, publish_result)
                lifecycle_state = ConsumptionState.BLOCKED
                if control_result.runner_result and control_result.runner_result.shutdown_requested:
                    raise KeyboardInterrupt
                return blocked
            self.consumption.append(item.contract_id, ConsumptionState.REVIEW_PUBLISHED, "review envelope pushed")
            lifecycle_state = ConsumptionState.REVIEW_PUBLISHED
            return TriggerResult(TriggerStatus.PUBLISHED, item.contract_id, ConsumptionState.REVIEW_PUBLISHED, writer_result, control_result, publish_result)
        except KeyboardInterrupt:
            if item is not None and lifecycle_state not in {None, ConsumptionState.BLOCKED, ConsumptionState.REVIEW_PUBLISHED}:
                self._block_safely(item.contract_id, lifecycle_state, "watch-once interrupted", writer_result, control_result, publish_result)
            raise
        except Exception as exc:
            reason = f"watch-once failed: {exc.__class__.__name__}"
            if item is not None and lifecycle_state not in {None, ConsumptionState.BLOCKED, ConsumptionState.REVIEW_PUBLISHED}:
                return self._block_safely(item.contract_id, lifecycle_state, reason, writer_result, control_result, publish_result)
            return TriggerResult(TriggerStatus.ERROR, None, None, failure_reason=reason)

    def _block(self, contract_id: str, state: ConsumptionState, reason: str, writer_result=None, control_result=None, publish_result=None) -> TriggerResult:
        self.consumption.append(contract_id, ConsumptionState.BLOCKED, reason)
        return TriggerResult(TriggerStatus.BLOCKED, contract_id, ConsumptionState.BLOCKED, writer_result, control_result, publish_result, reason)

    def _block_safely(self, contract_id: str, state: ConsumptionState, reason: str, writer_result=None, control_result=None, publish_result=None) -> TriggerResult:
        try:
            return self._block(contract_id, state, reason, writer_result, control_result, publish_result)
        except Exception as exc:
            return TriggerResult(
                TriggerStatus.ERROR, contract_id, state, writer_result, control_result,
                publish_result, f"terminal consumption persistence failed: {exc.__class__.__name__}",
            )

    def _execution_lock_active(self) -> bool:
        lock_path = subprocess.check_output(
            ("git", "rev-parse", "--git-path", "aidp-orchestration/execution.lock"),
            cwd=self.repository.root, text=True,
        ).strip()
        resolved = Path(lock_path) if Path(lock_path).is_absolute() else self.repository.root / lock_path
        return resolved.exists()


def serialize_review_envelope(value: ReviewEnvelope) -> str:
    return _json({"architect_review_envelope": value})


def serialize_contract_inbox_item(value: ContractInboxItem) -> str:
    contract_type = "architect_task" if isinstance(value.contract, ArchitectTaskContract) else "rework"
    return _json({"contract_inbox_item": {
        "contract_id": value.contract_id,
        "contract_type": contract_type,
        "contract": value.contract,
        "received_at": value.received_at,
    }})


def serialize_trigger_result(value: TriggerResult) -> str:
    return _json({"trigger_result": value})


def _architect_contract(v: dict[str, object]) -> ArchitectTaskContract:
    expected = {"task_id", "title", "phase", "expected_head", "allowed_scope", "prohibited_actions", "validation_requirements", "acceptance_criteria", "product_owner_gate", "created_at"}
    if set(v) != expected: raise ValueError("invalid ArchitectTaskContract schema")
    return ArchitectTaskContract(_string(v,"task_id"), _string(v,"title"), _string(v,"phase"), _string(v,"expected_head"),
        _strings(v,"allowed_scope"), _strings(v,"prohibited_actions"), _strings(v,"validation_requirements"),
        _strings(v,"acceptance_criteria"), _boolean(v,"product_owner_gate"), datetime.fromisoformat(_string(v,"created_at")))


def _rework_contract(v: dict[str, object]) -> ReworkContract:
    expected = {"task_id", "review_iteration", "expected_head", "allowed_rework_scope", "findings", "required_validations", "created_at"}
    if set(v) != expected: raise ValueError("invalid ReworkContract schema")
    iteration = v.get("review_iteration")
    if not isinstance(iteration, int) or isinstance(iteration, bool): raise ValueError("review_iteration must be integer")
    return ReworkContract(_string(v,"task_id"), iteration, _string(v,"expected_head"), _strings(v,"allowed_rework_scope"),
                          _strings(v,"findings"), _strings(v,"required_validations"), datetime.fromisoformat(_string(v,"created_at")))


def _string(v: dict[str, object], name: str) -> str:
    value = v.get(name)
    if not isinstance(value, str): raise ValueError(f"{name} must be string")
    return value


def _strings(v: dict[str, object], name: str) -> tuple[str, ...]:
    value = v.get(name)
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value): raise ValueError(f"{name} must be string array")
    return tuple(value)


def _boolean(v: dict[str, object], name: str) -> bool:
    value = v.get(name)
    if not isinstance(value, bool): raise ValueError(f"{name} must be boolean")
    return value


def _json(value: object) -> str:
    def default(item: object) -> object:
        if hasattr(item, "__dataclass_fields__"): return asdict(item)
        if isinstance(item, datetime): return item.isoformat()
        if isinstance(item, Enum): return item.value
        raise TypeError(type(item).__name__)
    return json.dumps(value, default=default, sort_keys=True, separators=(",", ":"))
