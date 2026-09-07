"""Fail-closed local contract trigger and Git review publisher."""

from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
from uuid import uuid4
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

from .architect_writer import ArchitectContractWriter
from .contracts import (
    AIDPState, ArchitectReviewDisposition, ArchitectReviewRecoveryAuthorityV1, ArchitectTaskContract,
    CodexExecutionRequest, ConsumptionEvent, ConsumptionState, ContractInboxItem, ControlPlaneAction,
    ControlPlaneResult, ExecutionStatus, ProductOwnerGateDependencyResult, ProductOwnerGateDependencyState,
    PublishResult, ReworkContract, ReviewEnvelope, ScopeCompliance, TriggerResult,
    TriggerStatus, WriterAction, WriterResult, LegacyRecoveryAuthorizationV1, RecoveryAuthorizationV1,
    ProductOwnerGateDependencyAuthorityV1,
    canonical_digest, utc_now,
)
from .control_plane import AIDPControlPlane
from .operator_stream import ActivitySink
from .executor import GitInspector
from .architect_review import ArchitectReviewCoordinator, ProductWorktreeIdentityGuard, architect_result_schema, create_review_request
from .runner import AIDPRunner
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


class ProductOwnerGateDependencyRunner:
    """One-shot lane for the technical dependency of an already waiting PO gate."""

    def __init__(
        self, repository: AIDPRepository, *, runtime_root: Path,
        architect: ArchitectReviewCoordinator, timeout_seconds: float = 900.0,
    ) -> None:
        self.repository = repository
        self.inbox = LocalContractInbox(runtime_root)
        self.store = LocalRuntimeStore.for_repository(repository.root)
        self.architect = architect
        self.timeout_seconds = timeout_seconds

    def run_once(self) -> ProductOwnerGateDependencyResult:
        all_candidates = tuple(item for item in self.inbox.pending() if isinstance(item.contract, ProductOwnerGateDependencyAuthorityV1))
        claimed = tuple(item for item in all_candidates if self.store.product_owner_gate_dependency_claimed(item.contract_id))
        candidates = tuple(item for item in all_candidates if item not in claimed)
        if claimed:
            item = claimed[-1]
            return ProductOwnerGateDependencyResult(
                item.contract_id, item.contract.dependency_id, ProductOwnerGateDependencyState.BLOCKED,
                reason="claimed gate dependency authority is terminal or requires explicit recovery authority",
            )
        if not candidates:
            return ProductOwnerGateDependencyResult(None, None, ProductOwnerGateDependencyState.NO_ACTION)
        if len(candidates) != 1:
            return ProductOwnerGateDependencyResult(None, None, ProductOwnerGateDependencyState.BLOCKED, reason="gate dependency authority is ambiguous")
        item = candidates[0]
        authority = item.contract
        execution_id = str(uuid4())
        try:
            self._validate(authority)
            parent_snapshot = self._parent_snapshot(authority.parent_task_id)
            self.store.claim_product_owner_gate_dependency(authority, execution_id)
            self.store.persist_product_owner_gate_dependency_status(
                authority.authority_id, authority.dependency_id, "EXECUTING",
                "one-shot dependency authority consumed", execution_id=execution_id,
            )
            workspace, dependency_branch = self._prepare_workspace(authority)
            self._assert_parent_unchanged(authority, parent_snapshot)
            workspace_repository = AIDPRepository(workspace, task_namespace="infrastructure")
            task_path = workspace / self._parent_task_path(authority.parent_task_id).relative_to(self.repository.root)
            request = CodexExecutionRequest(
                task_id=authority.dependency_id, task_path=task_path,
                repository=str(workspace), branch=dependency_branch,
                base_commit=authority.expected_head, expected_head=authority.expected_head,
                phase="PRODUCT_OWNER_GATE_DEPENDENCY", allowed_scope=authority.allowed_scope,
                prohibited_actions=authority.prohibited_actions,
                validation_requirements=authority.validation_requirements, created_at=utc_now(),
                execution_id=execution_id, authority_instructions=authority.acceptance_criteria,
            )
            runner = AIDPRunner(workspace_repository, timeout_seconds=self.timeout_seconds)
            result = runner.execute_authorized(
                request, contract_id=authority.authority_id, namespace="product-owner-gate-dependency",
            )
            if result.status is not ExecutionStatus.SUCCESS or result.scope_compliance is not ScopeCompliance.COMPLIANT:
                raise RuntimeError("dependency execution did not produce compliant success")
            if not result.validation_results or any(not value.passed for value in result.validation_results):
                raise RuntimeError("dependency validation did not pass")
            if not result.changed_files:
                raise RuntimeError("dependency execution produced no reviewable implementation")
            self._assert_parent_unchanged(authority, parent_snapshot)
            implementation_commit = self._commit_exact(workspace, result.changed_files, f"aidp({authority.dependency_id}): implement PO gate dependency")
            self._assert_parent_unchanged(authority, parent_snapshot)
            envelope = ReviewEnvelope(
                authority.dependency_id, result.execution_id, dependency_branch, result.start_commit,
                implementation_commit, result.status, tuple(sorted(result.changed_files)), result.scope_compliance,
                result.validation_results, result.failure_reason, AIDPState.READY_FOR_ARCHITECT, utc_now(),
            )
            relative = f".ai/orchestration/gate-dependency-review/{authority.dependency_id}-{result.execution_id}.json"
            envelope_path = workspace / relative
            envelope_path.parent.mkdir(parents=True, exist_ok=True)
            envelope_text = serialize_review_envelope(envelope) + "\n"
            with envelope_path.open("x", encoding="utf-8", newline="\n") as stream: stream.write(envelope_text)
            envelope_commit = self._commit_exact(workspace, (relative,), f"aidp({authority.dependency_id}): publish dependency review evidence")
            self._git_at(workspace, "push", "origin", dependency_branch)
            self._assert_parent_unchanged(authority, parent_snapshot)
            architect = self._workspace_architect(workspace, dependency_branch)
            identity = architect.identity_guard.validate(expected_head=envelope_commit)
            request_values = dict(
                task_id=authority.dependency_id, review_iteration=0, execution_id=result.execution_id,
                repository=identity["repository"], git_common_dir=identity["git_common_dir"],
                branch=identity["branch"], remote_url=identity["remote_url"],
                authority_contract_id=authority.authority_id, authority_contract_digest=authority.expected_id(),
                original_allowed_scope=authority.allowed_scope,
                original_prohibited_actions=authority.prohibited_actions,
                original_validation_requirements=authority.validation_requirements,
                original_acceptance_criteria=authority.acceptance_criteria, product_owner_gate=True,
                review_envelope_path=relative, review_envelope_digest=canonical_digest(json.loads(envelope_text)),
                execution_status=result.status, start_commit=result.start_commit,
                resulting_commit=implementation_commit, review_envelope_commit=envelope_commit,
                changed_files=tuple(sorted(result.changed_files)), validation_results=result.validation_results,
                scope_compliance=result.scope_compliance, expected_current_head=envelope_commit,
                current_head=envelope_commit, reviewed_head=implementation_commit,
                reviewed_tree_hash=self._git_at(workspace, "rev-parse", f"{implementation_commit}^{{tree}}"),
                previous_review_result_id=None, previous_rework_contract_id=None,
                previous_finding_fingerprints=(), created_at=utc_now(),
            )
            review_request = create_review_request(**request_values)
            self.store.persist_architect_request(review_request)
            schema_path = self.store.root / "schemas" / "gate-dependency-architect-result.json"
            schema_path.parent.mkdir(parents=True, exist_ok=True)
            schema_path.write_text(json.dumps(architect_result_schema(), sort_keys=True), encoding="utf-8")
            architect_result = architect.review(review_request, schema_path=schema_path)
            architect.revalidate(review_request)
            self.store.persist_architect_result(architect_result)
            self._assert_parent_unchanged(authority, parent_snapshot)
            state = (
                ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING
                if architect_result.disposition is ArchitectReviewDisposition.PASS
                else ProductOwnerGateDependencyState.BLOCKED
            )
            reason = "independent review passed; administrator provisioning remains required" if state is ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING else "independent review did not pass"
            self.store.persist_product_owner_gate_dependency_status(
                authority.authority_id, authority.dependency_id, state.value, reason,
                execution_id=execution_id, architect_result_id=architect_result.review_result_id,
            )
            return ProductOwnerGateDependencyResult(authority.authority_id, authority.dependency_id, state, execution_id, architect_result.review_result_id, reason)
        except Exception as exc:
            reason = f"gate dependency blocked: {exc.__class__.__name__}"
            try:
                self.store.persist_product_owner_gate_dependency_status(
                    authority.authority_id, authority.dependency_id, "BLOCKED", reason,
                    execution_id=execution_id,
                )
            except Exception:
                pass
            return ProductOwnerGateDependencyResult(authority.authority_id, authority.dependency_id, ProductOwnerGateDependencyState.BLOCKED, execution_id, reason=reason)

    def _validate(self, authority: ProductOwnerGateDependencyAuthorityV1) -> None:
        decision = self.repository.inspect()
        if self.repository.task_namespace != "infrastructure" or not self.repository.accepts_task_id(authority.parent_task_id):
            raise ValueError("dependency parent namespace mismatch")
        if decision.task_id != authority.parent_task_id or decision.state is not AIDPState.WAITING_FOR_PRODUCT_OWNER:
            raise ValueError("dependency parent is not the active Product Owner gate")
        common = Path(self._git_at(self.repository.root, "rev-parse", "--git-common-dir"))
        common = (self.repository.root / common).resolve() if not common.is_absolute() else common.resolve()
        remote = self._git_at(self.repository.root, "remote", "get-url", "origin")
        if authority.repository_id != canonical_digest(str(self.repository.root).lower()):
            raise ValueError("dependency repository identity mismatch")
        if authority.git_common_id != canonical_digest(str(common).lower()) or authority.repository_remote_id != canonical_digest(remote):
            raise ValueError("dependency Git identity mismatch")
        if self.repository.branch != authority.branch or self.repository.head != authority.expected_head:
            raise ValueError("dependency repository lineage mismatch")
        if utc_now() >= authority.expires_at:
            raise ValueError("dependency authority expired")

    def _parent_task_path(self, task_id: str) -> Path:
        paths = tuple(path for path in self.repository.task_paths("review") if path.stem == task_id)
        if len(paths) != 1: raise ValueError("dependency parent task is missing or ambiguous")
        return paths[0]

    def _parent_snapshot(self, task_id: str) -> str:
        paths = (self._parent_task_path(task_id), self.repository.ai_root / "handoff" / "TO-CODEX.md", self.repository.ai_root / "handoff" / "TO-ARCHITECT.md")
        return canonical_digest(tuple(
            (str(path.relative_to(self.repository.root)), canonical_digest(path.read_bytes()))
            for path in paths
        ))

    def _assert_parent_unchanged(self, authority: ProductOwnerGateDependencyAuthorityV1, snapshot: str) -> None:
        if self._parent_snapshot(authority.parent_task_id) != snapshot:
            raise RuntimeError("dependency execution attempted to modify parent authority")
        decision = self.repository.inspect()
        if decision.task_id != authority.parent_task_id or decision.state is not AIDPState.WAITING_FOR_PRODUCT_OWNER:
            raise RuntimeError("dependency execution changed parent lifecycle")
        if self.repository.branch != authority.branch or self.repository.head != authority.expected_head:
            raise RuntimeError("dependency execution changed parent branch or HEAD")

    def _prepare_workspace(self, authority: ProductOwnerGateDependencyAuthorityV1) -> tuple[Path, str]:
        workspace = Path(tempfile.gettempdir()).resolve() / f"aidp-gate-dependency-{authority.authority_id[:12]}"
        if workspace.exists(): raise RuntimeError("gate dependency workspace already exists")
        workspace.parent.mkdir(parents=True, exist_ok=True)
        branch = f"aidp/gate-dependency-{authority.authority_id[:12]}"
        self._git_at(self.repository.root, "worktree", "add", "-b", branch, str(workspace), authority.expected_head)
        self._git_at(workspace, "push", "-u", "origin", branch)
        return workspace, branch

    def _workspace_architect(self, workspace: Path, branch: str) -> ArchitectReviewCoordinator:
        original = self.architect
        guard = ProductWorktreeIdentityGuard(
            workspace, expected_branch=branch,
            excluded_roots=(*original.identity_guard.excluded_roots, self.repository.root),
            expected_remote_url=original.identity_guard.expected_remote_url,
        )
        return ArchitectReviewCoordinator(
            product_root=workspace, identity_guard=guard, runner=original.runner,
            launcher=original.launcher, timeout_seconds=original.timeout_seconds,
            max_capture_bytes=original.max_capture_bytes, clock=original.clock,
            model=original.model, activity_sink=original.activity_sink,
        )

    def _commit_exact(self, root: Path, paths: tuple[str, ...], message: str) -> str:
        paths = tuple(sorted(paths))
        git = GitInspector(root)
        if git.changed_files() != paths: raise RuntimeError("dependency commit contains unauthorized paths")
        self._git_at(root, "add", "--", *paths)
        staged = tuple(filter(None, self._git_at(root, "diff", "--cached", "--name-only").splitlines()))
        if tuple(sorted(staged)) != paths: raise RuntimeError("dependency staged paths differ from authority")
        self._git_at(root, "commit", "-m", message)
        return self._git_at(root, "rev-parse", "HEAD")

    @staticmethod
    def _git_at(root: Path, *args: str) -> str:
        return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


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
        payload = json.loads(
            content.decode("utf-8-sig", errors="strict"),
            object_pairs_hook=_reject_duplicate_json_fields,
        )
        value = payload.get("contract_inbox_item") if isinstance(payload, dict) else None
        if not isinstance(value, dict) or set(value) != {"contract_id", "contract_type", "contract", "received_at"}:
            raise ValueError("malformed contract inbox item")
        contract_value = value["contract"]
        if not isinstance(contract_value, dict):
            raise ValueError("contract must be an object")
        contract_type = _string(value, "contract_type")
        contract = _architect_contract(contract_value) if contract_type == "architect_task" else (
            _rework_contract(contract_value) if contract_type == "rework" else (
                _architect_review_recovery_authority(contract_value)
                if contract_type == "architect_review_recovery" else (
                    _product_owner_gate_dependency_authority(contract_value)
                    if contract_type == "product_owner_gate_dependency" else None
                )
            )
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
        ConsumptionState.BLOCKED: {ConsumptionState.RECOVERY_AUTHORIZED},
        ConsumptionState.RECOVERY_AUTHORIZED: {ConsumptionState.RECOVERY_EXECUTING, ConsumptionState.BLOCKED},
        ConsumptionState.RECOVERY_EXECUTING: {ConsumptionState.REVIEW_PUBLISHED, ConsumptionState.BLOCKED},
        ConsumptionState.REVIEW_PUBLISHED: set(),
    }

    def __init__(self, root: Path):
        self.path = root / "consumption-events.jsonl"

    def current(self, contract_id: str) -> ConsumptionState | None:
        events = self.events(contract_id)
        return events[-1].state if events else None

    def events(self, contract_id: str) -> tuple[ConsumptionEvent, ...]:
        states: dict[str, ConsumptionState] = {}
        events: list[ConsumptionEvent] = []
        if not self.path.exists():
            return ()
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
            if event_id == contract_id:
                events.append(ConsumptionEvent(
                    event_id, candidate,
                    datetime.fromisoformat(_string(value, "timestamp")),
                    _string(value, "reason"),
                ))
        return tuple(events)

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
            self._git("push", "origin", expected_branch)
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
                 execution_lock_active: Callable[[], bool] | None = None,
                 allow_test_failure_retry: bool = False,
                 activity_sink: ActivitySink | None = None):
        root = runtime_root or LocalRuntimeStore.for_repository(repository.root).root
        self.inbox = LocalContractInbox(root)
        self.consumption = ConsumptionStore(root)
        self.repository = repository
        self.execution_lock_active = execution_lock_active or self._execution_lock_active
        self.writer = writer or ArchitectContractWriter(repository)
        self.control_plane = control_plane or AIDPControlPlane(
            repository, timeout_seconds=timeout_seconds, activity_sink=activity_sink,
        )
        self.publisher = publisher or GitReviewPublisher(repository)
        self.allow_test_failure_retry = allow_test_failure_retry

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
                if isinstance(candidate.contract, (ArchitectTaskContract, ReworkContract))
                if self.repository.accepts_task_id(candidate.contract.task_id)
                if (
                    self.consumption.current(candidate.contract_id)
                    not in {ConsumptionState.BLOCKED, ConsumptionState.REVIEW_PUBLISHED}
                    or self._recovery_is_authorized(candidate)
                )
            )
            if not candidates:
                blocked = tuple(candidate for candidate in items
                                if isinstance(candidate.contract, (ArchitectTaskContract, ReworkContract))
                                and self.repository.accepts_task_id(candidate.contract.task_id)
                                and self.consumption.current(candidate.contract_id) is ConsumptionState.BLOCKED)
                if blocked and self.repository.task_namespace == "infrastructure":
                    candidate = blocked[-1]
                    result = LocalRuntimeStore.for_repository(self.repository.root).latest_execution_result(candidate.contract.task_id)
                    state = result.status.value if result is not None else "BLOCKED"
                    return TriggerResult(
                        TriggerStatus.BLOCKED, candidate.contract_id, ConsumptionState.BLOCKED,
                        failure_reason=f"HUMAN_ACTION_REQUIRED: terminal infrastructure execution {state}",
                    )
                return TriggerResult(TriggerStatus.NO_ACTION, None, None)
            if len(candidates) != 1:
                return TriggerResult(TriggerStatus.BLOCKED, None, None, failure_reason="contract inbox is ambiguous")
            item = candidates[0]
            current = self.consumption.current(item.contract_id)
            recovering = current is ConsumptionState.BLOCKED
            if current in {ConsumptionState.RECEIVED, ConsumptionState.MATERIALIZED, ConsumptionState.EXECUTING}:
                if current is ConsumptionState.EXECUTING and self.execution_lock_active():
                    return TriggerResult(TriggerStatus.BLOCKED, item.contract_id, current, failure_reason="contract execution is still locally active")
                return self._block(
                    item.contract_id, current,
                    f"recovered abandoned {current.value} consumption as terminal BLOCKED",
                )
            if current is not None and not recovering:
                return TriggerResult(TriggerStatus.BLOCKED, item.contract_id, current, failure_reason="contract_id was already consumed")
            if self.execution_lock_active():
                return TriggerResult(TriggerStatus.BLOCKED, item.contract_id, None, failure_reason="local execution lock is active")
            if recovering:
                if not self._recovery_is_authorized(item):
                    return TriggerResult(TriggerStatus.NO_ACTION, None, None)
                typed_authority = self._typed_recovery_authorization(item)
                if typed_authority is not None:
                    LocalRuntimeStore.for_repository(self.repository.root).claim_recovery_authorization(
                        typed_authority.authorization_id, typed_authority.failed_execution_id,
                    )
                self.consumption.append(
                    item.contract_id, ConsumptionState.RECOVERY_AUTHORIZED,
                    "one bounded infrastructure recovery authorized",
                )
                lifecycle_state = ConsumptionState.RECOVERY_AUTHORIZED
            else:
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
            original_changed_reader = None
            if recovering and hasattr(self.control_plane, "worktree_changed_files"):
                original_changed_reader = self.control_plane.worktree_changed_files
                self.control_plane.worktree_changed_files = lambda: ()
            decision = self.control_plane.decide()
            if decision.action is not ControlPlaneAction.EXECUTE:
                return self._block(item.contract_id, ConsumptionState.MATERIALIZED, f"control plane decided {decision.action.value}", writer_result)
            execution_state = ConsumptionState.RECOVERY_EXECUTING if recovering else ConsumptionState.EXECUTING
            self.consumption.append(item.contract_id, execution_state, "control plane authorized execution")
            lifecycle_state = execution_state
            runner = getattr(self.control_plane, "runner", None)
            if runner is not None and hasattr(runner, "authorize_contract_context"):
                runner.authorize_contract_context(
                    item.contract_id, attempt_ordinal=1, retry_budget=0,
                    allowed_scope=(item.contract.allowed_rework_scope if isinstance(item.contract, ReworkContract) else None),
                )
            control_result = self.control_plane.run_once()
            if original_changed_reader is not None:
                self.control_plane.worktree_changed_files = original_changed_reader
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
        finally:
            if 'original_changed_reader' in locals() and original_changed_reader is not None:
                self.control_plane.worktree_changed_files = original_changed_reader

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

    def _recovery_is_authorized(self, item: ContractInboxItem) -> bool:
        return bool(
            self._typed_recovery_authorization(item)
            or self._test_failure_retry_is_authorized(item)
            or self._abandoned_rework_recovery_is_authorized(item)
            or self._rework_test_failure_retry_is_authorized(item)
        )

    def _typed_recovery_authorization(
        self, item: ContractInboxItem,
    ) -> RecoveryAuthorizationV1 | LegacyRecoveryAuthorizationV1 | None:
        if not self.allow_test_failure_retry or self.repository.task_namespace != "infrastructure":
            return None
        try:
            events = self.consumption.events(item.contract_id)
            if (not events or events[-1].state is not ConsumptionState.BLOCKED
                    or any(event.state is ConsumptionState.RECOVERY_AUTHORIZED for event in events)):
                return None
            runtime = LocalRuntimeStore.for_repository(self.repository.root)
            result = runtime.latest_execution_result(item.contract.task_id)
            decision = self.repository.inspect()
            changed = GitInspector(self.repository.root).changed_files()
            digest = GitInspector(self.repository.root).residual_digest()
            if result is None or not changed:
                return None
            matches: list[RecoveryAuthorizationV1 | LegacyRecoveryAuthorizationV1] = []
            for authority in runtime.recovery_authorizations():
                common = (
                    authority.task_id == item.contract.task_id
                    and authority.failed_execution_id == result.execution_id
                    and authority.expected_head == item.contract.expected_head == decision.commit
                    and authority.start_head == result.start_commit
                    and authority.authorizer_identity == item.contract_id
                    and authority.retry_budget == 1
                    and decision.task_id == item.contract.task_id
                    and not runtime.recovery_authorization_claimed(authority.authorization_id)
                )
                if not common:
                    continue
                if isinstance(authority, RecoveryAuthorizationV1):
                    if (
                        authority.terminal_status is result.status
                        and authority.failure_classification == result.failure_reason
                        and authority.residual_paths == changed == result.changed_files
                        and authority.residual_digest == digest == result.residual_digest
                        and authority.authorizing_evidence_id == canonical_digest(result)
                    ):
                        matches.append(authority)
                    continue
                if not isinstance(item.contract, ReworkContract):
                    continue
                attempt = runtime.execution_attempt(result.execution_id)
                heartbeat = runtime.execution_heartbeat(result.execution_id)
                if (
                    result.status is ExecutionStatus.ERROR
                    and result.failure_reason == "execution heartbeat persistence failed"
                    and result.resulting_commit is None
                    and result.changed_files == ()
                    and result.validation_results == ()
                    and result.scope_compliance is ScopeCompliance.NOT_EVALUATED
                    and result.residual_digest is None
                    and result.process_identity is None
                    and result.process_termination_confirmed is None
                    and authority.terminal_result_digest == canonical_digest(result)
                    and attempt.execution_id == result.execution_id
                    and attempt.task_id == result.task_id
                    and attempt.contract_id == item.contract_id
                    and attempt.expected_head == authority.expected_head
                    and authority.execution_attempt_digest == canonical_digest(attempt)
                    and heartbeat is not None
                    and heartbeat.execution_id == result.execution_id
                    and authority.latest_heartbeat_digest == heartbeat.heartbeat_digest
                    and authority.residual_paths == changed
                    and authority.residual_digest == digest
                    and authority.prior_rework_authority_id != authority.authorization_id
                    and runtime.rework_contract_id(
                        item.contract.task_id, item.contract.review_iteration,
                        expected_head=item.contract.expected_head,
                    ) == item.contract_id
                    and item.contract.canonical_id(authority.prior_rework_authority_id) == item.contract_id
                    and changed == tuple(sorted(item.contract.allowed_rework_scope))
                ):
                    matches.append(authority)
            return matches[0] if len(matches) == 1 else None
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
            return None

    def _abandoned_rework_recovery_is_authorized(self, item: ContractInboxItem) -> bool:
        if (not self.allow_test_failure_retry or self.repository.task_namespace != "infrastructure"
                or not isinstance(item.contract, ReworkContract)):
            return False
        expected = {
            "contract_id": "4ece65a0224b1a3978b266d6663b10eeef27479180f7c9b4300599414dc684f8",
            "execution_id": "381f8c6d-8db2-447d-bfc3-da6b61ddad75",
            "head": "7d2751ea9ca5a103649e3248ad7487278dc3c3bd",
            "architect_result": "fadfb7535c9ced7b5ca68970557bffbf23bc9d7ed9f87de8cafabb3712f7a40c",
            "residual_digest": "ecfe59b8f3efc7e656528829a5b08a9d946b7fefaaeaf17c52c794a4405e5efa",
        }
        try:
            events = self.consumption.events(item.contract_id)
            if (item.contract_id != expected["contract_id"] or not events
                    or events[-1].state is not ConsumptionState.BLOCKED
                    or any(event.state is ConsumptionState.RECOVERY_AUTHORIZED for event in events)):
                return False
            decision = self.repository.inspect()
            if (decision.task_id != item.contract.task_id or decision.state is not AIDPState.REWORK_REQUIRED
                    or decision.commit != expected["head"] or item.contract.expected_head != expected["head"]):
                return False
            result = LocalRuntimeStore.for_repository(self.repository.root).latest_execution_result(item.contract.task_id)
            if (result is None or result.execution_id != expected["execution_id"]
                    or result.start_commit != expected["head"]
                    or result.status not in {ExecutionStatus.ERROR, ExecutionStatus.TIMED_OUT, ExecutionStatus.ABANDONED_DIRTY_WORKTREE}
                    or result.failure_reason != "Codex process timed out"):
                return False
            changed = GitInspector(self.repository.root).changed_files()
            if changed != tuple(sorted(item.contract.allowed_rework_scope)):
                return False
            payload = subprocess.check_output(
                ("git", "diff", "--binary", "--no-ext-diff", "--", *changed), cwd=self.repository.root,
            )
            if hashlib.sha256(payload).hexdigest() != expected["residual_digest"]:
                return False
            runtime = LocalRuntimeStore.for_repository(self.repository.root).root
            if not (runtime / "architect-review-results" / f"{expected['architect_result']}.json").is_file():
                return False
            request = self.repository.build_execution_request(item.contract.task_id, rework_count=item.contract.review_iteration)
            return self.repository.validate_scope(request, changed) is ScopeCompliance.COMPLIANT
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
            return False

    def _test_failure_retry_is_authorized(self, item: ContractInboxItem) -> bool:
        if (
            not self.allow_test_failure_retry
            or self.repository.task_namespace != "infrastructure"
            or not isinstance(item.contract, ArchitectTaskContract)
        ):
            return False
        try:
            events = self.consumption.events(item.contract_id)
            if (
                not events or events[-1].state is not ConsumptionState.BLOCKED
                or events[-1].reason != "execution is not review-ready"
                or any(event.state is ConsumptionState.RECOVERY_AUTHORIZED for event in events)
            ):
                return False
            decision = self.repository.inspect()
            contract = item.contract
            if decision.state is not AIDPState.READY_FOR_CODEX or decision.task_id != contract.task_id:
                return False
            task_path = self.repository.ai_root / "tasks" / "ready" / f"{contract.task_id}.md"
            metadata = self.repository.parse_metadata(task_path)
            if metadata is None or (
                metadata.task_id != contract.task_id
                or metadata.phase != contract.phase
                or metadata.allowed_scope != contract.allowed_scope
                or metadata.prohibited_actions != contract.prohibited_actions
                or metadata.validation_requirements != contract.validation_requirements
                or metadata.product_owner_gate != contract.product_owner_gate
            ):
                return False
            parent = self.repository._git("rev-parse", f"{decision.commit}^")
            materialized = tuple(sorted(filter(None, self.repository._git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", decision.commit,
            ).splitlines())))
            expected_materialized = tuple(sorted((
                f".ai/tasks/ready/{contract.task_id}.md",
                ".ai/handoff/TO-CODEX.md",
                ".ai/handoff/TO-ARCHITECT.md",
            )))
            if parent != contract.expected_head or materialized != expected_materialized:
                return False
            changed = GitInspector(self.repository.root).changed_files()
            if self.repository.validate_scope(
                self.repository.build_execution_request(contract.task_id), changed,
            ) is not ScopeCompliance.COMPLIANT:
                return False
            result = LocalRuntimeStore.for_repository(self.repository.root).latest_execution_result(contract.task_id)
            return bool(
                result is not None
                and result.status is ExecutionStatus.TEST_FAILED
                and result.scope_compliance is ScopeCompliance.COMPLIANT
                and result.resulting_commit == decision.commit
                and tuple(validation.name for validation in result.validation_results)
                == contract.validation_requirements
                and any(not validation.passed for validation in result.validation_results)
                and self.repository.scope_compliance_for_paths(
                    contract.allowed_scope, contract.prohibited_actions, result.changed_files,
                ) is ScopeCompliance.COMPLIANT
            )
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
            return False

    def _rework_test_failure_retry_is_authorized(self, item: ContractInboxItem) -> bool:
        if (
            not self.allow_test_failure_retry
            or self.repository.task_namespace != "infrastructure"
            or not isinstance(item.contract, ReworkContract)
        ):
            return False
        try:
            events = self.consumption.events(item.contract_id)
            if (
                not events or events[-1].state is not ConsumptionState.BLOCKED
                or any(event.state is ConsumptionState.RECOVERY_AUTHORIZED for event in events)
            ):
                return False
            contract = item.contract
            decision = self.repository.inspect()
            if (
                decision.state is not AIDPState.REWORK_REQUIRED
                or decision.task_id != contract.task_id
                or decision.commit != contract.expected_head
            ):
                return False
            result = LocalRuntimeStore.for_repository(self.repository.root).latest_execution_result(contract.task_id)
            if (
                result is None
                or result.status is not ExecutionStatus.TEST_FAILED
                or result.scope_compliance is not ScopeCompliance.COMPLIANT
                or result.start_commit != contract.expected_head
                or result.resulting_commit != decision.commit
                or tuple(validation.name for validation in result.validation_results) != contract.required_validations
                or not any(not validation.passed for validation in result.validation_results)
            ):
                return False
            changed = GitInspector(self.repository.root).changed_files()
            if changed != tuple(sorted(result.changed_files)):
                return False
            request = self.repository.build_execution_request(
                contract.task_id, rework_count=contract.review_iteration,
            )
            return self.repository.validate_scope(request, changed) is ScopeCompliance.COMPLIANT
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
            return False


def serialize_review_envelope(value: ReviewEnvelope) -> str:
    return _json({"architect_review_envelope": value})


def serialize_contract_inbox_item(value: ContractInboxItem) -> str:
    contract_type = (
        "architect_task" if isinstance(value.contract, ArchitectTaskContract)
        else "rework" if isinstance(value.contract, ReworkContract)
        else "architect_review_recovery" if isinstance(value.contract, ArchitectReviewRecoveryAuthorityV1)
        else "product_owner_gate_dependency"
    )
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


def _architect_review_recovery_authority(v: dict[str, object]) -> ArchitectReviewRecoveryAuthorityV1:
    expected = {
        "schema_version", "authority_id", "task_id", "authorizing_review_result_id",
        "authorizing_review_result_digest", "legacy_rework_contract_id", "legacy_rework_contract_digest",
        "legacy_authorizing_lineage_missing", "execution_id", "execution_start_head",
        "implementation_commit", "lifecycle_projection_commit", "changed_files", "scope_compliance",
        "validator_evidence_digest", "execution_result_digest", "review_envelope_id",
        "review_envelope_digest", "repository_id", "branch", "expected_lifecycle_state",
        "issued_by", "issued_at", "expires_at",
    }
    if set(v) != expected: raise ValueError("invalid ArchitectReviewRecoveryAuthorityV1 schema")
    missing = v.get("legacy_authorizing_lineage_missing")
    if not isinstance(missing, bool): raise ValueError("legacy_authorizing_lineage_missing must be boolean")
    return ArchitectReviewRecoveryAuthorityV1(
        schema_version=_string(v, "schema_version"), authority_id=_string(v, "authority_id"),
        task_id=_string(v, "task_id"), authorizing_review_result_id=_string(v, "authorizing_review_result_id"),
        authorizing_review_result_digest=_string(v, "authorizing_review_result_digest"),
        legacy_rework_contract_id=_string(v, "legacy_rework_contract_id"),
        legacy_rework_contract_digest=_string(v, "legacy_rework_contract_digest"),
        legacy_authorizing_lineage_missing=missing, execution_id=_string(v, "execution_id"),
        execution_start_head=_string(v, "execution_start_head"), implementation_commit=_string(v, "implementation_commit"),
        lifecycle_projection_commit=_string(v, "lifecycle_projection_commit"), changed_files=_strings(v, "changed_files"),
        scope_compliance=ScopeCompliance(_string(v, "scope_compliance")),
        validator_evidence_digest=_string(v, "validator_evidence_digest"),
        execution_result_digest=_string(v, "execution_result_digest"), review_envelope_id=_string(v, "review_envelope_id"),
        review_envelope_digest=_string(v, "review_envelope_digest"), repository_id=_string(v, "repository_id"),
        branch=_string(v, "branch"), expected_lifecycle_state=AIDPState(_string(v, "expected_lifecycle_state")),
        issued_by=_string(v, "issued_by"), issued_at=datetime.fromisoformat(_string(v, "issued_at")),
        expires_at=datetime.fromisoformat(_string(v, "expires_at")),
    )


def _product_owner_gate_dependency_authority(v: dict[str, object]) -> ProductOwnerGateDependencyAuthorityV1:
    expected = {
        "schema_version", "authority_id", "parent_task_id", "dependency_id", "purpose",
        "repository_id", "git_common_id", "repository_remote_id", "branch", "expected_head", "allowed_scope", "prohibited_actions",
        "validation_requirements", "acceptance_criteria", "issued_by", "issued_at", "expires_at",
    }
    if set(v) != expected:
        raise ValueError("invalid ProductOwnerGateDependencyAuthorityV1 schema")
    return ProductOwnerGateDependencyAuthorityV1(
        schema_version=_string(v, "schema_version"), authority_id=_string(v, "authority_id"),
        parent_task_id=_string(v, "parent_task_id"), dependency_id=_string(v, "dependency_id"),
        purpose=_string(v, "purpose"), repository_id=_string(v, "repository_id"),
        git_common_id=_string(v, "git_common_id"), repository_remote_id=_string(v, "repository_remote_id"),
        branch=_string(v, "branch"), expected_head=_string(v, "expected_head"),
        allowed_scope=_strings(v, "allowed_scope"), prohibited_actions=_strings(v, "prohibited_actions"),
        validation_requirements=_strings(v, "validation_requirements"),
        acceptance_criteria=_strings(v, "acceptance_criteria"), issued_by=_string(v, "issued_by"),
        issued_at=datetime.fromisoformat(_string(v, "issued_at")),
        expires_at=datetime.fromisoformat(_string(v, "expires_at")),
    )


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


def _reject_duplicate_json_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON field")
        value[key] = item
    return value


def _json(value: object) -> str:
    def default(item: object) -> object:
        if hasattr(item, "__dataclass_fields__"): return asdict(item)
        if isinstance(item, datetime): return item.isoformat()
        if isinstance(item, Enum): return item.value
        raise TypeError(type(item).__name__)
    return json.dumps(value, default=default, sort_keys=True, separators=(",", ":"))
