"""Fail-closed, shell-free resolution of the Codex CLI launcher."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PathResolver = Callable[[str], str | None]


class CodexLauncherError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CodexLauncher:
    argv_prefix: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.argv_prefix or any(not item for item in self.argv_prefix):
            raise ValueError("Codex launcher argv prefix must be explicit")


def resolve_codex_launcher(
    *,
    platform: str | None = None,
    which: PathResolver = shutil.which,
    search_path: str | None = None,
) -> CodexLauncher:
    """Resolve only directly executable or trusted npm Codex entry points."""
    current_platform = platform or os.name
    native_name = "codex.exe" if current_platform == "nt" else "codex"
    native = _resolved_file(which(native_name), suffix=".exe" if current_platform == "nt" else None)
    if native is not None:
        return CodexLauncher((str(native),))

    if current_platform != "nt":
        raise CodexLauncherError("directly executable Codex CLI was not found")

    node = _resolved_file(which("node.exe"), suffix=".exe")
    if node is None:
        raise CodexLauncherError("node.exe required by the npm Codex launcher was not found")

    path_value = os.environ.get("PATH", "") if search_path is None else search_path
    candidates = {
        (Path(entry.strip('"')) / "node_modules" / "@openai" / "codex" / "bin" / "codex.js").resolve()
        for entry in path_value.split(";")
        if entry.strip('"')
    }
    codex_scripts = sorted(path for path in candidates if path.is_file() and path.suffix.lower() == ".js")
    if not codex_scripts:
        raise CodexLauncherError("trusted npm @openai/codex entry point was not found")
    if len(codex_scripts) != 1:
        raise CodexLauncherError("multiple npm Codex entry points are ambiguous")
    return CodexLauncher((str(node), str(codex_scripts[0])))


def _resolved_file(value: str | None, *, suffix: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).resolve()
    if not path.is_file():
        return None
    if suffix is not None and path.suffix.lower() != suffix:
        return None
    return path
