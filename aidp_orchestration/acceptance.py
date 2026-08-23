"""Isolated end-to-end acceptance harness for the production runner boundary."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from .contracts import (
    AcceptanceResult,
    AcceptanceStatus,
    CleanupStatus,
    ExecutionStatus,
    RunnerResult,
    RunnerStatus,
    ScopeCompliance,
)
from .executor import CodexExecutionService
from .repository import AIDPRepository
from .runner import AIDPRunner, ExecutionService
from .runtime import LocalRuntimeStore


E2E_TASK_ID = "TASK-E2E-0001"
E2E_BRANCH = "aidp-e2e-acceptance"
E2E_PROBE_PATH = "tests/orchestration/e2e_probe.txt"
E2E_PROBE_CONTENT = "AIDP_E2E_ACCEPTANCE_OK\n"

ServiceFactory = Callable[[Path, float], ExecutionService]


class AcceptanceHarness:
    """Creates a disposable READY repository and invokes the production runner.

    The orchestration modules remain loaded from the harness installation; all
    inspected AIDP state and all Codex changes are bound to the temporary Git
    repository. The source repository is observed only to prove its real AIDP
    paths were not changed.
    """

    def __init__(
        self,
        source_root: Path,
        *,
        timeout_seconds: float = 900.0,
        preserve_on_failure: bool = True,
        service_factory: ServiceFactory | None = None,
    ):
        self.source_root = source_root.resolve()
        self.timeout_seconds = timeout_seconds
        self.preserve_on_failure = preserve_on_failure
        self.service_factory = service_factory

    def run(self) -> AcceptanceResult:
        fixture_root = Path(tempfile.mkdtemp(prefix="aidp-acceptance-e2e-"))
        source_before = self._source_aidp_snapshot()
        runner_result: RunnerResult | None = None
        result_persisted = False
        audit_persisted = False
        failure_reason: str | None = None

        try:
            if self.service_factory is None and shutil.which("codex") is None:
                raise RuntimeError("Codex CLI is not available")
            self.build_fixture(fixture_root)
            if self._git(fixture_root, "branch", "--show-current") != E2E_BRANCH:
                raise RuntimeError("fixture repository is on the wrong branch")
            if self._git(fixture_root, "status", "--porcelain=v1"):
                raise RuntimeError("fixture repository is dirty before execution")

            repository = AIDPRepository(fixture_root)
            runtime_store = LocalRuntimeStore.for_repository(fixture_root)
            execution_service = self._execution_service(fixture_root)
            runner_result = AIDPRunner(
                repository,
                execution_service=execution_service,
                runtime_store=runtime_store,
            ).run_ready()

            execution_result = runner_result.execution_result
            if execution_result is not None:
                result_persisted = (runtime_store.root / "results" / f"{execution_result.execution_id}.json").is_file()
            audit_persisted = (runtime_store.root / "audit.jsonl").is_file()
            source_unchanged = self._source_aidp_snapshot() == source_before
            failure_reason = self._failure_reason(
                runner_result,
                fixture_root=fixture_root,
                result_persisted=result_persisted,
                audit_persisted=audit_persisted,
                source_unchanged=source_unchanged,
            )
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
            source_unchanged = self._source_aidp_snapshot() == source_before
            failure_reason = str(exc)

        passed = failure_reason is None
        cleanup_status = self._cleanup(fixture_root, passed)
        if cleanup_status is CleanupStatus.FAILED:
            passed = False
            failure_reason = failure_reason or "temporary repository cleanup failed"
        return AcceptanceResult(
            AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
            runner_result,
            result_persisted,
            audit_persisted,
            str(fixture_root),
            cleanup_status,
            source_unchanged,
            failure_reason,
        )

    @staticmethod
    def build_fixture(root: Path) -> None:
        task = root / ".ai" / "tasks" / "ready" / f"{E2E_TASK_ID}.md"
        codex_handoff = root / ".ai" / "handoff" / "TO-CODEX.md"
        architect_handoff = root / ".ai" / "handoff" / "TO-ARCHITECT.md"
        probe = root / E2E_PROBE_PATH
        task.parent.mkdir(parents=True, exist_ok=True)
        codex_handoff.parent.mkdir(parents=True, exist_ok=True)
        probe.parent.mkdir(parents=True, exist_ok=True)
        task.write_text(
            "---\n"
            f"task_id: {E2E_TASK_ID}\n"
            "phase: acceptance-e2e\n"
            f"allowed_scope: {E2E_PROBE_PATH}\n"
            "prohibited_actions: .ai/**, frontend/**, core/**, application/**\n"
            "validation_requirements: git diff --check\n"
            "product_owner_gate: false\n"
            "---\n"
            "Change only tests/orchestration/e2e_probe.txt so its exact content is:\n"
            "AIDP_E2E_ACCEPTANCE_OK\n"
            "Do not change, create, delete, or rename any other file.\n",
            encoding="utf-8",
        )
        codex_handoff.write_text(
            f"Status: OPEN\nCurrent AIDP Task: {E2E_TASK_ID}\nTask Status: READY\n",
            encoding="utf-8",
        )
        architect_handoff.write_text(
            f"Status: WAITING\nTask: {E2E_TASK_ID}\nTask Status: READY\n",
            encoding="utf-8",
        )
        probe.write_text("PENDING\n", encoding="utf-8")
        subprocess.run(("git", "init", "-q", "-b", E2E_BRANCH), cwd=root, check=True)
        subprocess.run(("git", "config", "user.name", "AIDP E2E Harness"), cwd=root, check=True)
        subprocess.run(("git", "config", "user.email", "aidp-e2e@localhost"), cwd=root, check=True)
        subprocess.run(("git", "add", "--", ".ai", "tests/orchestration/e2e_probe.txt"), cwd=root, check=True)
        subprocess.run(("git", "commit", "-q", "-m", "test: initialize AIDP E2E fixture"), cwd=root, check=True)

    def _execution_service(self, root: Path) -> ExecutionService:
        if self.service_factory is not None:
            return self.service_factory(root, self.timeout_seconds)
        return CodexExecutionService(repository_root=root, timeout_seconds=self.timeout_seconds)

    def _failure_reason(
        self,
        runner_result: RunnerResult,
        *,
        fixture_root: Path,
        result_persisted: bool,
        audit_persisted: bool,
        source_unchanged: bool,
    ) -> str | None:
        result = runner_result.execution_result
        checks = (
            (runner_result.status is RunnerStatus.EXECUTED, "runner did not execute exactly one task"),
            (result is not None, "Codex execution result is missing"),
            (result is not None and result.status is ExecutionStatus.SUCCESS, "Codex execution was not successful"),
            (result is not None and result.scope_compliance is ScopeCompliance.COMPLIANT, "scope is not compliant"),
            (result is not None and result.changed_files == (E2E_PROBE_PATH,), "changed files are not exactly the probe"),
            (result is not None and result.resulting_commit == result.start_commit, "repository commit changed during execution"),
            (self._git(fixture_root, "branch", "--show-current") == E2E_BRANCH, "fixture branch changed during execution"),
            (result is not None and bool(result.validation_results) and all(item.passed for item in result.validation_results), "validation did not pass"),
            ((fixture_root / E2E_PROBE_PATH).read_text(encoding="utf-8") == E2E_PROBE_CONTENT, "probe content is not exact"),
            (result_persisted, "execution result was not persisted"),
            (audit_persisted, "audit event was not persisted"),
            (source_unchanged, "source repository AIDP state changed"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        return None

    def _cleanup(self, root: Path, passed: bool) -> CleanupStatus:
        if not passed and self.preserve_on_failure:
            return CleanupStatus.PRESERVED
        try:
            self.remove_fixture(root)
        except OSError:
            return CleanupStatus.FAILED
        return CleanupStatus.CLEANED

    @staticmethod
    def remove_fixture(root: Path) -> None:
        """Remove only an explicit harness fixture, including read-only Git objects."""
        resolved = root.resolve()
        if not resolved.name.startswith("aidp-acceptance-e2e-"):
            raise ValueError("refusing to remove a non-harness directory")

        def remove_readonly(function, path: str, _error: BaseException) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)

        shutil.rmtree(resolved, onexc=remove_readonly)

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
    def _git(root: Path, *args: str) -> str:
        return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def serialize_acceptance_result(result: AcceptanceResult) -> str:
    return json.dumps({"acceptance_result": asdict(result)}, default=_json_default, sort_keys=True)


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")
