from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aidp_orchestration.architect_review import create_review_request, create_review_result
from aidp_orchestration.contracts import (
    AIDPState, ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance, ArchitectTaskContract,
    ContractInboxItem, ReworkContract,
    ExecutionStatus, LifecycleStatus, OrchestrationDecision, ScopeCompliance, ValidationResult,
)
from aidp_orchestration.lifecycle import AIDPLifecycleOnce
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.trigger_publisher import LocalContractInbox


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _request(iteration=0, tree="4" * 40, changed=("a.py",)):
    return create_review_request(
        task_id="TASK-9000", review_iteration=iteration, execution_id=f"exec-{iteration}", repository="repo",
        git_common_dir="git", branch="branch", remote_url="origin", authority_contract_id="contract",
        authority_contract_digest="a" * 64, original_allowed_scope=("a.py",),
        original_prohibited_actions=("no product",), original_validation_requirements=("pytest",),
        original_acceptance_criteria=("pass",), product_owner_gate=True, review_envelope_path="review.json",
        review_envelope_digest=(str(iteration) or "0") * 64, execution_status=ExecutionStatus.SUCCESS,
        start_commit="1" * 40, resulting_commit="2" * 40, review_envelope_commit="3" * 40,
        changed_files=changed, validation_results=(ValidationResult("pytest", True),),
        scope_compliance=ScopeCompliance.COMPLIANT, expected_current_head="3" * 40,
        current_head="3" * 40, reviewed_head="2" * 40, reviewed_tree_hash=tree,
        previous_review_result_id=None, previous_rework_contract_id=None,
        previous_finding_fingerprints=(), created_at=NOW,
    )


def _result(request, disposition):
    finding = ArchitectFinding("F", "rule", "high", "summary", ("a.py",), "action", "change")
    values = dict(
        review_request_id=request.review_request_id, task_id=request.task_id,
        execution_id=request.execution_id, review_iteration=request.review_iteration,
        disposition=disposition, reviewed_head=request.reviewed_head,
        expected_head=request.expected_current_head, reviewed_tree_hash=request.reviewed_tree_hash,
        findings=(finding,) if disposition is ArchitectReviewDisposition.FAIL else (),
        allowed_rework_scope=("a.py",) if disposition is ArchitectReviewDisposition.FAIL else (),
        required_validations=("pytest",) if disposition is ArchitectReviewDisposition.FAIL else (),
        provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    return create_review_result(**values)


class Repo:
    root = Path(".").resolve()
    head = "5" * 40

    def __init__(self, states):
        self.states = iter(states)

    def inspect(self):
        state = next(self.states)
        return OrchestrationDecision("TASK-9000", state, None, "branch", "head", (), NOW)


class Architect:
    def __init__(self, result, revalidation_error=None):
        self.result = result
        self.calls = 0
        self.revalidation_error = revalidation_error

    def review(self, request, *, schema_path):
        self.calls += 1
        return self.result

    def revalidate(self, request):
        if self.revalidation_error:
            raise ValueError(self.revalidation_error)


class Projection:
    def __init__(self): self.calls = []
    def project_architect_result(self, result): self.calls.append(result.disposition); return "5" * 40
    def publish_result_only(self, result): self.calls.append(("only", result.disposition)); return "5" * 40
    def push(self, branch): self.calls.append(("push", branch)); return "5" * 40
    def verify_result_projection_commit(self, result, commit): self.calls.append(("verify", commit))


def test_product_owner_gate_is_absolute_no_action(tmp_path):
    architect = Architect(None)
    lifecycle = AIDPLifecycleOnce(
        Repo([AIDPState.WAITING_FOR_PRODUCT_OWNER]), architect=architect,
        runtime_store=LocalRuntimeStore(tmp_path), projection=Projection(),
    )
    assert lifecycle.run_once().status is LifecycleStatus.NO_ACTION
    assert architect.calls == 0


def test_pass_reaches_product_owner_gate_after_verified_persistence(tmp_path):
    request = _request()
    architect = Architect(_result(request, ArchitectReviewDisposition.PASS))
    projection = Projection()
    lifecycle = AIDPLifecycleOnce(
        Repo([AIDPState.READY_FOR_ARCHITECT, AIDPState.WAITING_FOR_PRODUCT_OWNER]),
        architect=architect, runtime_store=LocalRuntimeStore(tmp_path), projection=projection,
        request_factory=lambda _task: request, clock=lambda: NOW,
    )
    result = lifecycle.run_once()
    assert result.status is LifecycleStatus.ADVANCED
    assert result.state is AIDPState.WAITING_FOR_PRODUCT_OWNER
    assert projection.calls == [ArchitectReviewDisposition.PASS, ("push", "branch")]
    assert tuple((tmp_path / "architect-review-results").glob("*.json"))


def test_abandoned_architect_attempt_escalates_without_duplicate_launch(tmp_path):
    request = _request()
    store = LocalRuntimeStore(tmp_path)
    store.persist_architect_attempt(request.review_request_id, {"state": "LAUNCHING"})
    architect = Architect(_result(request, ArchitectReviewDisposition.PASS))
    lifecycle = AIDPLifecycleOnce(
        Repo([AIDPState.READY_FOR_ARCHITECT]), architect=architect, runtime_store=store,
        projection=Projection(), request_factory=lambda _task: request,
    )
    assert lifecycle.run_once().status is LifecycleStatus.ESCALATION_REQUIRED
    assert architect.calls == 0


def test_persisted_result_is_projected_after_restart_without_relaunch(tmp_path):
    request = _request()
    persisted = _result(request, ArchitectReviewDisposition.PASS)
    store = LocalRuntimeStore(tmp_path)
    store.persist_architect_request(request)
    store.persist_architect_attempt(request.review_request_id, {
        "review_request_id": request.review_request_id,
        "execution_id": request.execution_id,
        "state": "LAUNCH_AUTHORIZED",
        "created_at": request.created_at,
    })
    store.persist_architect_result(persisted)
    architect = Architect(persisted)
    lifecycle = AIDPLifecycleOnce(
        Repo([AIDPState.READY_FOR_ARCHITECT, AIDPState.WAITING_FOR_PRODUCT_OWNER]),
        architect=architect, runtime_store=store, projection=Projection(),
        request_factory=lambda _task: request, clock=lambda: NOW,
    )
    assert lifecycle.run_once().state is AIDPState.WAITING_FOR_PRODUCT_OWNER
    assert architect.calls == 0


def test_loop_limit_identical_findings_and_no_progress_are_escalations():
    initial = _request()
    prior = _result(initial, ArchitectReviewDisposition.FAIL)
    limit_request = _request(iteration=3, tree="5" * 40)
    limit = _result(limit_request, ArchitectReviewDisposition.FAIL)
    assert "Rework 4" in AIDPLifecycleOnce._loop_guard(limit_request, limit, (prior,))
    next_request = _request(iteration=1, tree="5" * 40)
    repeated = _result(next_request, ArchitectReviewDisposition.FAIL)
    assert "identical" in AIDPLifecycleOnce._loop_guard(next_request, repeated, (prior,))
    unchanged = _request(iteration=1, tree=prior.reviewed_tree_hash)
    unchanged_result = _result(unchanged, ArchitectReviewDisposition.FAIL)
    assert "tree" in AIDPLifecycleOnce._loop_guard(unchanged, unchanged_result, (prior,))


def test_iteration_jump_and_duplicate_execution_are_rejected():
    initial = _request()
    prior = _result(initial, ArchitectReviewDisposition.FAIL)
    jumped = _request(iteration=2)
    jumped_result = _result(jumped, ArchitectReviewDisposition.PASS)
    try:
        AIDPLifecycleOnce._validate_sequence(jumped, jumped_result, (prior,))
    except ValueError as exc:
        assert "iteration" in str(exc)
    else:
        raise AssertionError("iteration jump was accepted")


@pytest.mark.parametrize("change", ("HEAD", "branch", "dirty worktree", "upstream divergence"))
def test_post_review_identity_change_blocks_before_projection(tmp_path, change):
    request = _request()
    projection = Projection()
    lifecycle = AIDPLifecycleOnce(
        Repo([AIDPState.READY_FOR_ARCHITECT]),
        architect=Architect(_result(request, ArchitectReviewDisposition.PASS), change),
        runtime_store=LocalRuntimeStore(tmp_path), projection=projection,
        request_factory=lambda _task: request, clock=lambda: NOW,
    )
    result = lifecycle.run_once()
    assert result.status is LifecycleStatus.ESCALATION_REQUIRED
    assert change in result.reason
    assert projection.calls == []


@pytest.mark.parametrize(
    ("disposition", "local_state", "target"),
    (
        (ArchitectReviewDisposition.PASS, AIDPState.WAITING_FOR_PRODUCT_OWNER, AIDPState.WAITING_FOR_PRODUCT_OWNER),
        (ArchitectReviewDisposition.FAIL, AIDPState.REWORK_REQUIRED, AIDPState.REWORK_REQUIRED),
    ),
)
def test_restart_pushes_existing_projection_commit_without_recommit(tmp_path, disposition, local_state, target):
    request = _request()
    result = _result(request, disposition)
    store = LocalRuntimeStore(tmp_path)
    store.persist_architect_result(result)
    store.append_projection_event(result.review_result_id, {
        "task_id": request.task_id, "review_result_id": result.review_result_id,
        "branch": request.branch, "expected_parent": result.expected_head,
        "projection_commit": "5" * 40, "disposition": disposition,
        "state": "COMMITTED", "timestamp": NOW,
    })
    projection = Projection()
    architect = Architect(result)
    lifecycle = AIDPLifecycleOnce(
        Repo([local_state]), architect=architect, runtime_store=store,
        projection=projection, clock=lambda: NOW,
    )
    recovered = lifecycle.run_once()
    assert recovered.state is target
    assert projection.calls == [("verify", "5" * 40), ("push", "branch")]
    assert architect.calls == 0


def test_review_request_binds_exact_preceding_rework_contract_identity(tmp_path):
    class RequestRepo:
        root = tmp_path
        ai_root = tmp_path / ".ai"
        head = "3" * 40

        def _git(self, *args):
            if args[0] == "rev-parse" and args[1].endswith("^{tree}"):
                return "5" * 40
            if args == ("rev-parse", "--git-common-dir"):
                return ".git"
            if args == ("remote", "get-url", "origin"):
                return "origin"
            raise AssertionError(args)

    store = LocalRuntimeStore(tmp_path / "runtime")
    authority = ArchitectTaskContract(
        "TASK-9000", "title", "phase", "1" * 40, ("a.py",), ("no product",),
        ("pytest",), ("pass",), True, NOW,
    )
    LocalContractInbox(store.root).persist(ContractInboxItem("authority", authority, NOW))
    prior_request = _request()
    prior_result = _result(prior_request, ArchitectReviewDisposition.FAIL)
    store.persist_architect_result(prior_result)
    rework = ReworkContract("TASK-9000", 1, "1" * 40, ("a.py",), ("finding",), ("pytest",), NOW)
    exact_rework_id = rework.canonical_id(prior_result.review_result_id)
    store.persist_rework_contract(exact_rework_id, rework, prior_result.review_result_id)
    envelope = RequestRepo.ai_root / "orchestration/review-inbox/TASK-9000-rework.json"
    envelope.parent.mkdir(parents=True)
    envelope.write_text(json.dumps({"architect_review_envelope": {
        "task_id": "TASK-9000", "execution_id": "exec-1", "branch": "branch",
        "start_commit": "1" * 40, "resulting_commit": "2" * 40,
        "execution_status": "SUCCESS", "changed_files": ["a.py"],
        "scope_compliance": "COMPLIANT",
        "validation_results": [{"name": "pytest", "passed": True, "detail": "passed"}],
        "published_at": NOW.isoformat(),
    }}), encoding="utf-8")
    lifecycle = AIDPLifecycleOnce(
        RequestRepo(), codex=object(), architect=Architect(prior_result), runtime_store=store,
        projection=Projection(), clock=lambda: NOW,
    )
    built = lifecycle._build_request("TASK-9000")
    assert built.review_iteration == 1
    assert built.previous_rework_contract_id == exact_rework_id
