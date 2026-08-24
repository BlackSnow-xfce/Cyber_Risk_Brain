"""Deterministic fail-closed worktree admission shared by governance boundaries."""

from __future__ import annotations

import subprocess
from pathlib import PurePosixPath
from typing import Callable

from .contracts import ScopeCompliance
from .repository import AIDPRepository


def worktree_admission_reason(
    changed_files: Callable[[], tuple[str, ...]],
    *,
    allowed_scope: tuple[str, ...] | None = None,
    prohibited_actions: tuple[str, ...] = (),
) -> str | None:
    try:
        paths = changed_files()
    except (OSError, RuntimeError, ValueError, UnicodeError, subprocess.SubprocessError):
        return "worktree dirty paths could not be established"
    if not isinstance(paths, tuple) or any(not _valid_relative_path(path) for path in paths):
        return "worktree dirty paths could not be established"
    if not paths:
        return None
    if allowed_scope is None:
        return "worktree is dirty"
    compliance = AIDPRepository.scope_compliance_for_paths(
        allowed_scope,
        prohibited_actions,
        paths,
    )
    if compliance is not ScopeCompliance.COMPLIANT:
        return "worktree contains changes outside the active task authority"
    return None


def cleanliness_adapter(is_clean: Callable[[], bool]) -> Callable[[], tuple[str, ...]]:
    def changed_files() -> tuple[str, ...]:
        if is_clean():
            return ()
        raise RuntimeError("binary cleanliness result does not establish dirty paths")

    return changed_files


def _valid_relative_path(path: object) -> bool:
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    parsed = PurePosixPath(path)
    return not parsed.is_absolute() and ".." not in parsed.parts and path == parsed.as_posix()
