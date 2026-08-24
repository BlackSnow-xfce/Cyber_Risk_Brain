"""Fail-closed execution boundary for a single Codex invocation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .contracts import (
    CodexExecutionRequest,
    CodexExecutionResult,
    ExecutionStatus,
    ScopeCompliance,
    ValidationResult,
)
from .repository import AIDPRepository
from .validators import ValidatorRegistry
from .executor_types import ProcessOutcome, ProcessRunner
from .launcher import CodexLauncher, resolve_codex_launcher
from .worktree import worktree_admission_reason


class SubprocessRunner:
    """Small adapter around subprocess; callers can inject a deterministic fake."""

    def run(self, args: Sequence[str], *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        try:
            completed = subprocess.run(
                tuple(args),
                cwd=cwd,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout, stdout_error = _decode_process_output(exc.stdout, "stdout")
            stderr, stderr_error = _decode_process_output(exc.stderr, "stderr")
            return ProcessOutcome(
                None,
                stdout,
                stderr,
                timed_out=True,
                error=stdout_error or stderr_error or "timeout",
            )
        except OSError as exc:
            return ProcessOutcome(None, "", "", error=f"process error: {exc.__class__.__name__}")
        stdout, stdout_error = _decode_process_output(completed.stdout, "stdout")
        stderr, stderr_error = _decode_process_output(completed.stderr, "stderr")
        return ProcessOutcome(
            completed.returncode,
            stdout,
            stderr,
            error=stdout_error or stderr_error,
        )


class WindowsVisibleCodexRunner:
    """Runs the trusted relay in a visible console while retaining captured output."""

    def __init__(self, *, platform: str | None = None, popen=subprocess.Popen):
        self.platform = platform or os.name
        self.popen = popen

    def run(self, args: Sequence[str], *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        if self.platform != "nt":
            return ProcessOutcome(None, "", "", error="visible Codex console is only supported on Windows")
        relay = (sys.executable, "-m", "aidp_orchestration.visible_codex", "--", *tuple(args))
        try:
            process = self.popen(
                relay,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010),
            )
            try:
                stdout_value, stderr_value = process.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_value, stderr_value = process.communicate()
                stdout, stdout_error = _decode_process_output(stdout_value, "stdout")
                stderr, stderr_error = _decode_process_output(stderr_value, "stderr")
                return ProcessOutcome(
                    None, stdout, stderr, timed_out=True,
                    error=stdout_error or stderr_error or "timeout",
                )
            except KeyboardInterrupt:
                process.kill()
                process.wait()
                raise
        except OSError as exc:
            return ProcessOutcome(None, "", "", error=f"visible process error: {exc.__class__.__name__}")
        stdout, stdout_error = _decode_process_output(stdout_value, "stdout")
        stderr, stderr_error = _decode_process_output(stderr_value, "stderr")
        return ProcessOutcome(
            process.returncode, stdout, stderr, error=stdout_error or stderr_error,
        )


class GitInspector:
    def __init__(self, root: Path):
        self.root = root

    def branch(self) -> str:
        return self._read("git", "branch", "--show-current")

    def head(self) -> str:
        return self._read("git", "rev-parse", "HEAD")

    def is_clean(self) -> bool:
        return not self._read("git", "status", "--porcelain=v1")

    def changed_files(self) -> tuple[str, ...]:
        paths: set[str] = set()
        commands = (
            ("git", "diff", "--no-renames", "--name-only", "-z"),
            ("git", "diff", "--cached", "--no-renames", "--name-only", "-z"),
            ("git", "ls-files", "--others", "--exclude-standard", "-z"),
        )
        for command in commands:
            paths.update(self._read_null_paths(*command))
        return tuple(sorted(paths))

    def _read_null_paths(self, *args: str) -> tuple[str, ...]:
        output = subprocess.check_output(args, cwd=self.root)
        if not output:
            return ()
        if not output.endswith(b"\0"):
            raise RuntimeError("Git returned a malformed NUL-separated path list")
        decoded = output.decode("utf-8", errors="strict")
        return tuple(decoded[:-1].split("\0"))

    def _read(self, *args: str) -> str:
        return subprocess.check_output(args, cwd=self.root, text=True).strip()


class ExecutionLock:
    """Exclusive local lock; it is removed on every release path.

    This provides exclusivity only for executions sharing this local Git
    repository context. It is not a global or distributed lock.
    """

    def __init__(self, path: Path):
        self.path = path
        self._owned = False

    @classmethod
    def for_repository(cls, root: Path) -> "ExecutionLock":
        git_path = subprocess.check_output(
            ("git", "rev-parse", "--git-path", "aidp-orchestration/execution.lock"),
            cwd=root,
            text=True,
        ).strip()
        path = Path(git_path)
        return cls(path if path.is_absolute() else root / path)

    def acquire(self, request: CodexExecutionRequest) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError("another Codex execution is already running") from exc
        try:
            os.write(descriptor, f"{request.execution_id}\n".encode("utf-8"))
        finally:
            os.close(descriptor)
        self._owned = True

    def release(self) -> None:
        if self._owned:
            self.path.unlink(missing_ok=True)
            self._owned = False


class CodexExecutionService:
    """Runs at most one explicitly requested Codex execution and never approves it.

    ``resulting_commit`` is the repository HEAD observed after the process;
    this service never creates a commit, so it is never a synthetic identity.
    """

    def __init__(
        self,
        *,
        runner: ProcessRunner | None = None,
        codex_runner: ProcessRunner | None = None,
        git: GitInspector | None = None,
        validator_registry: ValidatorRegistry | None = None,
        lock: ExecutionLock | None = None,
        repository_root: Path | None = None,
        timeout_seconds: float = 900.0,
        launcher: CodexLauncher | None = None,
    ):
        self.runner = runner or SubprocessRunner()
        self.codex_runner = codex_runner or (
            runner
            if runner is not None
            else WindowsVisibleCodexRunner()
            if os.name == "nt"
            else self.runner
        )
        self.git = git
        self.validator_registry = validator_registry or ValidatorRegistry()
        self.timeout_seconds = timeout_seconds
        self._lock = lock
        self.repository_root = repository_root.resolve() if repository_root is not None else None
        self.launcher = launcher

    def execute(self, request: CodexExecutionRequest) -> CodexExecutionResult:
        root = Path(request.repository).resolve()
        if self.repository_root is not None and root != self.repository_root:
            return self._result(request, request.expected_head, ExecutionStatus.BLOCKED, "request repository does not match execution boundary", ScopeCompliance.NOT_EVALUATED)
        git = self.git or GitInspector(root)
        start_commit = self._safe_head(git, request.expected_head)
        try:
            self._preflight(request, root, git)
        except _StaleExecution as exc:
            return self._result(request, start_commit, ExecutionStatus.STALE_EXECUTION, str(exc), ScopeCompliance.NOT_EVALUATED)
        except Exception as exc:
            return self._result(request, start_commit, ExecutionStatus.BLOCKED, str(exc), ScopeCompliance.NOT_EVALUATED)

        try:
            launcher = self.launcher or resolve_codex_launcher()
        except Exception as exc:
            return self._result(request, start_commit, ExecutionStatus.BLOCKED, str(exc), ScopeCompliance.NOT_EVALUATED)

        try:
            lock = self._lock or ExecutionLock.for_repository(root)
            lock.acquire(request)
        except Exception as exc:
            return self._result(request, start_commit, ExecutionStatus.BLOCKED, str(exc), ScopeCompliance.NOT_EVALUATED)

        try:
            outcome = self.codex_runner.run(
                self._codex_command(request, launcher), cwd=root,
                timeout_seconds=self.timeout_seconds,
            )
            if outcome.timed_out:
                return self._result(request, start_commit, ExecutionStatus.ERROR, "Codex process timed out", ScopeCompliance.NOT_EVALUATED)
            if outcome.error:
                return self._result(request, start_commit, ExecutionStatus.ERROR, outcome.error, ScopeCompliance.NOT_EVALUATED)
            if outcome.returncode != 0:
                return self._result(request, start_commit, ExecutionStatus.ERROR, f"Codex exited with code {outcome.returncode}", ScopeCompliance.NOT_EVALUATED)
            if not _valid_json_lines(outcome.stdout):
                return self._result(request, start_commit, ExecutionStatus.ERROR, "Codex returned malformed JSONL", ScopeCompliance.NOT_EVALUATED)

            try:
                changed = git.changed_files()
                resulting_commit = git.head()
            except (OSError, RuntimeError, UnicodeError, subprocess.SubprocessError) as exc:
                return self._result(request, start_commit, ExecutionStatus.ERROR, f"git inspection failed: {exc.__class__.__name__}", ScopeCompliance.NOT_EVALUATED)
            scope = AIDPRepository(root).validate_scope(request, changed)
            if scope is not ScopeCompliance.COMPLIANT:
                return self._result(request, start_commit, ExecutionStatus.SCOPE_VIOLATION, "changed files exceed the declared scope", scope, changed, resulting_commit)

            try:
                validations = self.validator_registry.run(
                    request.validation_requirements,
                    root=root,
                    runner=self.runner,
                    timeout_seconds=self.timeout_seconds,
                )
            except Exception as exc:
                return self._result(request, start_commit, ExecutionStatus.ERROR, f"validation execution failed: {exc.__class__.__name__}", scope, changed, resulting_commit)
            if not all(item.passed for item in validations):
                return self._result(request, start_commit, ExecutionStatus.TEST_FAILED, "one or more validations failed", scope, changed, resulting_commit, validations)
            return self._result(request, start_commit, ExecutionStatus.SUCCESS, None, scope, changed, resulting_commit, validations)
        except Exception as exc:
            return self._result(
                request,
                start_commit,
                ExecutionStatus.ERROR,
                f"unexpected execution failure: {exc.__class__.__name__}",
                ScopeCompliance.NOT_EVALUATED,
            )
        finally:
            lock.release()

    def _preflight(self, request: CodexExecutionRequest, root: Path, git: GitInspector) -> None:
        if root != Path(request.repository).resolve():
            raise ValueError("request repository does not match execution root")
        if not request.task_path.resolve().is_relative_to(root):
            raise ValueError("task path is outside the repository")
        if not request.task_path.exists():
            raise ValueError("task path does not exist")
        if not request.prohibited_actions:
            raise ValueError("prohibited actions must be explicit")
        unknown = self.validator_registry.unknown(request.validation_requirements)
        if unknown:
            raise ValueError(f"unknown validation requirement: {unknown[0]}")
        if git.branch() != request.branch:
            raise ValueError("branch does not match execution request")
        if git.head() != request.expected_head:
            raise _StaleExecution("repository HEAD is stale")
        if not git.is_clean():
            changed = git.changed_files()
            if not changed:
                raise ValueError("worktree dirty paths could not be established")
            worktree_reason = worktree_admission_reason(
                lambda: changed,
                allowed_scope=request.allowed_scope,
                prohibited_actions=request.prohibited_actions,
            )
            if worktree_reason is not None:
                raise ValueError(worktree_reason)

    @staticmethod
    def _codex_command(request: CodexExecutionRequest, launcher: CodexLauncher) -> tuple[str, ...]:
        prompt = (
            "Execute only the repository task described by the provided task file.\n"
            f"task_id={request.task_id}\n"
            f"task_path={request.task_path}\n"
            f"phase={request.phase}\n"
            f"expected_head={request.expected_head}\n"
            f"allowed_scope={','.join(request.allowed_scope)}\n"
            f"prohibited_actions={','.join(request.prohibited_actions)}\n"
            f"validation_requirements={','.join(request.validation_requirements)}\n"
            f"execution_id={request.execution_id}\n"
            "Repository contracts and the task file are authoritative; do not approve or create tasks."
        )
        return launcher.argv_prefix + (
            "--ask-for-approval", "never", "exec", "--json", "--cd", request.repository,
            "--sandbox", "workspace-write", prompt,
        )

    @staticmethod
    def _safe_head(git: GitInspector, fallback: str) -> str:
        try:
            return git.head()
        except Exception:
            return fallback

    @staticmethod
    def _result(
        request: CodexExecutionRequest,
        start_commit: str,
        status: ExecutionStatus,
        reason: str | None,
        scope: ScopeCompliance,
        changed: tuple[str, ...] = (),
        resulting: str | None = None,
        validations: tuple[ValidationResult, ...] = (),
    ) -> CodexExecutionResult:
        return CodexExecutionResult(request.execution_id, request.task_id, start_commit, resulting, changed, validations, status, reason, scope)


class _StaleExecution(RuntimeError):
    pass


def serialize_execution_result(result: CodexExecutionResult) -> str:
    """Stable JSON envelope; process output and prompts are deliberately excluded."""
    payload = asdict(result)
    payload["status"] = result.status.value
    payload["scope_compliance"] = result.scope_compliance.value
    return json.dumps({"codex_execution_result": payload}, sort_keys=True)


def _valid_json_lines(output: str) -> bool:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return False
    try:
        return all(isinstance(json.loads(line), (dict, list)) for line in lines)
    except json.JSONDecodeError:
        return False


def _decode_process_output(value: object, stream: str) -> tuple[str, str | None]:
    if value is None:
        return "", None
    if isinstance(value, str):
        return value, None
    if not isinstance(value, bytes):
        return "", f"process output capture error: unexpected {stream} type"
    try:
        return value.decode("utf-8", errors="strict"), None
    except UnicodeDecodeError as exc:
        diagnostic = value.decode("utf-8", errors="replace")
        return diagnostic, f"process output decode error: {stream} is not valid UTF-8 at byte {exc.start}"
