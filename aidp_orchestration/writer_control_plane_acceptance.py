"""Isolated Writer-to-Control-Plane end-to-end acceptance harness."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from .acceptance import AcceptanceHarness
from .architect_writer import ArchitectContractWriter
from .contracts import (
    AIDPState,
    AcceptanceStatus,
    ArchitectTaskContract,
    CleanupStatus,
    ControlPlaneAction,
    ControlPlaneResult,
    ExecutionStatus,
    ScopeCompliance,
    ValidationResult,
    WriterAction,
    WriterControlPlaneAcceptanceResult,
    WriterResult,
    utc_now,
)
from .control_plane import AIDPControlPlane
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore


WRITER_E2E_TASK_ID = "TASK-E2E-WRITER-0001"
WRITER_E2E_BRANCH = "aidp-writer-control-plane-e2e"
WRITER_E2E_PROBE_PATH = "tests/orchestration/writer_e2e_probe.txt"
WRITER_E2E_PROBE_CONTENT = "AIDP_WRITER_CONTROL_PLANE_E2E_OK\n"

ControlPlaneFactory = Callable[[AIDPRepository, float], AIDPControlPlane]


class WriterControlPlaneAcceptanceHarness:
    def __init__(
        self,
        source_root: Path,
        *,
        timeout_seconds: float = 900.0,
        preserve_on_failure: bool = True,
        control_plane_factory: ControlPlaneFactory | None = None,
    ):
        self.source_root = source_root.resolve()
        self.timeout_seconds = timeout_seconds
        self.preserve_on_failure = preserve_on_failure
        self.control_plane_factory = control_plane_factory

    def run(self) -> WriterControlPlaneAcceptanceResult:
        fixture_root = Path(tempfile.mkdtemp(prefix="aidp-acceptance-e2e-writer-control-plane-"))
        source_before = self._source_aidp_snapshot()
        writer_result: WriterResult | None = None
        ready_commit: str | None = None
        control_result: ControlPlaneResult | None = None
        changed_files: tuple[str, ...] = ()
        scope = ScopeCompliance.NOT_EVALUATED
        validations: tuple[ValidationResult, ...] = ()
        inbox_persisted = False
        failure_reason: str | None = None

        try:
            self.build_fixture(fixture_root)
            repository = AIDPRepository(fixture_root)
            if repository.inspect().state is not AIDPState.WAITING:
                raise RuntimeError("fixture did not initialize in WAITING")
            if self._git(fixture_root, "status", "--porcelain=v1"):
                raise RuntimeError("initial fixture is dirty")

            contract = self.build_contract(repository)
            runtime = LocalRuntimeStore.for_repository(fixture_root)
            writer_result = ArchitectContractWriter(repository, runtime_root=runtime.root).materialize_task(contract)
            expected_paths = (
                ".ai/handoff/TO-ARCHITECT.md",
                ".ai/handoff/TO-CODEX.md",
                f".ai/tasks/ready/{WRITER_E2E_TASK_ID}.md",
            )
            if writer_result.decision.action is not WriterAction.MATERIALIZE_READY:
                raise RuntimeError("Architect writer blocked fixture materialization")
            if writer_result.materialized_paths != expected_paths:
                raise RuntimeError("Architect writer materialized unexpected paths")
            if repository.inspect().state is not AIDPState.READY_FOR_CODEX:
                raise RuntimeError("writer output is not READY_FOR_CODEX")

            self._run_git(fixture_root, "add", "--", ".ai")
            self._run_git(fixture_root, "commit", "-q", "-m", "test: materialize writer E2E READY state")
            ready_commit = self._git(fixture_root, "rev-parse", "HEAD")
            if self._git(fixture_root, "status", "--porcelain=v1"):
                raise RuntimeError("committed READY fixture is dirty")

            control_plane = self._control_plane(repository)
            control_result = control_plane.run_once()
            execution = control_result.runner_result.execution_result if control_result.runner_result else None
            if execution is not None:
                changed_files = execution.changed_files
                scope = execution.scope_compliance
                validations = execution.validation_results
            inbox_persisted = bool(
                control_result.architect_inbox_path
                and Path(control_result.architect_inbox_path).is_file()
            )
            source_unchanged = self._source_aidp_snapshot() == source_before
            failure_reason = self._failure_reason(
                fixture_root,
                writer_result,
                ready_commit,
                control_result,
                inbox_persisted,
                source_unchanged,
            )
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            source_unchanged = self._source_aidp_snapshot() == source_before
            failure_reason = str(exc)

        passed = failure_reason is None
        cleanup_status = self._cleanup(fixture_root, passed)
        if cleanup_status is CleanupStatus.FAILED:
            passed = False
            failure_reason = failure_reason or "temporary repository cleanup failed"
        return WriterControlPlaneAcceptanceResult(
            AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
            writer_result,
            ready_commit,
            control_result,
            changed_files,
            scope,
            validations,
            inbox_persisted,
            source_unchanged,
            cleanup_status,
            str(fixture_root),
            failure_reason,
        )

    @staticmethod
    def build_fixture(root: Path) -> None:
        ready = root / ".ai" / "tasks" / "ready"
        review = root / ".ai" / "tasks" / "review"
        handoff = root / ".ai" / "handoff"
        probe = root / WRITER_E2E_PROBE_PATH
        ready.mkdir(parents=True)
        review.mkdir(parents=True)
        handoff.mkdir(parents=True)
        probe.parent.mkdir(parents=True)
        (handoff / "TO-CODEX.md").write_text(
            "Status: WAITING\nCurrent AIDP Task: NONE\nCurrent Phase: IDLE / WAITING\n",
            encoding="utf-8",
        )
        (handoff / "TO-ARCHITECT.md").write_text(
            "Status: WAITING\nTask: NONE\n",
            encoding="utf-8",
        )
        probe.write_text("PENDING\n", encoding="utf-8")
        subprocess.run(("git", "init", "-q", "-b", WRITER_E2E_BRANCH), cwd=root, check=True)
        subprocess.run(("git", "config", "user.name", "AIDP Writer E2E Harness"), cwd=root, check=True)
        subprocess.run(("git", "config", "user.email", "aidp-writer-e2e@localhost"), cwd=root, check=True)
        subprocess.run(("git", "add", "--", ".ai", WRITER_E2E_PROBE_PATH), cwd=root, check=True)
        subprocess.run(("git", "commit", "-q", "-m", "test: initialize Writer Control Plane E2E fixture"), cwd=root, check=True)

    def build_contract(self, repository: AIDPRepository) -> ArchitectTaskContract:
        return ArchitectTaskContract(
            WRITER_E2E_TASK_ID,
            "Writer Control Plane E2E Probe",
            "acceptance-e2e",
            repository.head,
            (WRITER_E2E_PROBE_PATH,),
            (".ai/**", "frontend/**", "core/**", "application/**"),
            ("git diff --check",),
            (
                f"Change only {WRITER_E2E_PROBE_PATH}",
                "Set its exact content to AIDP_WRITER_CONTROL_PLANE_E2E_OK",
            ),
            False,
            utc_now(),
        )

    def _control_plane(self, repository: AIDPRepository) -> AIDPControlPlane:
        if self.control_plane_factory is not None:
            return self.control_plane_factory(repository, self.timeout_seconds)
        return AIDPControlPlane(repository, timeout_seconds=self.timeout_seconds)

    def _failure_reason(
        self,
        fixture_root: Path,
        writer_result: WriterResult,
        ready_commit: str,
        control_result: ControlPlaneResult,
        inbox_persisted: bool,
        source_unchanged: bool,
    ) -> str | None:
        execution = control_result.runner_result.execution_result if control_result.runner_result else None
        checks = (
            (writer_result.decision.action is WriterAction.MATERIALIZE_READY, "writer did not materialize READY"),
            (bool(ready_commit), "READY commit is missing"),
            (control_result.decision.action is ControlPlaneAction.EXECUTE, "Control Plane did not decide EXECUTE"),
            (control_result.final_action is ControlPlaneAction.READY_FOR_ARCHITECT, "final state is not READY_FOR_ARCHITECT"),
            (execution is not None and execution.status is ExecutionStatus.SUCCESS, "Codex execution was not successful"),
            (execution is not None and execution.start_commit == ready_commit, "execution did not start from the READY commit"),
            (execution is not None and execution.resulting_commit == ready_commit, "execution changed or lost the committed HEAD"),
            (execution is not None and execution.changed_files == (WRITER_E2E_PROBE_PATH,), "changed files are not exactly the probe"),
            (execution is not None and execution.scope_compliance is ScopeCompliance.COMPLIANT, "scope is not compliant"),
            (execution is not None and bool(execution.validation_results) and all(item.passed for item in execution.validation_results), "validation did not pass"),
            ((fixture_root / WRITER_E2E_PROBE_PATH).read_text(encoding="utf-8") == WRITER_E2E_PROBE_CONTENT, "probe content is not exact"),
            (inbox_persisted, "Architect Inbox was not persisted"),
            (source_unchanged, "source repository AIDP state changed"),
        )
        for accepted, reason in checks:
            if not accepted:
                return reason
        return None

    def _cleanup(self, root: Path, passed: bool) -> CleanupStatus:
        if not passed and self.preserve_on_failure:
            return CleanupStatus.PRESERVED
        try:
            AcceptanceHarness.remove_fixture(root)
        except (OSError, ValueError):
            return CleanupStatus.FAILED
        return CleanupStatus.CLEANED

    def _source_aidp_snapshot(self) -> tuple[tuple[str, str], ...]:
        files: list[tuple[str, str]] = []
        for relative_root in (Path(".ai/tasks"), Path(".ai/handoff")):
            directory = self.source_root / relative_root
            if not directory.exists():
                continue
            for path in sorted(item for item in directory.rglob("*") if item.is_file()):
                relative = path.relative_to(self.source_root).as_posix()
                files.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
        return tuple(files)

    @staticmethod
    def _run_git(root: Path, *args: str) -> None:
        subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)

    @staticmethod
    def _git(root: Path, *args: str) -> str:
        return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def serialize_writer_control_plane_acceptance_result(result: WriterControlPlaneAcceptanceResult) -> str:
    return json.dumps({"writer_control_plane_acceptance_result": asdict(result)}, default=_json_default, sort_keys=True)


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")
