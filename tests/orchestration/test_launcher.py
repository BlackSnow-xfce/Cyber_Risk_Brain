from __future__ import annotations

from pathlib import Path

import pytest

from aidp_orchestration.launcher import CodexLauncherError, resolve_codex_launcher


def resolver(paths: dict[str, Path]):
    return lambda name: str(paths[name]) if name in paths else None


def test_native_codex_exe_is_preferred_and_prefix_is_deterministic(tmp_path: Path) -> None:
    native = tmp_path / "codex.exe"
    node = tmp_path / "node.exe"
    native.write_bytes(b"native")
    node.write_bytes(b"node")

    launcher = resolve_codex_launcher(
        platform="nt",
        which=resolver({"codex.exe": native, "node.exe": node}),
        search_path=str(tmp_path),
    )

    assert launcher.argv_prefix == (str(native.resolve()),)


def test_windows_npm_launcher_uses_node_and_absolute_codex_js(tmp_path: Path) -> None:
    npm_root = tmp_path / "npm"
    node = tmp_path / "node.exe"
    codex_js = npm_root / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    codex_js.parent.mkdir(parents=True)
    node.write_bytes(b"node")
    codex_js.write_text("entry", encoding="utf-8")

    launcher = resolve_codex_launcher(
        platform="nt",
        which=resolver({"node.exe": node}),
        search_path=str(npm_root),
    )

    assert launcher.argv_prefix == (str(node.resolve()), str(codex_js.resolve()))
    assert all(not item.lower().endswith((".cmd", ".ps1")) for item in launcher.argv_prefix)


def test_missing_node_exe_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(CodexLauncherError, match="node.exe"):
        resolve_codex_launcher(platform="nt", which=resolver({}), search_path=str(tmp_path))


def test_missing_codex_js_fails_closed(tmp_path: Path) -> None:
    node = tmp_path / "node.exe"
    node.write_bytes(b"node")
    with pytest.raises(CodexLauncherError, match="entry point"):
        resolve_codex_launcher(
            platform="nt",
            which=resolver({"node.exe": node}),
            search_path=str(tmp_path),
        )


def test_non_file_launcher_paths_fail_closed(tmp_path: Path) -> None:
    native_directory = tmp_path / "codex.exe"
    native_directory.mkdir()
    with pytest.raises(CodexLauncherError):
        resolve_codex_launcher(
            platform="nt",
            which=resolver({"codex.exe": native_directory}),
            search_path=str(tmp_path),
        )
