from __future__ import annotations

from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    AIDPState,
    CodexExecutionResult,
    ExecutionStatus,
    ScopeCompliance,
    ValidationResult,
)
from aidp_orchestration.repository import AIDPRepository


def write_repo(tmp_path: Path, *, ready: tuple[str, ...] = (), review: tuple[str, ...] = (), status: str = "READY", task_namespace: str = "product") -> AIDPRepository:
    (tmp_path / ".ai" / "tasks" / "ready").mkdir(parents=True)
    (tmp_path / ".ai" / "tasks" / "review").mkdir(parents=True)
    (tmp_path / ".ai" / "handoff").mkdir(parents=True)
    for task_id in ready:
        (tmp_path / ".ai" / "tasks" / "ready" / f"{task_id}.md").write_text(
            "---\n"
            f"task_id: {task_id}\nphase: implementation\n"
            "allowed_scope: application/**, tests/**\n"
            "prohibited_actions: .ai/tasks/**, .git/**\n"
            "validation_requirements: pytest, git diff --check\n"
            "product_owner_gate: false\n---\n",
            encoding="utf-8",
        )
    for task_id in review:
        (tmp_path / ".ai" / "tasks" / "review" / f"{task_id}.md").write_text(f"Status: {status}\n", encoding="utf-8")
    task_id = (ready or review or (None,))[0]
    (tmp_path / ".ai" / "handoff" / "TO-CODEX.md").write_text(
        f"Status: {'OPEN' if ready else 'WAITING'}\nCurrent AIDP Task: {task_id or 'NONE'}\n",
        encoding="utf-8",
    )
    (tmp_path / ".ai" / "handoff" / "TO-ARCHITECT.md").write_text(
        f"Status: {'WAITING' if ready else 'OPEN'}\nTask: {task_id or 'NONE'}\n",
        encoding="utf-8",
    )
    repo = AIDPRepository(tmp_path, task_namespace=task_namespace)
    repo._git = lambda *args: "main" if args == ("branch", "--show-current") else "base-commit"
    return repo


def test_exactly_one_ready_task_is_ready_for_codex(tmp_path: Path) -> None:
    assert write_repo(tmp_path, ready=("TASK-9000",)).inspect().state is AIDPState.READY_FOR_CODEX


def test_exact_infrastructure_namespace_is_discovered_without_broadening(tmp_path: Path) -> None:
    assert write_repo(
        tmp_path, ready=("AIDP-INFRA-0001",), task_namespace="infrastructure",
    ).inspect().state is AIDPState.READY_FOR_CODEX
    repo = write_repo(
        tmp_path / "invalid", ready=("AIDP-INFRA-00001",),
        task_namespace="infrastructure",
    )
    assert repo.inspect().state is AIDPState.WAITING


def test_task_namespaces_are_repository_isolated(tmp_path: Path) -> None:
    product = write_repo(tmp_path, ready=("TASK-9000", "AIDP-INFRA-0001"))
    infrastructure = AIDPRepository(tmp_path, task_namespace="infrastructure")
    infrastructure._git = product._git
    assert product.inspect().task_id == "TASK-9000"
    assert infrastructure.inspect().state is AIDPState.BLOCKED
    assert infrastructure.accepts_task_id("AIDP-INFRA-0001")
    assert not infrastructure.accepts_task_id("TASK-9000")
    with pytest.raises(ValueError, match="namespace"):
        infrastructure.build_execution_request("TASK-9000")


def test_review_task_is_ready_for_architect(tmp_path: Path) -> None:
    assert write_repo(tmp_path, review=("TASK-9000",)).inspect().state is AIDPState.READY_FOR_ARCHITECT


def test_rework_requires_explicit_execution_scope(tmp_path: Path) -> None:
    decision = write_repo(tmp_path, review=("TASK-9000",), status="REVIEW / REWORK REQUIRED").inspect()
    assert decision.state is AIDPState.BLOCKED


def test_rework_with_explicit_scope_can_create_new_execution_request(tmp_path: Path) -> None:
    repo = write_repo(tmp_path, review=("TASK-9000",), status="REVIEW / REWORK REQUIRED")
    path = tmp_path / ".ai" / "tasks" / "review" / "TASK-9000.md"
    path.write_text(
        "---\ntask_id: TASK-9000\nphase: rework\nallowed_scope: application/**\n"
        "prohibited_actions: .git/**\nvalidation_requirements: pytest\n---\n"
        "Status: REVIEW / REWORK REQUIRED\n",
        encoding="utf-8",
    )
    assert repo.inspect().state is AIDPState.REWORK_REQUIRED
    request = repo.build_execution_request("TASK-9000", rework_count=1)
    assert request.task_id == "TASK-9000"
    assert request.rework_count == 1


def test_two_ready_tasks_are_blocked(tmp_path: Path) -> None:
    assert write_repo(tmp_path, ready=("TASK-9000", "TASK-9001")).inspect().state is AIDPState.BLOCKED


def test_ready_and_review_conflict_is_blocked(tmp_path: Path) -> None:
    assert write_repo(tmp_path, ready=("TASK-9000",), review=("TASK-9001",)).inspect().state is AIDPState.BLOCKED


def test_missing_task_waits(tmp_path: Path) -> None:
    assert write_repo(tmp_path).inspect().state is AIDPState.WAITING


def test_done_task_cannot_create_execution_request(tmp_path: Path) -> None:
    repo = write_repo(tmp_path)
    done = tmp_path / ".ai" / "tasks" / "done"
    done.mkdir()
    (done / "TASK-9000.md").write_text("Status: DONE / PASS / APPROVED\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one active task"):
        repo.build_execution_request("TASK-9000")


def test_conflicting_handoffs_are_blocked(tmp_path: Path) -> None:
    repo = write_repo(tmp_path, ready=("TASK-9000",))
    (tmp_path / ".ai" / "handoff" / "TO-ARCHITECT.md").write_text(
        "Status: OPEN\nTask: TASK-9999\n", encoding="utf-8"
    )
    assert repo.inspect().state is AIDPState.BLOCKED


def test_architect_approval_with_product_owner_gate_is_waiting(tmp_path: Path) -> None:
    repo = write_repo(tmp_path, review=("TASK-9000",), status="ARCHITECT_APPROVED")
    path = tmp_path / ".ai" / "tasks" / "review" / "TASK-9000.md"
    path.write_text(
        "---\ntask_id: TASK-9000\nphase: acceptance\nallowed_scope: application/**\n"
        "prohibited_actions: .git/**\nvalidation_requirements: pytest\nproduct_owner_gate: true\n---\n"
        "Status: ARCHITECT_APPROVED\n",
        encoding="utf-8",
    )
    assert repo.inspect().state is AIDPState.WAITING_FOR_PRODUCT_OWNER


def test_product_owner_rework_requested_is_not_codex_executable(tmp_path: Path) -> None:
    repo = write_repo(tmp_path, review=("TASK-9000",), status="PRODUCT OWNER REWORK REQUESTED")
    decision = repo.inspect()
    assert decision.state is AIDPState.PRODUCT_OWNER_REWORK_REQUESTED
    assert decision.next_state is None
    with pytest.raises(ValueError):
        repo.build_execution_request("TASK-9000")


def test_stale_head_blocks_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = write_repo(tmp_path, ready=("TASK-9000",))
    request = repo.build_execution_request("TASK-9000")
    monkeypatch.setattr(repo, "_git", lambda *args: "different" if args == ("rev-parse", "HEAD") else "main")
    result = CodexExecutionResult(
        request.execution_id, request.task_id, request.expected_head, "different", (),
        (ValidationResult("pytest", True),), ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT,
    )
    assert repo.evaluate_result(request, result) is AIDPState.STALE_EXECUTION


def test_scope_violation_is_blocked(tmp_path: Path) -> None:
    repo = write_repo(tmp_path, ready=("TASK-9000",))
    request = repo.build_execution_request("TASK-9000")
    assert repo.validate_scope(request, ("frontend/app.tsx",)) is ScopeCompliance.VIOLATION


def test_success_only_transitions_to_architect_review(tmp_path: Path) -> None:
    repo = write_repo(tmp_path, ready=("TASK-9000",))
    request = repo.build_execution_request("TASK-9000")
    result = CodexExecutionResult(
        request.execution_id, request.task_id, request.expected_head, request.expected_head, (),
        (ValidationResult("pytest", True),), ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT,
    )
    assert repo.evaluate_result(request, result) is AIDPState.READY_FOR_ARCHITECT


def test_dry_run_does_not_mutate_repository(tmp_path: Path) -> None:
    repo = write_repo(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    repo.inspect()
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    assert after == before
