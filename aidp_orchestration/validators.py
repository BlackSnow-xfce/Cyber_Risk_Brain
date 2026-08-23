"""Explicit, non-free-form validation command registry."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .contracts import ValidationResult
from .executor_types import ProcessOutcome, ProcessRunner


class ValidatorRegistry:
    _commands: dict[str, tuple[str, ...]] = {
        "python tests": ("python", "-m", "pytest"),
        "pytest": ("python", "-m", "pytest"),
        "frontend tests": ("npm", "test", "--", "--run"),
        "typescript": ("npx", "tsc", "--noEmit"),
        "production build": ("npm", "run", "build"),
        "git diff --check": ("git", "diff", "--check"),
    }

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
            outcome = runner.run(command, cwd=root, timeout_seconds=timeout_seconds)
            passed = outcome.returncode == 0 and not outcome.timed_out and outcome.error is None
            detail = "passed" if passed else ("timed out" if outcome.timed_out else f"exit_code={outcome.returncode}")
            results.append(ValidationResult(requirement, passed, detail))
        return tuple(results)
