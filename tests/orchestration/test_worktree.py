from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aidp_orchestration.executor import GitInspector
from aidp_orchestration.worktree import worktree_admission_reason


def git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def fixture(tmp_path: Path) -> GitInspector:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@localhost")
    for relative in ("allowed/one.txt", "allowed/two.txt", "outside.txt"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("initial\n", encoding="utf-8")
    git(tmp_path, "add", "--", "allowed/one.txt", "allowed/two.txt", "outside.txt")
    git(tmp_path, "commit", "-q", "-m", "fixture")
    return GitInspector(tmp_path)


def reason(inspector: GitInspector) -> str | None:
    return worktree_admission_reason(
        inspector.changed_files,
        allowed_scope=("allowed/**",),
        prohibited_actions=(".ai/**",),
    )


def test_clean_worktree_is_admitted(tmp_path: Path) -> None:
    assert reason(fixture(tmp_path)) is None


def test_staged_and_untracked_unauthorized_paths_are_blocked(tmp_path: Path) -> None:
    inspector = fixture(tmp_path)
    (tmp_path / "outside.txt").write_text("staged\n", encoding="utf-8")
    git(tmp_path, "add", "--", "outside.txt")
    assert reason(inspector) is not None
    git(tmp_path, "restore", "--staged", "outside.txt")
    git(tmp_path, "restore", "--", "outside.txt")
    (tmp_path / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    assert reason(inspector) is not None


@pytest.mark.parametrize("operation", ("delete", "rename"))
def test_delete_and_rename_cannot_bypass_scope(tmp_path: Path, operation: str) -> None:
    inspector = fixture(tmp_path)
    if operation == "delete":
        (tmp_path / "outside.txt").unlink()
    else:
        git(tmp_path, "mv", "outside.txt", "allowed/renamed.txt")
    assert reason(inspector) is not None


def test_authorized_tracked_delete_remains_in_scope(tmp_path: Path) -> None:
    inspector = fixture(tmp_path)
    (tmp_path / "allowed/one.txt").unlink()
    assert reason(inspector) is None


@pytest.mark.parametrize("paths", (("../escape",), ("C:/absolute",), ("bad\\path",), ["allowed/one.txt"]))
def test_malformed_or_unverifiable_status_fails_closed(paths) -> None:
    assert worktree_admission_reason(lambda: paths, allowed_scope=("allowed/**",)) is not None


def test_git_status_failure_fails_closed() -> None:
    def failed_git_status():
        raise subprocess.CalledProcessError(128, ("git", "diff"))

    assert worktree_admission_reason(failed_git_status, allowed_scope=("allowed/**",)) is not None
