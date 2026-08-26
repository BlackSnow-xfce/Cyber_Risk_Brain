from __future__ import annotations

import json
import subprocess
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

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
    SubprocessRunner,
    WindowsVisibleCodexRunner,
    _VISIBLE_ERROR_CODES,
    serialize_execution_result,
)
from aidp_orchestration.launcher import CodexLauncher
from aidp_orchestration.visible_codex import READINESS_ERROR_CODES


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


def test_subprocess_runner_never_enables_shell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def run(args, **kwargs):
        observed.update(kwargs)
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", run)
    SubprocessRunner().run(("node.exe", "codex.js"), cwd=tmp_path, timeout_seconds=1.0)
    assert observed.get("shell", False) is False
    assert observed.get("text", False) is False
    assert "encoding" not in observed


def test_subprocess_runner_decodes_utf8_independently_of_windows_charmap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = '{"message":"Grüße — 完了"}\n'.encode("utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=output, stderr=b""),
    )
    result = SubprocessRunner().run(("codex-test.exe",), cwd=tmp_path, timeout_seconds=1.0)
    assert result.stdout == '{"message":"Grüße — 完了"}\n'
    assert result.error is None


def test_subprocess_runner_rejects_non_utf8_output_with_safe_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=b'{"message":"\x81"}\n', stderr=b""),
    )
    result = SubprocessRunner().run(("codex-test.exe",), cwd=tmp_path, timeout_seconds=1.0)
    assert result.error == "process output decode error: stdout is not valid UTF-8 at byte 12"
    assert "�" in result.stdout


class FakeVisibleProcess:
    def __init__(self, *, output=(b'{"type":"completed"}\n', b"diagnostic"), error=None):
        self.output = output
        self.error = error
        self.returncode = 0
        self.killed = False
        self.waited = False
        self.stderr = BytesIO(b"AIDP_VISIBLE_CONSOLE_READY_V2\n")

    def communicate(self, timeout=None):
        if self.error is not None and not self.killed:
            raise self.error
        return self.output

    def kill(self):
        self.killed = True

    def wait(self):
        self.waited = True


def test_visible_windows_runner_uses_trusted_relay_and_separate_argv(tmp_path: Path) -> None:
    observed = {}
    process = FakeVisibleProcess()
    def popen(args, **kwargs):
        observed["args"] = tuple(args)
        observed.update(kwargs)
        return process
    original = ("node.exe", "codex.js", "exec", "prompt with spaces")
    outcome = WindowsVisibleCodexRunner(platform="nt", popen=popen).run(
        original, cwd=tmp_path, timeout_seconds=10,
    )
    assert observed["args"][-len(original):] == original
    assert observed["args"][-len(original) - 1] == "--"
    assert observed["shell"] is False
    assert observed["creationflags"] == getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
    assert observed["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert observed["startupinfo"].wShowWindow == 1
    assert outcome.returncode == 0
    assert outcome.stdout == '{"type":"completed"}\n'
    assert outcome.stderr == "diagnostic"


def test_visible_windows_runner_requires_relay_readiness(tmp_path: Path) -> None:
    process = FakeVisibleProcess()
    process.stderr = BytesIO(b"AIDP_VISIBLE_CONSOLE_ERROR_V2:WINDOW_OFFSCREEN\n")
    outcome = WindowsVisibleCodexRunner(platform="nt", popen=lambda *a, **k: process).run(
        ("codex.exe",), cwd=tmp_path, timeout_seconds=1,
    )
    assert outcome.error == "visible Codex console readiness failed: WINDOW_OFFSCREEN"
    assert process.killed


def test_parent_and_relay_readiness_allowlists_match() -> None:
    assert _VISIBLE_ERROR_CODES == READINESS_ERROR_CODES


@pytest.mark.parametrize(
    "readiness",
    (
        b"AIDP_VISIBLE_CONSOLE_ERROR_V2:UNKNOWN\n",
        b"AIDP_VISIBLE_CONSOLE_ERROR_V2:WINDOW_OFFSCREEN:prompt\n",
        b"visible Codex relay failed: RuntimeError\n",
        b"AIDP_VISIBLE_CONSOLE_ERROR_V2:\xff\n",
        b"",
    ),
)
def test_visible_windows_runner_normalizes_untrusted_readiness(readiness: bytes, tmp_path: Path) -> None:
    process = FakeVisibleProcess()
    process.stderr = BytesIO(readiness)
    outcome = WindowsVisibleCodexRunner(platform="nt", popen=lambda *a, **k: process).run(
        ("codex.exe", "secret prompt"), cwd=tmp_path, timeout_seconds=1,
    )
    assert outcome.error == "visible Codex console readiness failed: READINESS_PROTOCOL_INVALID"
    assert "secret prompt" not in outcome.error
    assert process.killed


def test_visible_windows_runner_waits_for_readiness_before_communicating(tmp_path: Path) -> None:
    order: list[str] = []

    class ReadyStream(BytesIO):
        def readline(self, *args, **kwargs):
            order.append("ready")
            return super().readline(*args, **kwargs)

    process = FakeVisibleProcess()
    process.stderr = ReadyStream(b"AIDP_VISIBLE_CONSOLE_READY_V2\n")
    original_communicate = process.communicate

    def communicate(timeout=None):
        order.append("communicate")
        return original_communicate(timeout)

    process.communicate = communicate
    outcome = WindowsVisibleCodexRunner(platform="nt", popen=lambda *a, **k: process).run(
        ("codex.exe",), cwd=tmp_path, timeout_seconds=1,
    )
    assert outcome.returncode == 0
    assert order == ["ready", "communicate"]


def test_visible_windows_runner_timeout_kills_relay_job_owner(tmp_path: Path) -> None:
    process = FakeVisibleProcess(error=subprocess.TimeoutExpired(("relay",), 1))
    outcome = WindowsVisibleCodexRunner(platform="nt", popen=lambda *a, **k: process).run(
        ("codex.exe",), cwd=tmp_path, timeout_seconds=1,
    )
    assert outcome.timed_out and outcome.error == "timeout"
    assert process.killed


def test_visible_windows_runner_keyboard_interrupt_kills_relay(tmp_path: Path) -> None:
    process = FakeVisibleProcess(error=KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        WindowsVisibleCodexRunner(platform="nt", popen=lambda *a, **k: process).run(
            ("codex.exe",), cwd=tmp_path, timeout_seconds=1,
        )
    assert process.killed and process.waited


def service(tmp_path: Path, runner: FakeRunner, git: FakeGit | None = None) -> CodexExecutionService:
    return CodexExecutionService(
        runner=runner,
        git=git or FakeGit(),
        lock=ExecutionLock(tmp_path / "execution.lock"),
        launcher=CodexLauncher(("codex-test.exe",)),
    )


def test_valid_execution_runs_bound_codex_request_and_validators(tmp_path: Path) -> None:
    runner = success_runner()
    result = service(tmp_path, runner).execute(request(tmp_path))
    assert result.status is ExecutionStatus.SUCCESS
    assert result.scope_compliance is ScopeCompliance.COMPLIANT
    assert result.is_review_ready
    command = runner.calls[0]
    assert command[:-1] == (
        "codex-test.exe",
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--cd",
        str(tmp_path),
        "--sandbox",
        "workspace-write",
    )
    assert "task_id=TASK-9000" in command[-1]
    assert "execution_id=execution-1" in command[-1]


def test_autonomous_command_is_unattended_but_workspace_scoped(tmp_path: Path) -> None:
    runner = success_runner()
    service(tmp_path, runner).execute(request(tmp_path))
    command = runner.calls[0]
    assert command[1:5] == ("--ask-for-approval", "never", "exec", "--json")
    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert "--approve-for-me" not in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert "danger-full-access" not in command


def test_visible_runner_is_codex_only_and_validators_keep_headless_runner(tmp_path: Path) -> None:
    codex = FakeRunner([ProcessOutcome(0, '{"type":"completed"}\n', "")])
    validators = FakeRunner([ProcessOutcome(0, "", "")])
    result = CodexExecutionService(
        runner=validators,
        codex_runner=codex,
        git=FakeGit(),
        lock=ExecutionLock(tmp_path / "execution.lock"),
        launcher=CodexLauncher(("codex-test.exe",)),
    ).execute(request(tmp_path))
    assert result.status is ExecutionStatus.SUCCESS
    assert len(codex.calls) == 1
    assert len(validators.calls) == 1


@pytest.mark.parametrize(
    ("git", "expected"),
    (
        (FakeGit(branch="other"), ExecutionStatus.BLOCKED),
        (FakeGit(head="different"), ExecutionStatus.STALE_EXECUTION),
        (FakeGit(clean=False, changed=("outside.py",)), ExecutionStatus.BLOCKED),
    ),
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


def test_executor_admits_only_dirty_paths_within_request_scope(tmp_path: Path) -> None:
    authorized = service(
        tmp_path,
        success_runner(),
        FakeGit(clean=False, changed=("aidp_orchestration/continued.py",)),
    ).execute(request(tmp_path))
    assert authorized.status is ExecutionStatus.SUCCESS

    blocked_runner = FakeRunner([])
    blocked = service(
        tmp_path,
        blocked_runner,
        FakeGit(clean=False, changed=("aidp_orchestration/continued.py", "frontend/unauthorized.tsx")),
    ).execute(request(tmp_path))
    assert blocked.status is ExecutionStatus.BLOCKED
    assert blocked_runner.calls == []


def test_parallel_lock_blocks_second_execution(tmp_path: Path) -> None:
    lock = ExecutionLock(tmp_path / "execution.lock")
    first = request(tmp_path)
    lock.acquire(first)
    try:
        result = CodexExecutionService(
            runner=FakeRunner([]),
            git=FakeGit(),
            lock=lock,
            launcher=CodexLauncher(("codex-test.exe",)),
        ).execute(first)
        assert result.status is ExecutionStatus.BLOCKED
    finally:
        lock.release()


def test_default_lock_is_git_internal_and_locally_exclusive(tmp_path: Path) -> None:
    subprocess.run(("git", "init", "-q"), cwd=tmp_path, check=True)
    lock = ExecutionLock.for_repository(tmp_path)
    assert lock.path.is_relative_to(tmp_path / ".git")
    lock.acquire(request(tmp_path))
    try:
        with pytest.raises(RuntimeError, match="already running"):
            ExecutionLock.for_repository(tmp_path).acquire(request(tmp_path))
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


def test_readiness_predicate_code_is_preserved_in_execution_result(tmp_path: Path) -> None:
    reason = "visible Codex console readiness failed: WINDOW_OFFSCREEN"
    result = service(tmp_path, FakeRunner([ProcessOutcome(125, "", "", error=reason)])).execute(request(tmp_path))
    assert result.status is ExecutionStatus.ERROR
    assert result.failure_reason == reason
    assert json.loads(serialize_execution_result(result))["codex_execution_result"]["failure_reason"] == reason


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
    result = CodexExecutionService(
        runner=FakeRunner([ProcessOutcome(3, "", "")]),
        git=FakeGit(),
        lock=ExecutionLock(lock_path),
        launcher=CodexLauncher(("codex-test.exe",)),
    ).execute(request(tmp_path))
    assert result.status is ExecutionStatus.ERROR
    assert not lock_path.exists()


def test_output_decode_failure_becomes_error_and_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=b'{"message":"\x81"}\n', stderr=b""),
    )
    lock_path = tmp_path / "execution.lock"
    result = CodexExecutionService(
        runner=SubprocessRunner(),
        git=FakeGit(),
        lock=ExecutionLock(lock_path),
        launcher=CodexLauncher(("codex-test.exe",)),
    ).execute(request(tmp_path))
    assert result.status is ExecutionStatus.ERROR
    assert result.failure_reason == "process output decode error: stdout is not valid UTF-8 at byte 12"
    assert not lock_path.exists()


def test_unexpected_process_adapter_failure_becomes_error_and_releases_lock(tmp_path: Path) -> None:
    class ExplodingRunner:
        def run(self, args, *, cwd, timeout_seconds):
            raise AssertionError("unexpected adapter failure")

    lock_path = tmp_path / "execution.lock"
    result = CodexExecutionService(
        runner=ExplodingRunner(), git=FakeGit(), lock=ExecutionLock(lock_path),
        launcher=CodexLauncher(("codex-test.exe",)),
    ).execute(request(tmp_path))
    assert result.status is ExecutionStatus.ERROR
    assert result.failure_reason == "unexpected execution failure: AssertionError"
    assert not lock_path.exists()


def test_malformed_codex_jsonl_is_explicit_error(tmp_path: Path) -> None:
    result = service(tmp_path, FakeRunner([ProcessOutcome(0, '{"ok":true}\nmalformed', "")])).execute(request(tmp_path))
    assert result.status is ExecutionStatus.ERROR
    assert result.failure_reason == "Codex returned malformed JSONL"
