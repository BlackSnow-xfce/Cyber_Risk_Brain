from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    AIDPState,
    CodexExecutionRequest,
    CodexExecutionResult,
    ExecutionStatus,
    OrchestrationDecision,
    ReworkContract,
    RunnerStatus,
    ScopeCompliance,
    ValidationResult,
    utc_now,
)
from aidp_orchestration.runner import AIDPRunner, serialize_runner_result
from aidp_orchestration.runtime import LocalRuntimeStore


class FakeRepository:
    def __init__(self, root: Path, state: AIDPState, *, next_state: AIDPState | None = None):
        self.root = root
        self.state = state
        self.next_state = next_state
        self.requests: list[tuple[str, int]] = []

    def inspect(self) -> OrchestrationDecision:
        task_id = None if self.state is AIDPState.WAITING else "TASK-9000"
        return OrchestrationDecision(task_id, self.state, self.next_state, "main", "base", (), utc_now())

    def build_execution_request(
        self,
        task_id: str,
        *,
        rework_count: int = 0,
        rework_contract: ReworkContract | None = None,
    ) -> CodexExecutionRequest:
        self.requests.append((task_id, rework_count))
        task_path = self.root / ".ai" / "tasks" / "ready" / f"{task_id}.md"
        allowed_scope = (
            rework_contract.allowed_rework_scope
            if rework_contract is not None
            else ("aidp_orchestration/**",)
        )
        validations = (
            rework_contract.required_validations
            if rework_contract is not None
            else ("pytest",)
        )
        expected_head = rework_contract.expected_head if rework_contract is not None else "base"
        return CodexExecutionRequest(
            task_id,
            task_path,
            str(self.root),
            "main",
            "base",
            expected_head,
            "implementation",
            allowed_scope,
            (".ai/tasks/**", ".ai/handoff/**"),
            validations,
            utc_now(),
            "execution-1",
            rework_count,
        )

    def evaluate_result(self, request: CodexExecutionRequest, result: CodexExecutionResult) -> AIDPState:
        if result.is_review_ready:
            return AIDPState.READY_FOR_ARCHITECT
        return AIDPState.BLOCKED


class FakeExecutionService:
    def __init__(self, result: CodexExecutionResult | None = None):
        self.calls: list[CodexExecutionRequest] = []
        self.result = result

    def execute(self, request: CodexExecutionRequest) -> CodexExecutionResult:
        self.calls.append(request)
        return self.result or successful_result(request)


def successful_result(request: CodexExecutionRequest) -> CodexExecutionResult:
    return CodexExecutionResult(
        request.execution_id,
        request.task_id,
        request.expected_head,
        request.expected_head,
        ("aidp_orchestration/runner.py",),
        (ValidationResult("pytest", True, "exit_code=0"),),
        ExecutionStatus.SUCCESS,
        None,
        ScopeCompliance.COMPLIANT,
    )


def make_runner(tmp_path: Path, state: AIDPState, *, next_state: AIDPState | None = None):
    repository = FakeRepository(tmp_path, state, next_state=next_state)
    execution_service = FakeExecutionService()
    store = LocalRuntimeStore(tmp_path / "runtime")
    return AIDPRunner(repository, execution_service=execution_service, runtime_store=store), repository, execution_service, store


def rework_contract(**changes: object) -> ReworkContract:
    values = {
        "task_id": "TASK-9000",
        "review_iteration": 2,
        "expected_head": "base",
        "allowed_rework_scope": ("aidp_orchestration/product_owner_http.py",),
        "findings": ("Fix the active Architect finding",),
        "required_validations": ("git diff --check",),
        "created_at": utc_now(),
    }
    values.update(changes)
    return ReworkContract(**values)


def test_ready_for_codex_starts_exactly_one_execution_and_reports_review_state(tmp_path: Path) -> None:
    runner, repository, service, _ = make_runner(tmp_path, AIDPState.READY_FOR_CODEX, next_state=AIDPState.CODEX_RUNNING)

    result = runner.run_ready()

    assert result.status is RunnerStatus.EXECUTED
    assert result.intended_next_state is AIDPState.READY_FOR_ARCHITECT
    assert len(service.calls) == 1
    assert repository.requests == [("TASK-9000", 0)]
    assert result.execution_result is service.result or result.execution_result is not None


@pytest.mark.parametrize("state", (AIDPState.WAITING, AIDPState.READY_FOR_ARCHITECT))
def test_non_executable_states_return_no_action(tmp_path: Path, state: AIDPState) -> None:
    runner, repository, service, _ = make_runner(tmp_path, state)
    result = runner.run_ready()
    assert result.status is RunnerStatus.NO_ACTION
    assert service.calls == []
    assert repository.requests == []


def test_blocked_starts_nothing(tmp_path: Path) -> None:
    runner, _, service, _ = make_runner(tmp_path, AIDPState.BLOCKED)
    assert runner.run_ready().status is RunnerStatus.BLOCKED
    assert service.calls == []


def test_rework_executes_only_with_explicit_ready_authorization(tmp_path: Path) -> None:
    denied, _, denied_service, _ = make_runner(tmp_path / "denied", AIDPState.REWORK_REQUIRED)
    allowed, repository, allowed_service, _ = make_runner(
        tmp_path / "allowed", AIDPState.REWORK_REQUIRED, next_state=AIDPState.READY_FOR_CODEX
    )

    authority = rework_contract()
    assert denied.run_ready(authority).status is RunnerStatus.NO_ACTION
    assert denied_service.calls == []
    assert allowed.run_ready(authority).status is RunnerStatus.EXECUTED
    assert len(allowed_service.calls) == 1
    assert repository.requests == [("TASK-9000", 1)]
    assert allowed_service.calls[0].allowed_scope == authority.allowed_rework_scope
    assert allowed_service.calls[0].validation_requirements == authority.required_validations


def test_rework_without_contract_authority_fails_closed(tmp_path: Path) -> None:
    runner, repository, service, _ = make_runner(
        tmp_path, AIDPState.REWORK_REQUIRED, next_state=AIDPState.READY_FOR_CODEX,
    )

    result = runner.run_ready()

    assert result.status is RunnerStatus.ERROR
    assert service.calls == []
    assert repository.requests == []


def test_ready_for_codex_does_not_accept_rework_authority(tmp_path: Path) -> None:
    runner, repository, service, _ = make_runner(tmp_path, AIDPState.READY_FOR_CODEX)

    result = runner.run_ready(rework_contract())

    assert result.status is RunnerStatus.ERROR
    assert service.calls == []
    assert repository.requests == []


def test_execution_result_is_persisted_with_required_fields(tmp_path: Path) -> None:
    runner, _, _, store = make_runner(tmp_path, AIDPState.READY_FOR_CODEX)
    result = runner.run_ready()
    payload = json.loads((store.root / "results" / "execution-1.json").read_text(encoding="utf-8"))
    persisted = payload["codex_execution_result"]
    assert payload["timestamp"]
    assert persisted == {
        "changed_files": ["aidp_orchestration/runner.py"],
        "execution_id": "execution-1",
        "failure_reason": None,
        "resulting_commit": "base",
        "scope_compliance": "COMPLIANT",
        "start_commit": "base",
        "status": "SUCCESS",
        "task_id": "TASK-9000",
        "validation_results": [{"detail": "exit_code=0", "name": "pytest", "passed": True}],
    }
    assert result.execution_result is not None


def test_audit_is_append_only_and_contains_no_prompt_or_secret(tmp_path: Path) -> None:
    runner, _, _, store = make_runner(tmp_path, AIDPState.WAITING)
    runner.run_ready()
    runner.run_ready()
    lines = (store.root / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all(json.loads(line)["trigger"] == "run-ready" for line in lines)
    audit = "\n".join(lines).lower()
    assert "prompt" not in audit
    assert "secret" not in audit


def test_runner_does_not_mutate_task_or_handoff_files_or_create_authority(tmp_path: Path) -> None:
    task = tmp_path / ".ai" / "tasks" / "ready" / "TASK-9000.md"
    handoff = tmp_path / ".ai" / "handoff" / "TO-CODEX.md"
    task.parent.mkdir(parents=True)
    handoff.parent.mkdir(parents=True)
    task.write_text("READY", encoding="utf-8")
    handoff.write_text("OPEN", encoding="utf-8")
    before = (task.read_bytes(), handoff.read_bytes())
    runner, _, _, _ = make_runner(tmp_path, AIDPState.READY_FOR_CODEX)

    serialized = serialize_runner_result(runner.run_ready())

    assert before == (task.read_bytes(), handoff.read_bytes())
    assert "APPROVED" not in serialized
    assert '"DONE"' not in serialized


def test_runner_serialization_is_stable_and_execution_result_remains_authoritative(tmp_path: Path) -> None:
    runner, _, _, _ = make_runner(tmp_path, AIDPState.READY_FOR_CODEX)
    payload = json.loads(serialize_runner_result(runner.run_ready()))["runner_result"]
    assert payload["status"] == "EXECUTED"
    assert payload["execution_result"]["status"] == "SUCCESS"
    assert payload["intended_next_state"] == "READY_FOR_ARCHITECT"


@pytest.mark.parametrize("status", (ExecutionStatus.ERROR, ExecutionStatus.TEST_FAILED, ExecutionStatus.SCOPE_VIOLATION))
def test_failed_execution_outcomes_are_persisted_and_audited(tmp_path: Path, status: ExecutionStatus) -> None:
    repository = FakeRepository(tmp_path, AIDPState.READY_FOR_CODEX)
    request_value = repository.build_execution_request("TASK-9000")
    scope = ScopeCompliance.VIOLATION if status is ExecutionStatus.SCOPE_VIOLATION else ScopeCompliance.NOT_EVALUATED
    execution = CodexExecutionResult(
        request_value.execution_id, request_value.task_id, "base", None, (),
        (ValidationResult("pytest", False, "exit_code=1"),) if status is ExecutionStatus.TEST_FAILED else (),
        status, "terminal failure", scope,
    )
    repository.requests.clear()
    store = LocalRuntimeStore(tmp_path / "runtime")
    runner = AIDPRunner(repository, execution_service=FakeExecutionService(execution), runtime_store=store)
    result = runner.run_ready()
    persisted = json.loads((store.root / "results/execution-1.json").read_text(encoding="utf-8"))
    audit = json.loads((store.root / "audit.jsonl").read_text(encoding="utf-8"))
    assert result.status is RunnerStatus.EXECUTED
    assert persisted["codex_execution_result"]["status"] == status.value
    assert audit["execution_id"] == "execution-1"


def test_unexpected_executor_failure_is_converted_to_persisted_error(tmp_path: Path) -> None:
    class ExplodingService:
        def execute(self, request):
            raise AssertionError("must not escape")

    repository = FakeRepository(tmp_path, AIDPState.READY_FOR_CODEX)
    store = LocalRuntimeStore(tmp_path / "runtime")
    result = AIDPRunner(repository, execution_service=ExplodingService(), runtime_store=store).run_ready()
    persisted = json.loads((store.root / "results/execution-1.json").read_text(encoding="utf-8"))
    assert result.status is RunnerStatus.EXECUTED
    assert result.execution_result.status is ExecutionStatus.ERROR
    assert persisted["codex_execution_result"]["failure_reason"] == "unexpected executor failure: AssertionError"
    assert (store.root / "audit.jsonl").is_file()


def test_keyboard_interrupt_is_persisted_before_shutdown_is_requested(tmp_path: Path) -> None:
    class InterruptedService:
        def execute(self, request):
            raise KeyboardInterrupt

    repository = FakeRepository(tmp_path, AIDPState.READY_FOR_CODEX)
    store = LocalRuntimeStore(tmp_path / "runtime")
    result = AIDPRunner(repository, execution_service=InterruptedService(), runtime_store=store).run_ready()
    assert result.shutdown_requested
    assert result.execution_result.status is ExecutionStatus.ERROR
    assert (store.root / "results/execution-1.json").is_file()
    assert (store.root / "audit.jsonl").is_file()
