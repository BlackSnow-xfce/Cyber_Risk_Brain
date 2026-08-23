from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aidp_orchestration.executor import GitInspector


def git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def initialize_repository(root: Path, files: dict[str, str]) -> GitInspector:
    git(root, "init", "-q", "-b", "test")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@localhost")
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(root, "add", "--", ".")
    git(root, "commit", "-q", "-m", "fixture")
    return GitInspector(root)


def test_unstaged_modified_first_path_loses_no_leading_character(tmp_path: Path) -> None:
    inspector = initialize_repository(tmp_path, {"tests/orchestration/e2e_probe.txt": "PENDING\n"})
    (tmp_path / "tests/orchestration/e2e_probe.txt").write_text("CHANGED\n", encoding="utf-8")
    assert inspector.changed_files() == ("tests/orchestration/e2e_probe.txt",)


def test_staged_modified_path_is_included(tmp_path: Path) -> None:
    inspector = initialize_repository(tmp_path, {"staged.txt": "before\n"})
    (tmp_path / "staged.txt").write_text("after\n", encoding="utf-8")
    git(tmp_path, "add", "--", "staged.txt")
    assert inspector.changed_files() == ("staged.txt",)


def test_deleted_path_is_included(tmp_path: Path) -> None:
    inspector = initialize_repository(tmp_path, {"deleted.txt": "tracked\n"})
    (tmp_path / "deleted.txt").unlink()
    assert inspector.changed_files() == ("deleted.txt",)


def test_untracked_path_with_legitimate_spaces_is_preserved(tmp_path: Path) -> None:
    inspector = initialize_repository(tmp_path, {"tracked.txt": "tracked\n"})
    path = tmp_path / "tests" / "orchestration" / " probe file.txt"
    path.parent.mkdir(parents=True)
    path.write_text("untracked\n", encoding="utf-8")
    assert inspector.changed_files() == ("tests/orchestration/ probe file.txt",)


def test_staged_rename_reports_old_and_new_paths_without_rename_hiding(tmp_path: Path) -> None:
    inspector = initialize_repository(tmp_path, {"old.txt": "tracked\n"})
    (tmp_path / "old.txt").rename(tmp_path / "new.txt")
    git(tmp_path, "add", "--all")
    assert inspector.changed_files() == ("new.txt", "old.txt")


def test_multiple_sources_are_deduplicated_and_sorted(tmp_path: Path) -> None:
    inspector = initialize_repository(tmp_path, {"z.txt": "base\n", "m.txt": "base\n"})
    (tmp_path / "z.txt").write_text("staged\n", encoding="utf-8")
    git(tmp_path, "add", "--", "z.txt")
    (tmp_path / "z.txt").write_text("staged and unstaged\n", encoding="utf-8")
    (tmp_path / "m.txt").write_text("modified\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text("untracked\n", encoding="utf-8")
    assert inspector.changed_files() == ("a.txt", "m.txt", "z.txt")


def test_malformed_or_undecodable_git_paths_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inspector = GitInspector(tmp_path)
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: b"invalid\xff\0")
    with pytest.raises(UnicodeDecodeError):
        inspector.changed_files()
