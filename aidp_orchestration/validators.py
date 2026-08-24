"""Explicit, non-free-form validation command registry."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, Sequence

from .contracts import ValidationResult
from .executor_types import ProcessOutcome, ProcessRunner


ExecutableResolver = Callable[[str], str | None]


class ValidatorExecutableError(RuntimeError):
    pass


def resolve_validator_command(
    command: tuple[str, ...],
    *,
    platform: str | None = None,
    which: ExecutableResolver = shutil.which,
) -> tuple[str, ...]:
    if not command or not command[0]:
        raise ValidatorExecutableError("validator command is empty")
    if (platform or os.name) != "nt":
        return command

    name = command[0]
    candidates = (name,) if Path(name).suffix else (f"{name}.exe", f"{name}.com", f"{name}.cmd")
    for candidate in candidates:
        resolved = which(candidate)
        if not resolved:
            continue
        path = Path(resolved).resolve()
        if path.is_file() and path.suffix.lower() in {".exe", ".com", ".cmd"}:
            return (str(path), *command[1:])
    raise ValidatorExecutableError(f"validator executable could not be resolved: {name}")


class ValidatorRegistry:
    _commands: dict[str, tuple[str, ...]] = {
        "python tests": ("python", "-m", "pytest"),
        "pytest": ("python", "-m", "pytest"),
        "frontend tests": ("npm", "test", "--", "--run"),
        "typescript": ("npx", "tsc", "--noEmit"),
        "production build": ("npm", "run", "build"),
        "git diff --check": ("git", "diff", "--check"),
    }

    def __init__(
        self,
        *,
        platform: str | None = None,
        which: ExecutableResolver = shutil.which,
    ) -> None:
        self.platform = platform
        self.which = which

    def unknown(self, requirements: Sequence[str]) -> tuple[str, ...]:
        return tuple(requirement for requirement in requirements if requirement.strip().lower() not in self._commands)

    def run(self, requirements: Sequence[str], *, root: Path, runner: ProcessRunner, timeout_seconds: float) -> tuple[ValidationResult, ...]:
        results: list[ValidationResult] = []
        for requirement in requirements:
            key = requirement.strip().lower()
            command = self._commands.get(key)
            if command is None:
                results.append(ValidationResult(requirement, False, "unknown validator"))
                continue
            try:
                resolved = resolve_validator_command(command, platform=self.platform, which=self.which)
            except ValidatorExecutableError as exc:
                results.append(ValidationResult(requirement, False, str(exc)))
                continue
            outcome = runner.run(resolved, cwd=root, timeout_seconds=timeout_seconds)
            passed = outcome.returncode == 0 and not outcome.timed_out and outcome.error is None
            detail = (
                "passed"
                if passed
                else "timed out"
                if outcome.timed_out
                else outcome.error
                if outcome.error is not None
                else f"exit_code={outcome.returncode}"
            )
            results.append(ValidationResult(requirement, passed, detail))
        return tuple(results)
