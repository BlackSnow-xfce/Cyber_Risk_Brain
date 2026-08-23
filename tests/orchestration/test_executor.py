from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    CodexExecutionRequest,
    ExecutionStatus,
    ScopeCompliance,
    ValidationResult,
    utc_now,
)
from aidp_orchestration.executor import (
    CodexExecutionService,
    ExecutionLock,
    ProcessOutcome,
    serialize_execution_result,
)


class FakeGit:
    def __init__(self, *, branch: str = "main", head: str = "base", clean: bool = True, changed: tuple[str, ...] = ()):
        self.current_branch = branch
        self.current_head = head
        self.clean = clean
        self.changed = changed

    def branch(self) -> str:
        return self.current_branch

    def head(self) -> str:
        return self.current_head

    def is_clean(self) -> bool:
        return self.clean

    def changed_files(self) -> tuple[str, ...]:
        return self.changed


class FakeRunner:
    def __init__(self, outcomes: list[ProcessOutcome]):
        self.outcomes = outcomes
        self.calls: list[tuple[str, ...]] = []

    def run(self, args, *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        self.calls.append(tuple(args))
        return self.outcomes.pop(0)


def request(tmp_path: Path, *, validations: tuple[str, ...] = ("pytest",), scope: tuple[str, ...] = ("aidp_orchestration/**",)) -> CodexExecutionRequest:
    task = tmp_path / "TASK-9000.md"
    task.write_text("task", encoding="utf-8")
    return CodexExecutionRequest(
        "TASK-9000", task, str(tmp_path), "main", "base", "base", "implementation",
        scope, (".git/**",), validations, utc_now(), "execution-1",
    )


def success_runner() -> FakeRunner:
    return FakeRunner([ProcessOutcome(0, '{"type":"completed"}\n', ""), ProcessOutcome(0, "", "")])


def service(tmp_path: Path, runner: FakeRunner, git: FakeGit | None = None) -> CodexExecutionService:
    return CodexExecutionService(
        runner=runner,
        git=git or FakeGit(),
        lock=ExecutionLock(tmp_path / "execution.lock"),
    )


def test_valid_execution_runs_bound_codex_request_and_validators(tmp_path: Path) -> None:
    runner = success_runner()
    result = service(tmp_path, runner).execute(request(tmp_path))
    assert result.status is ExecutionStatus.SUCCESS
    assert result.scope_compliance is ScopeCompliance.COMPLIANT
    assert result.is_review_ready
    assert runner.calls[0][:3] == ("codex", "exec", "--json")
    assert "task_id=TASK-9000" in runner.calls[0][-1]
    assert "execution_id=execution-1" in runner.calls[0][-1]


@pytest.mark.parametrize(
    ("git", "expected"),
    ((FakeGit(branch="other"), ExecutionStatus.BLOCKED), (FakeGit(head="different"), ExecutionStatus.STALE_EXECUTION), (FakeGit(clean=False), ExecutionStatus.BLOCKED)),
)
def test_preflight_fail_closed(tmp_path: Path, git: FakeGit, expected: ExecutionStatus) -> None:
    runner = FakeRunner([])
    result = service(tmp_path, runner, git).execute(request(tmp_path))
    assert result.status is expected
    assert runner.calls == []


def test_repository_mismatch_blocks_before_process(tmp_path: Path) -> None:
    request_root = tmp_path / "request-root"
    request_root.mkdir()
    req = request(request_root)
    runner = FakeRunner([])
    result = CodexExecutionService(runner=runner, git=FakeGit(), repository_root=tmp_path).execute(req)
    assert result.status is ExecutionStatus.BLOCKED
    assert runner.calls == []


def test_parallel_lock_blocks_second_execution(tmp_path: Path) -> None:
    lock = ExecutionLock(tmp_path / "execution.lock")
    first = request(tmp_path)
    lock.acquire(first)
    try:
        result = CodexExecutionService(runner=FakeRunner([]), git=FakeGit(), lock=lock).execute(first)
        assert result.status is ExecutionStatus.BLOCKED
    finally:
        lock.release()


@pytest.mark.parametrize(
    ("outcome", "expected"),
    ((ProcessOutcome(7, "", "failure"), ExecutionStatus.ERROR), (ProcessOutcome(None, "", "", timed_out=True), ExecutionStatus.ERROR), (ProcessOutcome(0, "not json", ""), ExecutionStatus.ERROR)),
)
def test_process_failures_are_not_success(tmp_path: Path, outcome: ProcessOutcome, expected: ExecutionStatus) -> None:
    result = service(tmp_path, FakeRunner([outcome])).execute(request(tmp_path))
    assert result.status is expected
    assert not result.is_review_ready


def test_scope_violation_is_fail_closed(tmp_path: Path) -> None:
    result = service(tmp_path, success_runner(), FakeGit(changed=("product.py",))).execute(request(tmp_path))
    assert result.status is ExecutionStatus.SCOPE_VIOLATION
    assert result.scope_compliance is ScopeCompliance.VIOLATION


def test_unknown_validator_blocks_before_process(tmp_path: Path) -> None:
    runner = FakeRunner([])
    result = service(tmp_path, runner).execute(request(tmp_path, validations=("arbitrary shell",)))
    assert result.status is ExecutionStatus.BLOCKED
    assert runner.calls == []


def test_validator_failure_is_test_failed(tmp_path: Path) -> None:
    runner = FakeRunner([ProcessOutcome(0, '{"type":"completed"}\n', ""), ProcessOutcome(1, "", "failed")])
    result = service(tmp_path, runner).execute(request(tmp_path))
    assert result.status is ExecutionStatus.TEST_FAILED
    assert result.validation_results == (ValidationResult("pytest", False, "exit_code=1"),)


def test_result_serialization_is_stable_and_excludes_process_output(tmp_path: Path) -> None:
    result = service(tmp_path, success_runner()).execute(request(tmp_path))
    payload = json.loads(serialize_execution_result(result))
    assert payload["codex_execution_result"]["execution_id"] == "execution-1"
    assert payload["codex_execution_result"]["status"] == "SUCCESS"
    assert "completed" not in serialize_execution_result(result)


def test_lock_is_released_after_process_error(tmp_path: Path) -> None:
    lock_path = tmp_path / "execution.lock"
    result = CodexExecutionService(runner=FakeRunner([ProcessOutcome(3, "", "")]), git=FakeGit(), lock=ExecutionLock(lock_path)).execute(request(tmp_path))
    assert result.status is ExecutionStatus.ERROR
    assert not lock_path.exists()
