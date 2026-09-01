from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aidp_orchestration.architect_review import create_review_request, create_review_result
from aidp_orchestration.contracts import (
    AIDPState, ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance,
    CodexExecutionResult, ConsumptionState, ControlPlaneAction, ControlPlaneDecision,
    ControlPlaneResult, ExecutionStatus, LifecycleStatus, OrchestrationDecision,
    PublishResult, RunnerResult, RunnerStatus, ScopeCompliance, TriggerResult, TriggerStatus,
    ValidationResult,
)
from aidp_orchestration.lifecycle import AIDPLifecycleOnce
from aidp_orchestration.runtime import LocalRuntimeStore


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def request(iteration: int, *, tree: str, changed=("a.py",)):
    return create_review_request(
        task_id="TASK-9000", review_iteration=iteration, execution_id=f"exec-{iteration}", repository="repo",
        git_common_dir="git", branch="topic", remote_url="origin", authority_contract_id="contract",
        authority_contract_digest="a" * 64, original_allowed_scope=("a.py", "b.py"),
        original_prohibited_actions=("no product",), original_validation_requirements=("pytest",),
        original_acceptance_criteria=("pass",), product_owner_gate=True,
        review_envelope_path=f"review-{iteration}.json", review_envelope_digest=str(iteration) * 64,
        execution_status=ExecutionStatus.SUCCESS, start_commit="1" * 40, resulting_commit="2" * 40,
        review_envelope_commit="3" * 40, changed_files=tuple(sorted(changed)),
        validation_results=(ValidationResult("pytest", True),), scope_compliance=ScopeCompliance.COMPLIANT,
        expected_current_head="3" * 40, current_head="3" * 40, reviewed_head="2" * 40,
        reviewed_tree_hash=tree, previous_review_result_id=None, previous_rework_contract_id=None,
        previous_finding_fingerprints=(), created_at=NOW,
    )


def review(request_value, disposition, *, rule="rule", evidence="a.py"):
    finding = ArchitectFinding(f"F-{request_value.review_iteration}", rule, "high", "summary", (evidence,), f"fix-{rule}", "change")
    values = dict(
        review_request_id=request_value.review_request_id, task_id=request_value.task_id,
        execution_id=request_value.execution_id, review_iteration=request_value.review_iteration,
        disposition=disposition, reviewed_head=request_value.reviewed_head,
        expected_head=request_value.expected_current_head, reviewed_tree_hash=request_value.reviewed_tree_hash,
        findings=(finding,) if disposition is ArchitectReviewDisposition.FAIL else (),
        allowed_rework_scope=(evidence,) if disposition is ArchitectReviewDisposition.FAIL else (),
        required_validations=("pytest",) if disposition is ArchitectReviewDisposition.FAIL else (),
        provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    return create_review_result(**values)


class Repository:
    root = Path(".").resolve()
    head = "5" * 40

    def __init__(self, states): self.states = iter(states)
    def inspect(self):
        state = next(self.states)
        return OrchestrationDecision("TASK-9000", state, None, "topic", "head", (), NOW)


class Architect:
    def __init__(self, results): self.results = iter(results); self.calls = 0
    def review(self, _request, *, schema_path): self.calls += 1; return next(self.results)


class Projection:
    def __init__(self): self.calls = []
    def project_architect_result(self, result): self.calls.append(result.disposition); return f"{len(self.calls) + 4}" * 40
    def publish_result_only(self, result): self.calls.append(("only", result.disposition)); return "9" * 40
    def push(self, branch): self.calls.append(("push", branch)); return "9" * 40


class Codex:
    def __init__(self): self.calls = 0
    def run_once(self):
        self.calls += 1
        execution = CodexExecutionResult(
            f"codex-{self.calls}", "TASK-9000", "1" * 40, "2" * 40, ("a.py",),
            (ValidationResult("pytest", True),), ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT,
        )
        runner = RunnerResult(
            RunnerStatus.EXECUTED, "TASK-9000", AIDPState.REWORK_REQUIRED,
            AIDPState.READY_FOR_ARCHITECT, "ok", execution,
        )
        decision = ControlPlaneDecision(
            ControlPlaneAction.EXECUTE, "TASK-9000", AIDPState.REWORK_REQUIRED, "topic", "head", "ok",
        )
        control = ControlPlaneResult(decision, ControlPlaneAction.READY_FOR_ARCHITECT, runner_result=runner)
        publish = PublishResult("topic", "exec", "review.json", "review", "PUSHED", AIDPState.READY_FOR_ARCHITECT)
        return TriggerResult(TriggerStatus.PUBLISHED, f"contract-{self.calls}", ConsumptionState.REVIEW_PUBLISHED,
                             control_plane_result=control, publish_result=publish)


def test_fail_rework_pass_path_stops_at_product_owner(tmp_path):
    first = request(0, tree="4" * 40)
    second = request(1, tree="5" * 40)
    repository = Repository([
        AIDPState.READY_FOR_ARCHITECT, AIDPState.REWORK_REQUIRED,
        AIDPState.READY_FOR_ARCHITECT, AIDPState.WAITING_FOR_PRODUCT_OWNER,
        AIDPState.WAITING_FOR_PRODUCT_OWNER,
    ])
    architect = Architect([review(first, ArchitectReviewDisposition.FAIL), review(second, ArchitectReviewDisposition.PASS)])
    codex = Codex()
    requests = iter((first, second))
    lifecycle = AIDPLifecycleOnce(
        repository, codex=codex, architect=architect, runtime_store=LocalRuntimeStore(tmp_path),
        projection=Projection(), request_factory=lambda _task: next(requests), clock=lambda: NOW,
    )
    assert lifecycle.run_once().state is AIDPState.REWORK_REQUIRED
    assert lifecycle.run_once().state is AIDPState.READY_FOR_ARCHITECT
    assert lifecycle.run_once().state is AIDPState.WAITING_FOR_PRODUCT_OWNER
    assert lifecycle.run_once().status is LifecycleStatus.NO_ACTION
    assert architect.calls == 2 and codex.calls == 1


def test_two_reworks_then_pass(tmp_path):
    requests = [request(0, tree="4" * 40), request(1, tree="5" * 40), request(2, tree="6" * 40)]
    repository = Repository([
        AIDPState.READY_FOR_ARCHITECT, AIDPState.REWORK_REQUIRED, AIDPState.READY_FOR_ARCHITECT,
        AIDPState.REWORK_REQUIRED, AIDPState.READY_FOR_ARCHITECT, AIDPState.WAITING_FOR_PRODUCT_OWNER,
    ])
    results = [
        review(requests[0], ArchitectReviewDisposition.FAIL, rule="r1", evidence="a.py"),
        review(requests[1], ArchitectReviewDisposition.FAIL, rule="r2", evidence="a.py"),
        review(requests[2], ArchitectReviewDisposition.PASS),
    ]
    lifecycle = AIDPLifecycleOnce(
        repository, codex=Codex(), architect=Architect(results), runtime_store=LocalRuntimeStore(tmp_path),
        projection=Projection(), request_factory=lambda _task: requests.pop(0), clock=lambda: NOW,
    )
    states = [lifecycle.run_once().state for _ in range(5)]
    assert states == [AIDPState.REWORK_REQUIRED, AIDPState.READY_FOR_ARCHITECT,
                      AIDPState.REWORK_REQUIRED, AIDPState.READY_FOR_ARCHITECT,
                      AIDPState.WAITING_FOR_PRODUCT_OWNER]
