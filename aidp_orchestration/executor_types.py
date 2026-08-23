"""Shared process protocol types kept separate to avoid import cycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    error: str | None = None


class ProcessRunner(Protocol):
    def run(self, args: Sequence[str], *, cwd: Path, timeout_seconds: float) -> ProcessOutcome:
        ...
