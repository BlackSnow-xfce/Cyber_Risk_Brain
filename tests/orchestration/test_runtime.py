from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aidp_orchestration.architect_review import create_review_request, create_review_result
from aidp_orchestration.contracts import (
    ArchitectReviewDisposition, ArchitectReviewProvenance, ExecutionStatus, ReworkContract, ScopeCompliance,
    ValidationResult,
)
from aidp_orchestration.runtime import LocalRuntimeStore


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _request():
    return create_review_request(
        task_id="TASK-9000", review_iteration=0, execution_id="exec", repository="repo",
        git_common_dir="git", branch="branch", remote_url="origin", authority_contract_id="contract",
        authority_contract_digest="a" * 64, original_allowed_scope=("a.py",),
        original_prohibited_actions=("no product",), original_validation_requirements=("pytest",),
        original_acceptance_criteria=("pass",), product_owner_gate=True, review_envelope_path="review.json",
        review_envelope_digest="b" * 64, execution_status=ExecutionStatus.SUCCESS,
        start_commit="1" * 40, resulting_commit="2" * 40, review_envelope_commit="3" * 40,
        changed_files=("a.py",), validation_results=(ValidationResult("pytest", True),),
        scope_compliance=ScopeCompliance.COMPLIANT, expected_current_head="3" * 40,
        current_head="3" * 40, reviewed_head="2" * 40, reviewed_tree_hash="4" * 40,
        previous_review_result_id=None, previous_rework_contract_id=None,
        previous_finding_fingerprints=(), created_at=NOW,
    )


def _result(request):
    provenance = ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1")
    return create_review_result(
        review_request_id=request.review_request_id, task_id=request.task_id,
        execution_id=request.execution_id, review_iteration=0,
        disposition=ArchitectReviewDisposition.PASS, reviewed_head=request.reviewed_head,
        expected_head=request.expected_current_head, reviewed_tree_hash=request.reviewed_tree_hash,
        findings=(), allowed_rework_scope=(), required_validations=(), provenance=provenance,
        failure_reason=None, authority_claims=(), created_at=NOW,
    )


def test_architect_runtime_records_are_immutable_and_idempotent(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    request = _request()
    result = _result(request)
    assert store.persist_architect_request(request) == store.persist_architect_request(request)
    assert store.persist_architect_result(result) == store.persist_architect_result(result)
    assert store.persist_architect_attempt(request.review_request_id, {"state": "LAUNCHING"}).is_file()
    assert store.architect_attempt_exists(request.review_request_id)
    with pytest.raises(RuntimeError, match="collision"):
        store.persist_architect_attempt(request.review_request_id, {"state": "DIFFERENT"})


def test_rework_contract_lineage_is_exact_and_iteration_safe(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    for iteration, contract_id in ((1, "rework-one"), (2, "rework-two")):
        contract = ReworkContract(
            "AIDP-INFRA-0001", iteration, "a" * 40, ("a.py",),
            (f"finding-{iteration}",), ("pytest",), NOW,
        )
        store.persist_rework_contract(contract_id, contract)
    assert store.rework_contract_id("AIDP-INFRA-0001", 1) == "rework-one"
    assert store.rework_contract_id("AIDP-INFRA-0001", 2) == "rework-two"
    with pytest.raises(ValueError, match="missing or ambiguous"):
        store.rework_contract_id("AIDP-INFRA-0001", 3)
