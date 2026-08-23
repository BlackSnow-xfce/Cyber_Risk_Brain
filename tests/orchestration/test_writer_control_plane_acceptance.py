from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

from aidp_orchestration.acceptance import AcceptanceHarness
from aidp_orchestration.contracts import (
    AIDPState,
    AcceptanceStatus,
    CleanupStatus,
    CodexExecutionResult,
    ExecutionStatus,
    RunnerResult,
    RunnerStatus,
    ScopeCompliance,
    ValidationResult,
)
from aidp_orchestration.control_plane import AIDPControlPlane, LocalArchitectInbox
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.writer_control_plane_acceptance import (
    WRITER_E2E_PROBE_CONTENT,
    WRITER_E2E_PROBE_PATH,
    WRITER_E2E_TASK_ID,
    WriterControlPlaneAcceptanceHarness,
    serialize_writer_control_plane_acceptance_result,
)


class ProbeRunner:
    def __init__(self, repository: AIDPRepository, status: ExecutionStatus):
        self.repository = repository
        self.status = status
        self.calls = 0

    def run_ready(self) -> RunnerResult:
        self.calls += 1
        root = self.repository.root
        (root / WRITER_E2E_PROBE_PATH).write_text(WRITER_E2E_PROBE_CONTENT, encoding="utf-8")
        success = self.status is ExecutionStatus.SUCCESS
        execution = CodexExecutionResult(
            "writer-e2e-execution",
            WRITER_E2E_TASK_ID,
            self.repository.head,
            self.repository.head,
            (WRITER_E2E_PROBE_PATH,),
            (ValidationResult("git diff --check", success, "passed" if success else "failed"),),
            self.status,
            None if success else "fixture execution failed",
            ScopeCompliance.COMPLIANT if success else ScopeCompliance.VIOLATION,
        )
        intended = AIDPState.READY_FOR_ARCHITECT if success else AIDPState.BLOCKED
        return RunnerResult(
            RunnerStatus.EXECUTED,
            WRITER_E2E_TASK_ID,
            AIDPState.READY_FOR_CODEX,
            intended,
            "fixture runner completed",
            execution,
        )


def initialize_source(root: Path) -> Path:
    handoff = root / ".ai" / "handoff" / "TO-CODEX.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("Status: WAITING\n", encoding="utf-8")
    subprocess.run(("git", "init", "-q", "-b", "source"), cwd=root, check=True)
    subprocess.run(("git", "config", "user.name", "Test"), cwd=root, check=True)
    subprocess.run(("git", "config", "user.email", "test@localhost"), cwd=root, check=True)
    subprocess.run(("git", "add", ".ai"), cwd=root, check=True)
    subprocess.run(("git", "commit", "-q", "-m", "source"), cwd=root, check=True)
    return handoff


def control_plane_factory(status: ExecutionStatus):
    def factory(repository: AIDPRepository, _timeout: float) -> AIDPControlPlane:
        runtime = LocalRuntimeStore.for_repository(repository.root)
        return AIDPControlPlane(
            repository,
            runner=ProbeRunner(repository, status),
            architect_inbox=LocalArchitectInbox(runtime.root),
        )

    return factory


def test_fixture_initializes_in_waiting(tmp_path: Path) -> None:
    WriterControlPlaneAcceptanceHarness.build_fixture(tmp_path)
    repository = AIDPRepository(tmp_path)
    assert repository.inspect().state is AIDPState.WAITING
    assert subprocess.check_output(("git", "status", "--porcelain=v1"), cwd=tmp_path, text=True) == ""


def test_writer_ready_commit_control_plane_and_inbox_pass(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    handoff = initialize_source(source)
    before = handoff.read_bytes()
    result = WriterControlPlaneAcceptanceHarness(
        source,
        control_plane_factory=control_plane_factory(ExecutionStatus.SUCCESS),
    ).run()

    assert result.status is AcceptanceStatus.PASS
    assert result.writer_result is not None
    assert result.writer_result.decision.action.value == "MATERIALIZE_READY"
    assert result.ready_commit
    assert result.control_plane_result is not None
    assert result.control_plane_result.decision.action.value == "EXECUTE"
    assert result.control_plane_result.final_action.value == "READY_FOR_ARCHITECT"
    assert result.architect_inbox_persisted
    assert result.source_aidp_unchanged
    assert handoff.read_bytes() == before
    assert result.cleanup_status is CleanupStatus.CLEANED
    assert not Path(result.temporary_repository).exists()


def test_stale_writer_head_remains_blocked_and_fixture_is_preserved(tmp_path: Path) -> None:
    class StaleHarness(WriterControlPlaneAcceptanceHarness):
        def build_contract(self, repository: AIDPRepository):
            return replace(super().build_contract(repository), expected_head="stale")

    source = tmp_path / "source"
    source.mkdir()
    initialize_source(source)
    result = StaleHarness(
        source,
        control_plane_factory=control_plane_factory(ExecutionStatus.SUCCESS),
    ).run()
    fixture = Path(result.temporary_repository)
    try:
        assert result.status is AcceptanceStatus.FAIL
        assert result.writer_result is None or result.writer_result.decision.action.value == "BLOCKED"
        assert result.control_plane_result is None
        assert result.cleanup_status is CleanupStatus.PRESERVED
        assert fixture.is_dir()
    finally:
        AcceptanceHarness.remove_fixture(fixture)


def test_failed_control_plane_preserves_fixture_with_writer_commit(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    initialize_source(source)
    result = WriterControlPlaneAcceptanceHarness(
        source,
        control_plane_factory=control_plane_factory(ExecutionStatus.SCOPE_VIOLATION),
    ).run()
    fixture = Path(result.temporary_repository)
    try:
        assert result.status is AcceptanceStatus.FAIL
        assert result.ready_commit
        assert result.cleanup_status is CleanupStatus.PRESERVED
        assert fixture.is_dir()
        assert subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=fixture, text=True).strip() == result.ready_commit
    finally:
        AcceptanceHarness.remove_fixture(fixture)


def test_writer_control_plane_acceptance_serialization_is_stable(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    initialize_source(source)
    result = WriterControlPlaneAcceptanceHarness(
        source,
        control_plane_factory=control_plane_factory(ExecutionStatus.SUCCESS),
    ).run()
    payload = json.loads(serialize_writer_control_plane_acceptance_result(result))[
        "writer_control_plane_acceptance_result"
    ]
    assert payload["status"] == "PASS"
    assert payload["writer_result"]["decision"]["action"] == "MATERIALIZE_READY"
    assert payload["control_plane_result"]["decision"]["action"] == "EXECUTE"
    assert payload["changed_files"] == [WRITER_E2E_PROBE_PATH]
    assert payload["scope_compliance"] == "COMPLIANT"
