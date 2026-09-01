"""Exact Git-backed projections required by autonomous Architect review."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from .contracts import ArchitectReviewDisposition, ArchitectReviewResult
from .executor import GitInspector


class LifecycleProjection:
    def __init__(self, repository_root: Path) -> None:
        self.root = repository_root.resolve()
        self.git = GitInspector(self.root)

    def project_ready_for_architect(self, task_id: str, review_envelope_path: str) -> str:
        ready = self.root / ".ai" / "tasks" / "ready" / f"{task_id}.md"
        review = self.root / ".ai" / "tasks" / "review" / f"{task_id}.md"
        envelope = self.root / review_envelope_path
        if not ready.is_file() or review.exists() or not envelope.is_file():
            raise RuntimeError("READY-to-REVIEW projection precondition failed")
        document = ready.read_text(encoding="utf-8")
        if "Status: READY" not in document:
            raise RuntimeError("READY task has no exact status marker")
        contents = {
            review: document.replace("Status: READY", "Status: REVIEW", 1),
            self.root / ".ai/handoff/TO-CODEX.md": (
                "# Handoff - Architect to Codex\n\nStatus: WAITING\n"
                f"Current AIDP Task: {task_id}\nCurrent Phase: REVIEW / WAITING\nTask Status: REVIEW\n"
            ),
            self.root / ".ai/handoff/TO-ARCHITECT.md": (
                f"# Handoff - Architecture Review {task_id}\n\nStatus: OPEN\nTask: {task_id}\n"
                "Task Status: REVIEW\nReviewer: Architect\n"
            ),
        }
        expected = tuple(sorted((
            ready.relative_to(self.root).as_posix(), review.relative_to(self.root).as_posix(),
            ".ai/handoff/TO-CODEX.md", ".ai/handoff/TO-ARCHITECT.md", review_envelope_path,
        )))
        self._materialize(contents, deletes=(ready,))
        return self._commit_exact(expected, f"aidp({task_id}): project ready for architect")

    def project_rework_ready_for_architect(self, task_id: str, review_envelope_path: str) -> str:
        review = self.root / ".ai" / "tasks" / "review" / f"{task_id}.md"
        envelope = self.root / review_envelope_path
        if not review.is_file() or not envelope.is_file():
            raise RuntimeError("rework REVIEW projection precondition failed")
        document = review.read_text(encoding="utf-8")
        marker = "Status: REVIEW / REWORK REQUIRED"
        if marker not in document:
            raise RuntimeError("rework task has no exact status marker")
        contents = {
            review: document.replace(marker, "Status: REVIEW", 1),
            self.root / ".ai/handoff/TO-CODEX.md": (
                "# Handoff - Architect to Codex\n\nStatus: WAITING\n"
                f"Current AIDP Task: {task_id}\nCurrent Phase: REVIEW / WAITING\nTask Status: REVIEW\n"
            ),
            self.root / ".ai/handoff/TO-ARCHITECT.md": (
                f"# Handoff - Architecture Review {task_id}\n\nStatus: OPEN\nTask: {task_id}\n"
                "Task Status: REVIEW\nReviewer: Architect\n"
            ),
        }
        expected = tuple(sorted((*[path.relative_to(self.root).as_posix() for path in contents], review_envelope_path)))
        self._materialize(contents)
        return self._commit_exact(expected, f"aidp({task_id}): project rework ready for architect")

    def project_architect_result(self, result: ArchitectReviewResult) -> str:
        if result.disposition not in {ArchitectReviewDisposition.PASS, ArchitectReviewDisposition.FAIL}:
            raise RuntimeError("BLOCKED result has no lifecycle projection authority")
        review = self.root / ".ai" / "tasks" / "review" / f"{result.task_id}.md"
        if not review.is_file():
            raise RuntimeError("Architect projection requires one REVIEW task")
        document = review.read_text(encoding="utf-8")
        if "Status: REVIEW" not in document:
            raise RuntimeError("REVIEW task has no exact status marker")
        contents = self._result_projection_contents(result, document)
        expected = tuple(sorted(path.relative_to(self.root).as_posix() for path in contents))
        self._materialize(contents)
        return self._commit_exact(expected, f"aidp({result.task_id}): project architect {result.disposition.value.lower()} {result.review_result_id}")

    def publish_result_only(self, result: ArchitectReviewResult) -> str:
        relative = (
            ".ai/orchestration/architect-review-results/"
            f"{result.task_id}-{result.review_iteration}-{result.review_result_id}.json"
        )
        path = self.root / relative
        content = json.dumps(
            {"architect_review_result": asdict(result)}, default=_json_default,
            sort_keys=True, separators=(",", ":"),
        ) + "\n"
        self._materialize({path: content})
        return self._commit_exact((relative,), f"aidp({result.task_id}): publish blocked architect review {result.review_result_id}")

    def push(self, expected_branch: str) -> str:
        if self.git.branch() != expected_branch:
            raise RuntimeError("lifecycle projection branch mismatch")
        subprocess.check_output(("git", "remote", "get-url", "origin"), cwd=self.root, stderr=subprocess.STDOUT)
        subprocess.check_output(("git", "push", "origin", expected_branch), cwd=self.root, stderr=subprocess.STDOUT)
        local = self.git.head()
        remote = subprocess.check_output(
            ("git", "rev-parse", f"origin/{expected_branch}"), cwd=self.root, text=True, stderr=subprocess.STDOUT,
        ).strip()
        if local != remote:
            raise RuntimeError("lifecycle projection push did not synchronize upstream")
        return local

    def verify_result_projection_commit(self, result: ArchitectReviewResult, commit: str) -> None:
        if self.git.head() != commit:
            raise RuntimeError("pending lifecycle projection is not repository HEAD")
        parent = subprocess.check_output(
            ("git", "rev-parse", f"{commit}^"), cwd=self.root, text=True, stderr=subprocess.STDOUT,
        ).strip()
        if parent != result.expected_head:
            raise RuntimeError("pending lifecycle projection parent is not the reviewed HEAD")
        relative = (
            ".ai/orchestration/architect-review-results/"
            f"{result.task_id}-{result.review_iteration}-{result.review_result_id}.json"
        )
        expected = tuple(sorted((
            f".ai/tasks/review/{result.task_id}.md", ".ai/handoff/TO-CODEX.md",
            ".ai/handoff/TO-ARCHITECT.md", relative,
        )))
        changed = _nul(self.root, "diff", "--name-only", "--no-renames", "-z", f"{commit}^", commit)
        if tuple(sorted(changed)) != expected:
            raise RuntimeError("pending lifecycle projection paths differ from authority")
        task_relative = f".ai/tasks/review/{result.task_id}.md"
        try:
            parent_document = subprocess.check_output(
                ("git", "show", f"{parent}:{task_relative}"), cwd=self.root,
                stderr=subprocess.STDOUT,
            ).decode("utf-8", errors="strict")
        except (subprocess.CalledProcessError, UnicodeError) as exc:
            raise RuntimeError("pending lifecycle projection parent task is invalid") from exc
        expected_contents = self._result_projection_contents(result, parent_document)
        for path, content in expected_contents.items():
            relative_path = path.relative_to(self.root).as_posix()
            committed = _committed_blob(self.root, commit, relative_path)
            if committed != content.encode("utf-8"):
                raise RuntimeError(f"pending lifecycle projection content is invalid: {relative_path}")
        if self.git.changed_files():
            raise RuntimeError("pending lifecycle projection worktree is dirty")

    def _result_projection_contents(
        self, result: ArchitectReviewResult, review_document: str,
    ) -> dict[Path, str]:
        if "Status: REVIEW" not in review_document:
            raise RuntimeError("REVIEW task has no exact status marker")
        passed = result.disposition is ArchitectReviewDisposition.PASS
        status = "ARCHITECT_APPROVED" if passed else "REVIEW / REWORK REQUIRED"
        codex_status = "WAITING" if passed else "OPEN"
        architect_status = "CLOSED" if passed else "WAITING"
        result_relative = (
            ".ai/orchestration/architect-review-results/"
            f"{result.task_id}-{result.review_iteration}-{result.review_result_id}.json"
        )
        return {
            self.root / f".ai/tasks/review/{result.task_id}.md":
                review_document.replace("Status: REVIEW", f"Status: {status}", 1),
            self.root / ".ai/handoff/TO-CODEX.md": (
                f"# Handoff - Architect to Codex\n\nStatus: {codex_status}\n"
                f"Current AIDP Task: {result.task_id}\nCurrent Phase: {status}\nTask Status: {status}\n"
            ),
            self.root / ".ai/handoff/TO-ARCHITECT.md": (
                f"# Handoff - Architecture Review {result.task_id}\n\nStatus: {architect_status}\n"
                f"Task: {result.task_id}\nTask Status: {status}\nReviewer: Architect\n"
            ),
            self.root / result_relative: json.dumps(
                {"architect_review_result": asdict(result)}, default=_json_default,
                sort_keys=True, separators=(",", ":"),
            ) + "\n",
        }

    def _commit_exact(self, expected: tuple[str, ...], message: str) -> str:
        changed = self.git.changed_files()
        if changed != expected:
            raise RuntimeError("lifecycle projection contains unexpected paths")
        subprocess.check_output(("git", "add", "-A", "--", *expected), cwd=self.root, stderr=subprocess.STDOUT)
        staged = _nul(self.root, "diff", "--cached", "--no-renames", "--name-only", "-z")
        if tuple(sorted(staged)) != expected:
            raise RuntimeError("staged lifecycle projection differs from authority")
        subprocess.check_output(("git", "commit", "-m", message), cwd=self.root, stderr=subprocess.STDOUT)
        return self.git.head()

    @staticmethod
    def _materialize(contents: dict[Path, str], deletes: tuple[Path, ...] = ()) -> None:
        affected = (*contents, *deletes)
        original = {path: path.read_bytes() if path.exists() else None for path in affected}
        try:
            for path, content in contents.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(f".{path.name}.aidp-projection.tmp")
                try:
                    with temporary.open("xb") as stream:
                        stream.write(content.encode("utf-8"))
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
            for path in deletes:
                path.unlink()
        except OSError:
            for path, previous in original.items():
                if previous is None:
                    path.unlink(missing_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(previous)
            raise


def _nul(root: Path, *args: str) -> tuple[str, ...]:
    output = subprocess.check_output(("git", *args), cwd=root)
    if output and not output.endswith(b"\0"):
        raise RuntimeError("Git returned malformed path output")
    return tuple(output[:-1].decode("utf-8").split("\0")) if output else ()


def _committed_blob(root: Path, commit: str, relative_path: str) -> bytes:
    """Read one exact tree blob without constructing a long ``commit:path`` argument."""
    entry = subprocess.check_output(
        ("git", "ls-tree", "-z", commit, "--", relative_path), cwd=root,
        stderr=subprocess.STDOUT,
    )
    if not entry.endswith(b"\0") or entry.count(b"\0") != 1:
        raise RuntimeError(f"pending lifecycle projection blob is missing: {relative_path}")
    metadata, separator, encoded_path = entry[:-1].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3 or fields[1] != b"blob":
        raise RuntimeError(f"pending lifecycle projection tree entry is invalid: {relative_path}")
    try:
        tree_path = encoded_path.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise RuntimeError("pending lifecycle projection path is not UTF-8") from exc
    if tree_path != relative_path:
        raise RuntimeError(f"pending lifecycle projection path identity is invalid: {relative_path}")
    return subprocess.check_output(
        ("git", "cat-file", "blob", fields[2].decode("ascii")), cwd=root,
        stderr=subprocess.STDOUT,
    )


def _json_default(value: object) -> object:
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, Enum): return value.value
    if isinstance(value, Path): return str(value)
    raise TypeError(type(value).__name__)
