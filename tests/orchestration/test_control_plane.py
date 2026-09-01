from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    AIDPState,
    ArchitectInboxEntry,
    ControlPlaneAction,
    CodexExecutionResult,
    ExecutionStatus,
    ReworkContract,
    RunnerResult,
    RunnerStatus,
    ScopeCompliance,
    ValidationResult,
    utc_now,
)
from aidp_orchestration.control_plane import (
    AIDPControlPlane,
    LocalArchitectInbox,
    LocalReworkContractStore,
    serialize_architect_inbox_entry,
    serialize_control_plane_decision,
    serialize_control_plane_result,
    serialize_rework_contract,
)
from aidp_orchestration.repository import AIDPRepository


class StaticContractStore:
    def __init__(self, contract: ReworkContract | None = None):
        self.contract = contract

    def load(self, task_id: str) -> ReworkContract | None:
        return self.contract


class RecordingRunner:
    def __init__(self, result: RunnerResult | None = None):
        self.result = result
        self.calls = 0

    def run_ready(self) -> RunnerResult:
        self.calls += 1
        if self.result is None:
            raise AssertionError("runner result was not configured")
        return self.result


class FailingInbox:
    def persist(self, entry: ArchitectInboxEntry) -> Path:
        raise RuntimeError("persistence unavailable")


def git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def repository(tmp_path: Path, state: AIDPState) -> AIDPRepository:
    ready = tmp_path / ".ai" / "tasks" / "ready"
    review = tmp_path / ".ai" / "tasks" / "review"
    handoff = tmp_path / ".ai" / "handoff"
    ready.mkdir(parents=True)
    review.mkdir(parents=True)
    handoff.mkdir(parents=True)
    task_id = "TASK-9000"
    task_text = (
        "---\n"
        f"task_id: {task_id}\n"
        "phase: implementation\n"
        "allowed_scope: aidp_orchestration/**, tests/orchestration/**\n"
        "prohibited_actions: .ai/**, frontend/**\n"
        "validation_requirements: pytest, git diff --check\n"
        "product_owner_gate: false\n"
        "---\n"
    )
    if state in {AIDPState.READY_FOR_CODEX, AIDPState.BLOCKED}:
        (ready / f"{task_id}.md").write_text(task_text, encoding="utf-8")
    if state is AIDPState.BLOCKED:
        (ready / "TASK-9001.md").write_text(task_text.replace(task_id, "TASK-9001"), encoding="utf-8")
    if state in {AIDPState.READY_FOR_ARCHITECT, AIDPState.REWORK_REQUIRED, AIDPState.WAITING_FOR_PRODUCT_OWNER}:
        suffix = ""
        if state is AIDPState.REWORK_REQUIRED:
            suffix = "Status: REVIEW / REWORK REQUIRED\n"
        if state is AIDPState.WAITING_FOR_PRODUCT_OWNER:
            task_text = task_text.replace("product_owner_gate: false", "product_owner_gate: true")
            suffix = "Status: ARCHITECT_APPROVED\n"
        (review / f"{task_id}.md").write_text(task_text + suffix, encoding="utf-8")
    active = state is not AIDPState.WAITING
    review_state = state in {AIDPState.READY_FOR_ARCHITECT, AIDPState.REWORK_REQUIRED, AIDPState.WAITING_FOR_PRODUCT_OWNER}
    (handoff / "TO-CODEX.md").write_text(
        f"Status: {'WAITING' if review_state else 'OPEN' if active else 'WAITING'}\n"
        f"Current AIDP Task: {task_id if active else 'NONE'}\n",
        encoding="utf-8",
    )
    (handoff / "TO-ARCHITECT.md").write_text(
        f"Status: {'OPEN' if review_state else 'WAITING'}\nTask: {task_id if active else 'NONE'}\n",
        encoding="utf-8",
    )
    git(tmp_path, "init", "-q", "-b", "control-plane-test")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@localhost")
    git(tmp_path, "add", ".ai")
    git(tmp_path, "commit", "-q", "-m", "fixture")
    return AIDPRepository(tmp_path)


def contract(repo: AIDPRepository, **changes) -> ReworkContract:
    value = ReworkContract(
        "TASK-9000",
        1,
        repo.head,
        ("aidp_orchestration/**",),
        ("Correct the reviewed implementation defect",),
        ("pytest", "git diff --check"),
        utc_now(),
    )
    return replace(value, **changes)


def successful_runner_result(repo: AIDPRepository, *, status: ExecutionStatus = ExecutionStatus.SUCCESS) -> RunnerResult:
    scope = {
        ExecutionStatus.SUCCESS: ScopeCompliance.COMPLIANT,
        ExecutionStatus.SCOPE_VIOLATION: ScopeCompliance.VIOLATION,
    }.get(status, ScopeCompliance.NOT_EVALUATED)
    execution = CodexExecutionResult(
        "execution-1",
        "TASK-9000",
        repo.head,
        repo.head,
        ("aidp_orchestration/control_plane.py",),
        (ValidationResult("pytest", status is ExecutionStatus.SUCCESS, "passed"),),
        status,
        None if status is ExecutionStatus.SUCCESS else "execution requires Architect review",
        scope,
    )
    intended = AIDPState.READY_FOR_ARCHITECT if status is ExecutionStatus.SUCCESS else AIDPState.BLOCKED
    return RunnerResult(RunnerStatus.EXECUTED, "TASK-9000", AIDPState.READY_FOR_CODEX, intended, "executed", execution)


def plane(repo: AIDPRepository, runner: RecordingRunner | None = None, contract_value: ReworkContract | None = None, inbox=None) -> AIDPControlPlane:
    return AIDPControlPlane(
        repo,
        runner=runner or RecordingRunner(),
        contract_store=StaticContractStore(contract_value),
        architect_inbox=inbox or LocalArchitectInbox(repo.root / "runtime"),
        is_worktree_clean=lambda: True,
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        (AIDPState.WAITING, ControlPlaneAction.NO_ACTION),
        (AIDPState.READY_FOR_ARCHITECT, ControlPlaneAction.READY_FOR_ARCHITECT),
        (AIDPState.WAITING_FOR_PRODUCT_OWNER, ControlPlaneAction.WAITING_FOR_PRODUCT_OWNER),
        (AIDPState.BLOCKED, ControlPlaneAction.BLOCKED),
    ),
)
def test_non_execution_states_are_mapped_without_runner(tmp_path: Path, state: AIDPState, expected: ControlPlaneAction) -> None:
    repo = repository(tmp_path, state)
    runner = RecordingRunner()
    result = plane(repo, runner).run_once()
    assert result.final_action is expected
    assert runner.calls == 0


def test_ready_for_codex_executes_through_existing_runner_once(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    runner = RecordingRunner(successful_runner_result(repo))
    result = plane(repo, runner).run_once()
    assert result.decision.action is ControlPlaneAction.EXECUTE
    assert result.final_action is ControlPlaneAction.READY_FOR_ARCHITECT
    assert runner.calls == 1


def test_dirty_worktree_blocks_before_runner(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    runner = RecordingRunner(successful_runner_result(repo))
    control_plane = AIDPControlPlane(
        repo,
        runner=runner,
        contract_store=StaticContractStore(),
        architect_inbox=LocalArchitectInbox(tmp_path / "runtime"),
        is_worktree_clean=lambda: False,
    )
    assert control_plane.run_once().final_action is ControlPlaneAction.BLOCKED
    assert runner.calls == 0


@pytest.mark.parametrize(
    ("paths", "expected"),
    (
        (("aidp_orchestration/control_plane.py",), ControlPlaneAction.EXECUTE),
        (("tests/orchestration/test_control_plane.py",), ControlPlaneAction.EXECUTE),
        (("aidp_orchestration/control_plane.py", "frontend/unauthorized.tsx"), ControlPlaneAction.BLOCKED),
        (("frontend/unauthorized.tsx",), ControlPlaneAction.BLOCKED),
    ),
)
def test_ready_dirty_scope_policy_matches_writer(
    tmp_path: Path,
    paths: tuple[str, ...],
    expected: ControlPlaneAction,
) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    control_plane = AIDPControlPlane(
        repo,
        runner=RecordingRunner(successful_runner_result(repo)),
        contract_store=StaticContractStore(),
        architect_inbox=LocalArchitectInbox(tmp_path / "runtime"),
        worktree_changed_files=lambda: paths,
    )
    assert control_plane.decide().action is expected


def test_valid_rework_contract_admits_existing_runner(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.REWORK_REQUIRED)
    runner_result = successful_runner_result(repo)
    runner_result = replace(runner_result, current_state=AIDPState.REWORK_REQUIRED)
    runner = RecordingRunner(runner_result)
    result = plane(repo, runner, contract(repo)).run_once()
    assert result.decision.action is ControlPlaneAction.EXECUTE
    assert runner.calls == 1


def test_successful_execution_persists_architect_inbox(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    runner = RecordingRunner(successful_runner_result(repo))
    result = plane(repo, runner).run_once()
    assert result.architect_inbox_path is not None
    payload = json.loads(Path(result.architect_inbox_path).read_text(encoding="utf-8"))["architect_inbox_entry"]
    assert payload["execution_id"] == "execution-1"
    assert payload["execution_status"] == "SUCCESS"
    assert payload["intended_next_state"] == "READY_FOR_ARCHITECT"


def test_inbox_persistence_failure_blocks_without_approval_semantics(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    runner = RecordingRunner(successful_runner_result(repo))
    result = plane(repo, runner, inbox=FailingInbox()).run_once()
    assert result.final_action is ControlPlaneAction.BLOCKED
    assert result.architect_inbox_path is None
    assert result.failure_reason == "architect inbox persistence failed: RuntimeError"


@pytest.mark.parametrize("execution_status", (ExecutionStatus.SCOPE_VIOLATION, ExecutionStatus.ERROR))
def test_failed_execution_is_reviewable_but_never_approved(tmp_path: Path, execution_status: ExecutionStatus) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    runner = RecordingRunner(successful_runner_result(repo, status=execution_status))
    serialized = serialize_control_plane_result(plane(repo, runner).run_once())
    payload = json.loads(serialized)["control_plane_result"]
    assert payload["final_action"] == "BLOCKED"
    assert payload["architect_inbox_entry"]["execution_status"] == execution_status.value
    assert "APPROVED" not in serialized
    assert '"DONE"' not in serialized


@pytest.mark.parametrize(
    ("change", "reason"),
    (
        ({"task_id": "TASK-9999"}, "task_id"),
        ({"expected_head": "stale"}, "stale"),
        ({"allowed_rework_scope": ("product/**",)}, "widens"),
        ({"required_validations": ("unknown validator",)}, "unknown"),
    ),
)
def test_invalid_rework_contract_blocks(tmp_path: Path, change: dict[str, object], reason: str) -> None:
    repo = repository(tmp_path, AIDPState.REWORK_REQUIRED)
    decision = plane(repo, contract_value=contract(repo, **change)).decide()
    assert decision.action is ControlPlaneAction.BLOCKED
    assert reason in decision.reason


def test_missing_rework_contract_blocks(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.REWORK_REQUIRED)
    assert plane(repo).decide().action is ControlPlaneAction.BLOCKED


@pytest.mark.parametrize(
    "change",
    (
        {"review_iteration": 0},
        {"expected_head": ""},
        {"allowed_rework_scope": ()},
        {"findings": ()},
        {"required_validations": ()},
    ),
)
def test_rework_contract_validation_is_fail_closed(tmp_path: Path, change: dict[str, object]) -> None:
    repo = repository(tmp_path, AIDPState.REWORK_REQUIRED)
    with pytest.raises(ValueError):
        contract(repo, **change)


def test_control_plane_does_not_mutate_aidp_files(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.READY_FOR_CODEX)
    before = {path: path.read_bytes() for path in repo.ai_root.rglob("*") if path.is_file()}
    plane(repo, RecordingRunner(successful_runner_result(repo))).run_once()
    assert before == {path: path.read_bytes() for path in repo.ai_root.rglob("*") if path.is_file()}


def test_serialization_envelopes_are_stable_and_contract_store_round_trips(tmp_path: Path) -> None:
    repo = repository(tmp_path, AIDPState.REWORK_REQUIRED)
    rework = contract(repo)
    contract_path = tmp_path / "runtime" / "rework-contracts" / "TASK-9000.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(serialize_rework_contract(rework), encoding="utf-8")
    loaded = LocalReworkContractStore(tmp_path / "runtime").load("TASK-9000")
    assert loaded == rework
    decision = plane(repo, contract_value=rework).decide()
    assert json.loads(serialize_control_plane_decision(decision))["control_plane_decision"]["action"] == "EXECUTE"
    entry = ArchitectInboxEntry(
        "TASK-9000", "execution-1", AIDPState.REWORK_REQUIRED, AIDPState.READY_FOR_ARCHITECT,
        ExecutionStatus.SUCCESS, ("aidp_orchestration/control_plane.py",), ScopeCompliance.COMPLIANT,
        (ValidationResult("pytest", True),), None, repo.branch, repo.head, repo.head, utc_now(),
    )
    assert json.loads(serialize_architect_inbox_entry(entry))["architect_inbox_entry"]["task_id"] == "TASK-9000"


def test_iteration_safe_rework_store_selects_latest_without_overwrite(tmp_path: Path) -> None:
    from aidp_orchestration.runtime import LocalRuntimeStore

    root = tmp_path / "runtime"
    first = ReworkContract("TASK-9000", 1, "a", ("x.py",), ("f1",), ("pytest",), utc_now())
    second = ReworkContract("TASK-9000", 2, "b", ("x.py",), ("f2",), ("pytest",), utc_now())
    first_path = LocalRuntimeStore(root).persist_rework_contract("first", first)
    second_path = LocalRuntimeStore(root).persist_rework_contract("second", second)
    assert first_path != second_path and first_path.exists() and second_path.exists()
    assert LocalReworkContractStore(root).load("TASK-9000") == second
