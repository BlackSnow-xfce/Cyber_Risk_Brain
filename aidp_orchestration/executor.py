"""Fail-closed execution boundary for a single Codex invocation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Sequence

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
_VISIBLE_READY_TOKEN = b"AIDP_VISIBLE_CONSOLE_READY_V2\n"
_VISIBLE_ERROR_PREFIX = b"AIDP_VISIBLE_CONSOLE_ERROR_V2:"
_VISIBLE_PROTOCOL_ERROR = "READINESS_PROTOCOL_INVALID"
_VISIBLE_ERROR_CODES = frozenset({
    "NO_CONSOLE_HWND",
    "WINDOW_NOT_TOP_LEVEL",
    "MESSAGE_ONLY_OR_PSEUDOCONSOLE_WINDOW",
    "WINDOW_THREAD_UNAVAILABLE",
    "WINDOW_DESKTOP_UNAVAILABLE",
    "INPUT_DESKTOP_UNAVAILABLE",
    "DESKTOP_NAME_UNAVAILABLE",
    "DESKTOP_MISMATCH",
    "WINDOW_PRESENTATION_FAILED",
    "WINDOW_NOT_VISIBLE",
    "WINDOW_MINIMIZED",
    "VISIBLE_MONITOR_UNAVAILABLE",
    "WINDOW_BOUNDS_UNAVAILABLE",
    "MONITOR_WORK_AREA_UNAVAILABLE",
    "WINDOW_OFFSCREEN",
    "CONOUT_UNAVAILABLE",
})


class SubprocessRunner:
    """Small adapter around subprocess; callers can inject a deterministic fake."""

    def __init__(self, *, max_capture_bytes: int | None = None) -> None:
        if max_capture_bytes is not None and max_capture_bytes < 1:
            raise ValueError("max_capture_bytes must be positive")
        self.max_capture_bytes = max_capture_bytes

    def run(self, args: Sequence[str], *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        if self.max_capture_bytes is not None:
            return self._run_bounded(args, cwd=cwd, timeout_seconds=timeout_seconds)
        process_started_at = datetime.now(timezone.utc)
        try:
            completed = subprocess.run(
                tuple(args),
                cwd=cwd,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            process_completed_at = datetime.now(timezone.utc)
            stdout, stdout_error = _decode_process_output(exc.stdout, "stdout")
            stderr, stderr_error = _decode_process_output(exc.stderr, "stderr")
            return ProcessOutcome(
                None,
                stdout,
                stderr,
                timed_out=True,
                error=stdout_error or stderr_error or "timeout",
                process_started_at=process_started_at, process_completed_at=process_completed_at,
            )
        except OSError as exc:
            return ProcessOutcome(None, "", "", error=f"process error: {exc.__class__.__name__}")
        process_completed_at = datetime.now(timezone.utc)
        stdout, stdout_error = _decode_process_output(completed.stdout, "stdout")
        stderr, stderr_error = _decode_process_output(completed.stderr, "stderr")
        return ProcessOutcome(
            completed.returncode,
            stdout,
            stderr,
            error=stdout_error or stderr_error,
            process_started_at=process_started_at, process_completed_at=process_completed_at,
        )

    def _run_bounded(self, args: Sequence[str], *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        started_ns = time.time_ns()
        try:
            process = subprocess.Popen(
                tuple(args), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL, shell=False,
            )
        except OSError as exc:
            return ProcessOutcome(None, "", "", error=f"process error: {exc.__class__.__name__}")
        process_started_at = datetime.now(timezone.utc)
        identity = f"pid:{process.pid}:started_ns:{started_ns}"
        limit = self.max_capture_bytes or 1
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        overflow = threading.Event()

        def drain(name: str, stream) -> None:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    return
                remaining = limit - len(buffers[name])
                if remaining > 0:
                    buffers[name].extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
                    return

        readers = [
            threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
            threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
        ]
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + timeout_seconds
        timed_out = False
        while process.poll() is None and not overflow.is_set():
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.01)
        if overflow.is_set() or timed_out:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        else:
            process.wait()
        for reader in readers:
            reader.join(timeout=1.0)
        process_completed_at = datetime.now(timezone.utc)
        stdout, stdout_error = _decode_process_output(bytes(buffers["stdout"]), "stdout")
        stderr, stderr_error = _decode_process_output(bytes(buffers["stderr"]), "stderr")
        if overflow.is_set():
            return ProcessOutcome(
                process.returncode, "", "", error="process output limit exceeded",
                process_identity=identity, output_limit_exceeded=True,
                process_started_at=process_started_at, process_completed_at=process_completed_at,
            )
        if timed_out:
            return ProcessOutcome(
                None, stdout, stderr, timed_out=True,
                error=stdout_error or stderr_error or "timeout", process_identity=identity,
                process_started_at=process_started_at, process_completed_at=process_completed_at,
            )
        return ProcessOutcome(
            process.returncode, stdout, stderr, error=stdout_error or stderr_error,
            process_identity=identity,
            process_started_at=process_started_at, process_completed_at=process_completed_at,
        )


class WindowsVisibleCodexRunner:
    """Runs the trusted relay in a visible console while retaining captured output."""

    def __init__(
        self,
        *,
        platform: str | None = None,
        popen=subprocess.Popen,
        relay_root_resolver: Callable[[], Path] | None = None,
    ):
        self.platform = platform or os.name
        self.popen = popen
        self.relay_root_resolver = relay_root_resolver or _authoritative_relay_root

    def run(self, args: Sequence[str], *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        if self.platform != "nt":
            return ProcessOutcome(None, "", "", error="visible Codex console is only supported on Windows")
        try:
            relay_root = _validated_relay_root(self.relay_root_resolver())
        except (OSError, RuntimeError, ValueError):
            return ProcessOutcome(None, "", "", error="visible Codex relay start failed: RELAY_ROOT_INVALID")
        relay = (sys.executable, "-m", "aidp_orchestration.visible_codex", "--", *tuple(args))
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
        try:
            process = self.popen(
                relay,
                cwd=relay_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010),
                startupinfo=startupinfo,
            )
            if process.stderr is None:
                process.kill()
                process.wait()
                return ProcessOutcome(None, "", "", error="visible Codex console readiness channel is unavailable")
            readiness: list[bytes] = []
            ready_reader = threading.Thread(target=lambda: readiness.append(process.stderr.readline()), daemon=True)
            started_at = time.monotonic()
            ready_reader.start()
            try:
                ready_reader.join(timeout_seconds)
            except KeyboardInterrupt:
                process.kill()
                process.wait()
                raise
            if ready_reader.is_alive():
                process.kill()
                process.wait()
                return ProcessOutcome(None, "", "", timed_out=True, error="visible Codex console readiness timed out")
            ready_line = readiness[0] if readiness else b""
            if ready_line != _VISIBLE_READY_TOKEN:
                process.kill()
                stdout_value, stderr_value = process.communicate()
                stderr_value = ready_line + (stderr_value or b"")
                stdout, stdout_error = _decode_process_output(stdout_value, "stdout")
                stderr, stderr_error = _decode_process_output(stderr_value, "stderr")
                readiness_code = _readiness_error_code(ready_line)
                return ProcessOutcome(
                    process.returncode, stdout, stderr,
                    error=f"visible Codex console readiness failed: {readiness_code}",
                )
            remaining_timeout = max(0.0, timeout_seconds - (time.monotonic() - started_at))
            try:
                stdout_value, stderr_value = process.communicate(timeout=remaining_timeout)
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


def _authoritative_relay_root() -> Path:
    """Return the checkout/install root containing the loaded relay package."""

    package_directory = Path(__file__).resolve().parent
    relay_module = package_directory / "visible_codex.py"
    package_marker = package_directory / "__init__.py"
    if (
        package_directory.name != "aidp_orchestration"
        or not package_marker.is_file()
        or not relay_module.is_file()
    ):
        raise RuntimeError("authoritative visible relay package is unavailable")
    return package_directory.parent


def _validated_relay_root(candidate: Path) -> Path:
    relay_root = Path(candidate).resolve()
    loaded_relay = (Path(__file__).resolve().parent / "visible_codex.py").resolve()
    candidate_relay = relay_root / "aidp_orchestration" / "visible_codex.py"
    if not relay_root.is_dir() or not candidate_relay.is_file() or candidate_relay.resolve() != loaded_relay:
        raise RuntimeError("authoritative visible relay root is invalid")
    return relay_root


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
                external_requirements = tuple(
                    value for value in request.validation_requirements
                    if value.strip().lower() not in {
                        "exact rework-2 scope guard", "exact rework-3 scope guard",
                    }
                )
                validations = self.validator_registry.run(
                    external_requirements,
                    root=root,
                    runner=self.runner,
                    timeout_seconds=self.timeout_seconds,
                )
                if len(external_requirements) != len(request.validation_requirements):
                    validations = (*validations, ValidationResult(
                        next(
                            value for value in request.validation_requirements
                            if value.strip().lower() in {
                                "exact rework-2 scope guard", "exact rework-3 scope guard",
                            }
                        ), True,
                        "changed paths comply with the authorized ReworkContract scope",
                    ))
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


def _readiness_error_code(line: bytes) -> str:
    if not line.endswith(b"\n") or not line.startswith(_VISIBLE_ERROR_PREFIX):
        return _VISIBLE_PROTOCOL_ERROR
    encoded = line[len(_VISIBLE_ERROR_PREFIX):-1]
    try:
        code = encoded.decode("ascii", errors="strict")
    except UnicodeDecodeError:
        return _VISIBLE_PROTOCOL_ERROR
    return code if code in _VISIBLE_ERROR_CODES else _VISIBLE_PROTOCOL_ERROR
