from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aidp_orchestration.architect_review import (
    ArchitectReviewCoordinator, ProductWorktreeIdentityGuard, create_review_request,
    create_review_result, validate_review_result,
)
from aidp_orchestration.contracts import (
    ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance,
    ExecutionStatus, ScopeCompliance, ValidationResult,
)
from aidp_orchestration.executor_types import ProcessOutcome
from aidp_orchestration.launcher import CodexLauncher


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def request(**changes):
    values = dict(
        task_id="AIDP-INFRA-0001", review_iteration=0, execution_id="execution-1",
        repository="C:/product", git_common_dir="C:/repo/.git", branch="topic", remote_url="origin",
        authority_contract_id="authority-1", authority_contract_digest="a" * 64,
        original_allowed_scope=("allowed.py",), original_prohibited_actions=("no product",),
        original_validation_requirements=("python tests",), original_acceptance_criteria=("works",),
        product_owner_gate=True, review_envelope_path=".ai/review.json", review_envelope_digest="b" * 64,
        execution_status=ExecutionStatus.SUCCESS, start_commit="1" * 40, resulting_commit="2" * 40,
        review_envelope_commit="3" * 40, changed_files=("allowed.py",),
        validation_results=(ValidationResult("python tests", True, "passed"),),
        scope_compliance=ScopeCompliance.COMPLIANT, expected_current_head="3" * 40,
        current_head="3" * 40, reviewed_head="2" * 40, reviewed_tree_hash="4" * 40,
        previous_review_result_id=None, previous_rework_contract_id=None,
        previous_finding_fingerprints=(), created_at=NOW,
    )
    values.update(changes)
    return create_review_request(**values)


def provenance():
    return ArchitectReviewProvenance("process", "codex", "model", NOW, NOW, "architect-review-result-v1")


def result(req, disposition=ArchitectReviewDisposition.PASS, **changes):
    finding = ArchitectFinding("F-1", "rule", "high", "summary", ("allowed.py",), "fix", "change")
    values = dict(
        review_request_id=req.review_request_id, task_id=req.task_id, execution_id=req.execution_id,
        review_iteration=req.review_iteration, disposition=disposition, reviewed_head=req.reviewed_head,
        expected_head=req.expected_current_head, reviewed_tree_hash=req.reviewed_tree_hash,
        findings=(finding,) if disposition is ArchitectReviewDisposition.FAIL else (),
        allowed_rework_scope=("allowed.py",) if disposition is ArchitectReviewDisposition.FAIL else (),
        required_validations=("python tests",) if disposition is ArchitectReviewDisposition.FAIL else (),
        provenance=provenance(), failure_reason="blocked" if disposition is ArchitectReviewDisposition.BLOCKED else None,
        authority_claims=(), created_at=NOW,
    )
    values.update(changes)
    return create_review_result(**values)


def test_namespace_request_and_result_identities_are_deterministic():
    first = request()
    assert first.review_request_id == request().review_request_id
    approved = result(first)
    assert approved.review_result_id == result(first).review_result_id
    assert len(first.review_request_id) == len(approved.review_result_id) == 64


def test_pass_fail_and_blocked_authority_is_strict():
    req = request()
    validate_review_result(req, result(req))
    validate_review_result(req, result(req, ArchitectReviewDisposition.FAIL))
    with pytest.raises(ValueError, match="PASS"):
        result(req, findings=(ArchitectFinding("F", "r", "high", "s", ("allowed.py",), "a", "c"),))
    with pytest.raises(ValueError, match="authority"):
        result(req, authority_claims=("PRODUCT_OWNER_PASS",))
    with pytest.raises(ValueError, match="widens"):
        validate_review_result(req, result(req, ArchitectReviewDisposition.FAIL, allowed_rework_scope=("other.py",)))


class FakeGuard:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def validate(self, **_kwargs):
        return {"repository": str(self.root), "git_common_dir": "C:/repo/.git", "branch": "topic", "remote_url": "origin"}


class FakeRunner:
    def __init__(self, decision, *, timeout=False, returncode=0):
        self.decision = decision
        self.timeout = timeout
        self.returncode = returncode
        self.calls = []

    def run(self, args, *, cwd, timeout_seconds):
        self.calls.append((tuple(args), cwd, timeout_seconds))
        if len(self.calls) == 1:
            return ProcessOutcome(0, "--sandbox --ephemeral --ignore-user-config --output-schema --json", "")
        if self.timeout:
            return ProcessOutcome(None, "", "", timed_out=True, error="timeout")
        event = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.decision)}})
        return ProcessOutcome(self.returncode, event, "")


def test_coordinator_is_headless_read_only_and_orchestrator_binds_result(tmp_path: Path):
    req = request(repository=str(tmp_path), git_common_dir="C:/repo/.git")
    decision = {"disposition": "PASS", "findings": [], "allowed_rework_scope": [],
                "required_validations": [], "failure_reason": None, "authority_claims": []}
    runner = FakeRunner(decision)
    coordinator = ArchitectReviewCoordinator(
        product_root=tmp_path, identity_guard=FakeGuard(tmp_path), runner=runner,
        launcher=CodexLauncher(("codex.exe",)), clock=lambda: NOW,
    )
    schema = tmp_path / "schema.json"
    schema.write_text("{}", encoding="utf-8")
    reviewed = coordinator.review(req, schema_path=schema)
    assert reviewed.disposition is ArchitectReviewDisposition.PASS
    command, cwd, _ = runner.calls[1]
    assert cwd == tmp_path.resolve()
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert "--ephemeral" in command and "--output-schema" in command
    assert reviewed.review_request_id == req.review_request_id


def test_timeout_and_malformed_output_are_blocked(tmp_path: Path):
    req = request(repository=str(tmp_path), git_common_dir="C:/repo/.git")
    schema = tmp_path / "schema.json"
    schema.write_text("{}", encoding="utf-8")
    coordinator = ArchitectReviewCoordinator(
        product_root=tmp_path, identity_guard=FakeGuard(tmp_path), runner=FakeRunner({}, timeout=True),
        launcher=CodexLauncher(("codex.exe",)), clock=lambda: NOW,
    )
    assert coordinator.review(req, schema_path=schema).disposition is ArchitectReviewDisposition.BLOCKED


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def test_product_worktree_identity_guard_rejects_excluded_and_divergent_roots(tmp_path: Path):
    root = tmp_path / "product"
    remote = tmp_path / "origin.git"
    root.mkdir()
    _git(root, "init", "-b", "product")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.invalid")
    (root / "base").write_text("x", encoding="utf-8")
    _git(root, "add", "base")
    _git(root, "commit", "-m", "base")
    subprocess.check_call(("git", "init", "--bare", str(remote)))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-u", "origin", "product")
    guard = ProductWorktreeIdentityGuard(root, expected_branch="product", excluded_roots=(tmp_path / "infra",))
    assert guard.validate()["head"] == _git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="excluded"):
        ProductWorktreeIdentityGuard(root, expected_branch="product", excluded_roots=(root,)).validate()
    (root / "base").write_text("dirty", encoding="utf-8")
    with pytest.raises(ValueError, match="dirty"):
        guard.validate()
