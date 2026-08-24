from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from aidp_orchestration.architect_writer import (
    ArchitectContractWriter,
    load_architect_task_contract,
    serialize_architect_task_contract,
    serialize_writer_decision,
    serialize_writer_result,
)
from aidp_orchestration.contracts import (
    AIDPState,
    ArchitectTaskContract,
    ReworkContract,
    WriterAction,
    utc_now,
)
from aidp_orchestration.repository import AIDPRepository


def git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def make_repository(tmp_path: Path, *, active: bool = False, rework: bool = False) -> AIDPRepository:
    ready = tmp_path / ".ai" / "tasks" / "ready"
    review = tmp_path / ".ai" / "tasks" / "review"
    handoff = tmp_path / ".ai" / "handoff"
    ready.mkdir(parents=True)
    review.mkdir(parents=True)
    handoff.mkdir(parents=True)
    task_id = "TASK-9000"
    metadata = (
        "---\n"
        f"task_id: {task_id}\n"
        "phase: implementation\n"
        "allowed_scope: aidp_orchestration/**, tests/orchestration/**\n"
        "prohibited_actions: .ai/**, frontend/**\n"
        "validation_requirements: pytest, git diff --check\n"
        "product_owner_gate: false\n"
        "---\n"
    )
    if active:
        (ready / f"{task_id}.md").write_text(metadata, encoding="utf-8")
    if rework:
        (review / f"{task_id}.md").write_text(metadata + "Status: REVIEW / REWORK REQUIRED\n", encoding="utf-8")
    has_task = active or rework
    (handoff / "TO-CODEX.md").write_text(
        f"Status: {'WAITING' if rework or not has_task else 'OPEN'}\n"
        f"Current AIDP Task: {task_id if has_task else 'NONE'}\n",
        encoding="utf-8",
    )
    (handoff / "TO-ARCHITECT.md").write_text(
        f"Status: {'OPEN' if rework else 'WAITING'}\nTask: {task_id if has_task else 'NONE'}\n",
        encoding="utf-8",
    )
    git(tmp_path, "init", "-q", "-b", "writer-test")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@localhost")
    git(tmp_path, "add", ".ai")
    git(tmp_path, "commit", "-q", "-m", "fixture")
    return AIDPRepository(tmp_path)


def task_contract(repo: AIDPRepository, **changes) -> ArchitectTaskContract:
    value = ArchitectTaskContract(
        "TASK-9001",
        "Architect Writer Fixture",
        "implementation",
        repo.head,
        ("aidp_orchestration/**", "tests/orchestration/**"),
        (".ai/**", "frontend/**"),
        ("pytest", "git diff --check"),
        ("Implement only the authorized fixture scope", "Keep all governance boundaries fail-closed"),
        False,
        utc_now(),
    )
    return replace(value, **changes)


def rework_contract(repo: AIDPRepository, **changes) -> ReworkContract:
    value = ReworkContract(
        "TASK-9000",
        1,
        repo.head,
        ("aidp_orchestration/**",),
        ("Correct the reviewed orchestration defect",),
        ("pytest", "git diff --check"),
        utc_now(),
    )
    return replace(value, **changes)


def writer(
    repo: AIDPRepository,
    *,
    clean: bool = True,
    changed_files=None,
) -> ArchitectContractWriter:
    return ArchitectContractWriter(
        repo,
        is_worktree_clean=None if changed_files is not None else lambda: clean,
        worktree_changed_files=changed_files,
        runtime_root=repo.root / "runtime",
    )


def test_valid_architect_task_contract() -> None:
    contract = ArchitectTaskContract(
        "TASK-9001", "Title", "implementation", "head", ("tests/**",), (".ai/**",),
        ("pytest",), ("Acceptance is explicit",), False, utc_now(),
    )
    assert contract.task_id == "TASK-9001"


@pytest.mark.parametrize("task_id", ("TASK-12", "task-9001", "TASK-ABCD", ""))
def test_invalid_task_id_is_rejected(task_id: str) -> None:
    with pytest.raises(ValueError, match="task_id"):
        ArchitectTaskContract(
            task_id, "Title", "implementation", "head", ("tests/**",), (".ai/**",),
            ("pytest",), ("Acceptance is explicit",), False, utc_now(),
        )


@pytest.mark.parametrize(
    "change",
    (
        {"allowed_scope": ()},
        {"validation_requirements": ()},
        {"acceptance_criteria": ()},
        {"expected_head": ""},
    ),
)
def test_missing_contract_authority_is_rejected(tmp_path: Path, change: dict[str, object]) -> None:
    repo = make_repository(tmp_path)
    with pytest.raises(ValueError):
        task_contract(repo, **change)


def test_stale_head_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    result = writer(repo).materialize_task(task_contract(repo, expected_head="stale"))
    assert result.decision.action is WriterAction.BLOCKED
    assert "stale" in result.failure_reason


def test_dirty_worktree_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    result = writer(repo, clean=False).materialize_task(task_contract(repo))
    assert result.decision.action is WriterAction.BLOCKED
    assert "dirty" in result.failure_reason


def test_active_task_conflict_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, active=True)
    result = writer(repo).materialize_task(task_contract(repo))
    assert result.decision.action is WriterAction.BLOCKED
    assert "active" in result.failure_reason


def test_matching_ready_task_can_be_reauthorized_without_aidp_mutation(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, active=True)
    contract = task_contract(repo, task_id="TASK-9000")
    before = {path: path.read_bytes() for path in repo.ai_root.rglob("*") if path.is_file()}
    result = writer(repo).materialize_task(contract)
    after = {path: path.read_bytes() for path in repo.ai_root.rglob("*") if path.is_file()}
    assert result.decision.action is WriterAction.MATERIALIZE_READY
    assert result.materialized_paths == ()
    assert result.decision.reason == "contract reauthorizes the matching READY task"
    assert after == before


@pytest.mark.parametrize(
    "paths",
    (
        ("aidp_orchestration/continuation.py",),
        (
            "aidp_orchestration/continuation.py",
            "tests/orchestration/test_continuation.py",
        ),
    ),
)
def test_matching_ready_task_admits_only_authorized_dirty_paths(tmp_path: Path, paths: tuple[str, ...]) -> None:
    repo = make_repository(tmp_path, active=True)
    result = writer(repo, changed_files=lambda: paths).materialize_task(task_contract(repo, task_id="TASK-9000"))
    assert result.decision.action is WriterAction.MATERIALIZE_READY


@pytest.mark.parametrize(
    "paths",
    (
        ("frontend/unauthorized.tsx",),
        ("aidp_orchestration/continuation.py", "frontend/unauthorized.tsx"),
    ),
)
def test_matching_ready_task_blocks_any_unauthorized_dirty_path(tmp_path: Path, paths: tuple[str, ...]) -> None:
    repo = make_repository(tmp_path, active=True)
    result = writer(repo, changed_files=lambda: paths).materialize_task(task_contract(repo, task_id="TASK-9000"))
    assert result.decision.action is WriterAction.BLOCKED
    assert "outside" in result.failure_reason


def test_matching_ready_task_blocks_unreadable_dirty_paths(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, active=True)
    def unreadable():
        raise UnicodeError("malformed status")
    result = writer(repo, changed_files=unreadable).materialize_task(task_contract(repo, task_id="TASK-9000"))
    assert result.decision.action is WriterAction.BLOCKED
    assert "could not be established" in result.failure_reason


def test_matching_ready_task_does_not_bypass_expected_head(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, active=True)
    result = writer(repo).materialize_task(task_contract(repo, task_id="TASK-9000", expected_head="stale"))
    assert result.decision.action is WriterAction.BLOCKED
    assert "stale" in result.failure_reason


@pytest.mark.parametrize(
    "change",
    (
        {"allowed_scope": ("aidp_orchestration/**",)},
        {"prohibited_actions": (".ai/**",)},
        {"validation_requirements": ("pytest",)},
        {"phase": "different"},
        {"product_owner_gate": True},
    ),
)
def test_matching_ready_task_requires_identical_execution_authority(tmp_path: Path, change: dict[str, object]) -> None:
    repo = make_repository(tmp_path, active=True)
    contract = task_contract(repo, task_id="TASK-9000", **change)
    result = writer(repo).materialize_task(contract)
    assert result.decision.action is WriterAction.BLOCKED
    assert "authority" in result.failure_reason


def test_matching_review_task_is_not_executable_as_ready(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, rework=True)
    result = writer(repo).materialize_task(task_contract(repo, task_id="TASK-9000"))
    assert result.decision.action is WriterAction.BLOCKED
    assert "REVIEW" in result.failure_reason


def test_multiple_active_tasks_remain_fail_closed(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, active=True)
    second = repo.ai_root / "tasks" / "review" / "TASK-9001.md"
    second.write_text((repo.ai_root / "tasks" / "ready" / "TASK-9000.md").read_text(encoding="utf-8"), encoding="utf-8")
    result = writer(repo).materialize_task(task_contract(repo, task_id="TASK-9000"))
    assert result.decision.action is WriterAction.BLOCKED
    assert "another active" in result.failure_reason


def test_existing_task_id_collision_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    collision = tmp_path / ".ai" / "tasks" / "done" / "TASK-9001.md"
    collision.parent.mkdir(parents=True)
    collision.write_text("historical task\n", encoding="utf-8")
    result = writer(repo).materialize_task(task_contract(repo))
    assert result.decision.action is WriterAction.BLOCKED
    assert "already exists" in result.failure_reason


def test_unknown_validator_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    contract = task_contract(repo, validation_requirements=("unknown validator",))
    result = writer(repo).materialize_task(contract)
    assert result.decision.action is WriterAction.BLOCKED
    assert "unknown validator" in result.failure_reason


def test_ready_materialization_and_handoffs_are_deterministic_and_parseable(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    contract = task_contract(repo)
    result = writer(repo).materialize_task(contract)
    task = tmp_path / ".ai" / "tasks" / "ready" / "TASK-9001.md"
    codex = tmp_path / ".ai" / "handoff" / "TO-CODEX.md"
    architect = tmp_path / ".ai" / "handoff" / "TO-ARCHITECT.md"

    assert result.decision.action is WriterAction.MATERIALIZE_READY
    assert result.materialized_paths == (
        ".ai/handoff/TO-ARCHITECT.md",
        ".ai/handoff/TO-CODEX.md",
        ".ai/tasks/ready/TASK-9001.md",
    )
    metadata = repo.parse_metadata(task)
    assert metadata is not None
    assert metadata.task_id == contract.task_id
    assert metadata.allowed_scope == contract.allowed_scope
    assert metadata.validation_requirements == contract.validation_requirements
    assert repo.inspect().state is AIDPState.READY_FOR_CODEX
    assert "Status: OPEN" in codex.read_text(encoding="utf-8")
    assert "Current AIDP Task: TASK-9001" in codex.read_text(encoding="utf-8")
    assert "Status: WAITING" in architect.read_text(encoding="utf-8")
    materialized = task.read_text(encoding="utf-8") + codex.read_text(encoding="utf-8") + architect.read_text(encoding="utf-8")
    assert "APPROVED" not in materialized
    assert "DONE" not in materialized


def test_same_contract_produces_same_task_document(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = make_repository(first_root)
    second = make_repository(second_root)
    first_contract = task_contract(first)
    second_contract = replace(first_contract, expected_head=second.head)
    writer(first).materialize_task(first_contract)
    writer(second).materialize_task(second_contract)
    relative = Path(".ai/tasks/ready/TASK-9001.md")
    assert (first_root / relative).read_bytes() == (second_root / relative).read_bytes()


def test_rework_contract_is_persisted_only_for_existing_rework_task(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, rework=True)
    before = tuple(repo.ai_root.rglob("TASK-*.md"))
    result = writer(repo).materialize_rework(rework_contract(repo))
    assert result.decision.action is WriterAction.MATERIALIZE_REWORK
    assert result.rework_contract_path is not None
    assert Path(result.rework_contract_path).is_file()
    assert tuple(repo.ai_root.rglob("TASK-*.md")) == before


def test_rework_without_existing_task_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    assert writer(repo).materialize_rework(rework_contract(repo)).decision.action is WriterAction.BLOCKED


def test_rework_scope_widening_blocks(tmp_path: Path) -> None:
    repo = make_repository(tmp_path, rework=True)
    contract = rework_contract(repo, allowed_rework_scope=("product/**",))
    result = writer(repo).materialize_rework(contract)
    assert result.decision.action is WriterAction.BLOCKED
    assert "widens" in result.failure_reason


def test_serialization_is_stable_and_round_trips(tmp_path: Path) -> None:
    repo = make_repository(tmp_path)
    contract = task_contract(repo)
    serialized = serialize_architect_task_contract(contract)
    path = tmp_path / "contract.json"
    path.write_text(serialized, encoding="utf-8")
    assert load_architect_task_contract(path) == contract
    result = writer(repo).materialize_task(contract)
    assert json.loads(serialize_writer_decision(result.decision))["writer_decision"]["action"] == "MATERIALIZE_READY"
    payload = json.loads(serialize_writer_result(result))["writer_result"]
    assert payload["decision"]["task_id"] == "TASK-9001"
