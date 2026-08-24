from __future__ import annotations

from pathlib import Path

import pytest

from aidp_orchestration.executor_types import ProcessOutcome
from aidp_orchestration.validators import (
    ValidatorExecutableError,
    ValidatorRegistry,
    resolve_validator_command,
)


class RecordingRunner:
    def __init__(self, outcome: ProcessOutcome):
        self.outcome = outcome
        self.commands: list[tuple[str, ...]] = []

    def run(self, args, *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        self.commands.append(tuple(args))
        return self.outcome


def resolver(files: dict[str, Path]):
    return lambda name: str(files[name]) if name in files else None


@pytest.mark.parametrize(
    ("name", "resolved_name"),
    (("npm", "npm.cmd"), ("npx", "npx.cmd"), ("git", "git.exe")),
)
def test_windows_resolves_safe_executable_forms(
    tmp_path: Path, name: str, resolved_name: str,
) -> None:
    target = tmp_path / resolved_name
    target.write_text("launcher", encoding="utf-8")
    command = resolve_validator_command(
        (name, "arg one", "--flag"),
        platform="nt",
        which=resolver({resolved_name: target}),
    )
    assert command == (str(target.resolve()), "arg one", "--flag")


def test_windows_prefers_native_executable_over_cmd(tmp_path: Path) -> None:
    native, shim = tmp_path / "npm.exe", tmp_path / "npm.cmd"
    native.write_text("native", encoding="utf-8")
    shim.write_text("shim", encoding="utf-8")
    command = resolve_validator_command(
        ("npm", "test"), platform="nt", which=resolver({"npm.exe": native, "npm.cmd": shim}),
    )
    assert command[0] == str(native.resolve())


def test_non_windows_command_is_unchanged() -> None:
    command = ("npm", "test", "--", "--run")
    assert resolve_validator_command(command, platform="posix", which=lambda _: None) is command


def test_missing_or_untrusted_windows_executable_fails_closed(tmp_path: Path) -> None:
    script = tmp_path / "npm.ps1"
    script.write_text("script", encoding="utf-8")
    with pytest.raises(ValidatorExecutableError):
        resolve_validator_command(("npm", "test"), platform="nt", which=resolver({"npm.cmd": script}))


def test_registry_preserves_arguments_and_never_requests_a_shell(tmp_path: Path) -> None:
    npm = tmp_path / "npm.cmd"
    npm.write_text("shim", encoding="utf-8")
    runner = RecordingRunner(ProcessOutcome(0, "", ""))
    results = ValidatorRegistry(platform="nt", which=resolver({"npm.cmd": npm})).run(
        ("frontend tests",), root=tmp_path, runner=runner, timeout_seconds=10,
    )
    assert results[0].passed
    assert runner.commands == [(str(npm.resolve()), "test", "--", "--run")]


@pytest.mark.parametrize(
    ("outcome", "detail"),
    (
        (ProcessOutcome(None, "", "", error="process error: FileNotFoundError"), "process error: FileNotFoundError"),
        (ProcessOutcome(7, "", ""), "exit_code=7"),
        (ProcessOutcome(None, "", "", timed_out=True, error="timeout"), "timed out"),
        (ProcessOutcome(None, "�", "", error="process output decode error: stdout is not valid UTF-8 at byte 0"),
         "process output decode error: stdout is not valid UTF-8 at byte 0"),
    ),
)
def test_validator_diagnostics_preserve_failure_kind(
    tmp_path: Path, outcome: ProcessOutcome, detail: str,
) -> None:
    runner = RecordingRunner(outcome)
    result = ValidatorRegistry(platform="posix").run(
        ("typescript",), root=tmp_path, runner=runner, timeout_seconds=10,
    )[0]
    assert not result.passed
    assert result.detail == detail


def test_missing_executable_diagnostic_is_deterministic(tmp_path: Path) -> None:
    runner = RecordingRunner(ProcessOutcome(0, "", ""))
    result = ValidatorRegistry(platform="nt", which=lambda _: None).run(
        ("production build",), root=tmp_path, runner=runner, timeout_seconds=10,
    )[0]
    assert result.detail == "validator executable could not be resolved: npm"
    assert runner.commands == []
