from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aidp_orchestration.acceptance import (
    E2E_BRANCH,
    E2E_PROBE_CONTENT,
    E2E_PROBE_PATH,
    E2E_TASK_ID,
    AcceptanceHarness,
    serialize_acceptance_result,
)
from aidp_orchestration.contracts import (
    AIDPState,
    AcceptanceStatus,
    CleanupStatus,
    CodexExecutionRequest,
    CodexExecutionResult,
    ExecutionStatus,
    ScopeCompliance,
    ValidationResult,
)
from aidp_orchestration.repository import AIDPRepository


class ProbeExecutionService:
    def __init__(self, *, scope_violation: bool = False):
        self.scope_violation = scope_violation
        self.calls = 0

    def execute(self, request: CodexExecutionRequest) -> CodexExecutionResult:
        self.calls += 1
        root = Path(request.repository)
        (root / E2E_PROBE_PATH).write_text(E2E_PROBE_CONTENT, encoding="utf-8")
        changed = (E2E_PROBE_PATH,)
        status = ExecutionStatus.SUCCESS
        scope = ScopeCompliance.COMPLIANT
        reason = None
        if self.scope_violation:
            extra = root / "unexpected.txt"
            extra.write_text("unexpected\n", encoding="utf-8")
            changed = (E2E_PROBE_PATH, "unexpected.txt")
            status = ExecutionStatus.SCOPE_VIOLATION
            scope = ScopeCompliance.VIOLATION
            reason = "changed files exceed the declared scope"
        return CodexExecutionResult(
            request.execution_id,
            request.task_id,
            request.expected_head,
            request.expected_head,
            changed,
            (ValidationResult("git diff --check", True, "passed"),),
            status,
            reason,
            scope,
        )


def init_source_repository(root: Path) -> Path:
    handoff = root / ".ai" / "handoff" / "TO-CODEX.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("Status: WAITING\n", encoding="utf-8")
    subprocess.run(("git", "init", "-q", "-b", "source"), cwd=root, check=True)
    subprocess.run(("git", "config", "user.name", "Test"), cwd=root, check=True)
    subprocess.run(("git", "config", "user.email", "test@localhost"), cwd=root, check=True)
    subprocess.run(("git", "add", ".ai"), cwd=root, check=True)
    subprocess.run(("git", "commit", "-q", "-m", "source"), cwd=root, check=True)
    return handoff


def test_fixture_builds_minimal_clean_ready_repository(tmp_path: Path) -> None:
    AcceptanceHarness.build_fixture(tmp_path)
    repository = AIDPRepository(tmp_path)
    decision = repository.inspect()
    metadata = repository.parse_metadata(tmp_path / ".ai" / "tasks" / "ready" / f"{E2E_TASK_ID}.md")

    assert decision.state is AIDPState.READY_FOR_CODEX
    assert repository.branch == E2E_BRANCH
    assert metadata is not None
    assert metadata.allowed_scope == (E2E_PROBE_PATH,)
    assert metadata.validation_requirements == ("git diff --check",)
    assert (tmp_path / E2E_PROBE_PATH).read_text(encoding="utf-8") == "PENDING\n"
    assert subprocess.check_output(("git", "status", "--porcelain=v1"), cwd=tmp_path, text=True) == ""


def test_harness_accepts_exact_probe_and_does_not_mutate_source_aidp(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    handoff = init_source_repository(source)
    before = handoff.read_bytes()
    service = ProbeExecutionService()
    result = AcceptanceHarness(
        source,
        service_factory=lambda _root, _timeout: service,
    ).run()

    assert result.status is AcceptanceStatus.PASS
    assert result.cleanup_status is CleanupStatus.CLEANED
    assert result.result_persisted and result.audit_persisted
    assert result.source_aidp_unchanged
    assert handoff.read_bytes() == before
    assert service.calls == 1


def test_scope_violation_fails_closed_and_preserves_fixture(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    init_source_repository(source)
    result = AcceptanceHarness(
        source,
        service_factory=lambda _root, _timeout: ProbeExecutionService(scope_violation=True),
    ).run()

    fixture = Path(result.temporary_repository)
    try:
        assert result.status is AcceptanceStatus.FAIL
        assert result.cleanup_status is CleanupStatus.PRESERVED
        assert fixture.is_dir()
        assert result.runner_result is not None
        assert result.runner_result.execution_result is not None
        assert result.runner_result.execution_result.scope_compliance is ScopeCompliance.VIOLATION
    finally:
        AcceptanceHarness.remove_fixture(fixture)


def test_failure_can_clean_fixture_when_preservation_is_disabled(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    init_source_repository(source)
    result = AcceptanceHarness(
        source,
        preserve_on_failure=False,
        service_factory=lambda _root, _timeout: ProbeExecutionService(scope_violation=True),
    ).run()
    assert result.status is AcceptanceStatus.FAIL
    assert result.cleanup_status is CleanupStatus.CLEANED
    assert not Path(result.temporary_repository).exists()


def test_dirty_fixture_before_start_fails_closed(tmp_path: Path) -> None:
    class DirtyFixtureHarness(AcceptanceHarness):
        @staticmethod
        def build_fixture(root: Path) -> None:
            AcceptanceHarness.build_fixture(root)
            (root / E2E_PROBE_PATH).write_text("DIRTY\n", encoding="utf-8")

    source = tmp_path / "source"
    source.mkdir()
    init_source_repository(source)
    result = DirtyFixtureHarness(
        source,
        preserve_on_failure=False,
        service_factory=lambda _root, _timeout: ProbeExecutionService(),
    ).run()
    assert result.status is AcceptanceStatus.FAIL
    assert result.failure_reason == "fixture repository is dirty before execution"


def test_acceptance_serialization_is_stable(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    init_source_repository(source)
    result = AcceptanceHarness(
        source,
        service_factory=lambda _root, _timeout: ProbeExecutionService(),
    ).run()
    payload = json.loads(serialize_acceptance_result(result))["acceptance_result"]
    assert payload["status"] == "PASS"
    assert payload["runner_result"]["status"] == "EXECUTED"
    assert payload["runner_result"]["execution_result"]["changed_files"] == [E2E_PROBE_PATH]
    assert payload["result_persisted"] is True
    assert payload["audit_persisted"] is True
