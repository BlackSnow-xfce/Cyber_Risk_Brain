from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aidp_orchestration.architect_review import create_review_request, create_review_result
from aidp_orchestration.contracts import (
    AIDPState, ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance,
    ExecutionStatus, LifecycleStatus, OrchestrationDecision, ScopeCompliance, ValidationResult,
)
from aidp_orchestration.lifecycle import AIDPLifecycleOnce
from aidp_orchestration.runtime import LocalRuntimeStore


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

    def __init__(self, states):
        self.states = iter(states)

    def inspect(self):
        state = next(self.states)
        return OrchestrationDecision("TASK-9000", state, None, "branch", "head", (), NOW)


class Architect:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def review(self, request, *, schema_path):
        self.calls += 1
        return self.result


class Projection:
    def __init__(self): self.calls = []
    def project_architect_result(self, result): self.calls.append(result.disposition); return "5" * 40
    def publish_result_only(self, result): self.calls.append(("only", result.disposition)); return "5" * 40
    def push(self, branch): self.calls.append(("push", branch)); return "5" * 40


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
