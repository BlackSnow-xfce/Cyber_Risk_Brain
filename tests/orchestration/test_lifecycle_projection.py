from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from aidp_orchestration.architect_review import create_review_result
from aidp_orchestration.contracts import (
    ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance,
)
from aidp_orchestration.lifecycle_projection import LifecycleProjection


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "topic")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.invalid")
    ready = root / ".ai/tasks/ready/TASK-9000.md"
    ready.parent.mkdir(parents=True)
    ready.write_text("---\ntask_id: TASK-9000\n---\n# Task\n\nStatus: READY\n", encoding="utf-8")
    handoff = root / ".ai/handoff"
    handoff.mkdir(parents=True)
    (handoff / "TO-CODEX.md").write_text("ready\n", encoding="utf-8")
    (handoff / "TO-ARCHITECT.md").write_text("waiting\n", encoding="utf-8")
    _git(root, "add", ".ai")
    _git(root, "commit", "-m", "ready")
    return root


def _pass_result(expected_head: str):
    values = dict(
        review_request_id="a" * 64, task_id="TASK-9000", execution_id="execution",
        review_iteration=0, disposition=ArchitectReviewDisposition.PASS,
        reviewed_head="2" * 40, expected_head=expected_head, reviewed_tree_hash="3" * 40,
        findings=(), allowed_rework_scope=(), required_validations=(),
        provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    return create_review_result(**values)


def _fail_result(expected_head: str):
    finding = ArchitectFinding("F", "rule", "high", "summary", ("a.py",), "action", "change")
    values = dict(
        review_request_id="a" * 64, task_id="TASK-9000", execution_id="execution",
        review_iteration=0, disposition=ArchitectReviewDisposition.FAIL,
        reviewed_head="2" * 40, expected_head=expected_head, reviewed_tree_hash="3" * 40,
        findings=(finding,), allowed_rework_scope=("a.py",), required_validations=("pytest",),
        provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    return create_review_result(**values)


def test_ready_review_and_pass_projection_are_exact_commit_backed(tmp_path: Path):
    root = _repo(tmp_path)
    envelope = ".ai/orchestration/review-inbox/TASK-9000-execution.json"
    path = root / envelope
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"architect_review_envelope": {"execution_id": "execution"}}), encoding="utf-8")
    projection = LifecycleProjection(root)
    review_head = projection.project_ready_for_architect("TASK-9000", envelope)
    assert not (root / ".ai/tasks/ready/TASK-9000.md").exists()
    assert "Status: REVIEW" in (root / ".ai/tasks/review/TASK-9000.md").read_text(encoding="utf-8")
    assert not _git(root, "status", "--porcelain=v1")
    pass_head = projection.project_architect_result(_pass_result(review_head))
    assert pass_head != review_head
    assert "Status: ARCHITECT_APPROVED" in (root / ".ai/tasks/review/TASK-9000.md").read_text(encoding="utf-8")
    assert tuple((root / ".ai/orchestration/architect-review-results").glob("*.json"))
    assert not _git(root, "status", "--porcelain=v1")


def test_rework_projection_returns_committed_ready_for_architect_state(tmp_path: Path):
    root = _repo(tmp_path)
    first_envelope = ".ai/orchestration/review-inbox/TASK-9000-execution.json"
    first = root / first_envelope
    first.parent.mkdir(parents=True)
    first.write_text("{}", encoding="utf-8")
    projection = LifecycleProjection(root)
    review_head = projection.project_ready_for_architect("TASK-9000", first_envelope)
    projection.project_architect_result(_fail_result(review_head))
    second_envelope = ".ai/orchestration/review-inbox/TASK-9000-rework.json"
    second = root / second_envelope
    second.write_text("{}", encoding="utf-8")
    projection.project_rework_ready_for_architect("TASK-9000", second_envelope)
    assert "Status: REVIEW" in (root / ".ai/tasks/review/TASK-9000.md").read_text(encoding="utf-8")
    assert "REWORK REQUIRED" not in (root / ".ai/tasks/review/TASK-9000.md").read_text(encoding="utf-8")
    assert not _git(root, "status", "--porcelain=v1")
