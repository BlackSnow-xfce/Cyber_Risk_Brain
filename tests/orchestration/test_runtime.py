from __future__ import annotations

import json
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
    expected_ids = []
    for iteration in (1, 2):
        contract = ReworkContract(
            "AIDP-INFRA-0001", iteration, "a" * 40, ("a.py",),
            (f"finding-{iteration}",), ("pytest",), NOW,
        )
        authorizing = str(iteration) * 64
        contract_id = contract.canonical_id(authorizing)
        expected_ids.append(contract_id)
        store.persist_rework_contract(contract_id, contract, authorizing)
    assert store.rework_contract_id("AIDP-INFRA-0001", 1, expected_head="a" * 40) == expected_ids[0]
    assert store.rework_contract_id("AIDP-INFRA-0001", 2, expected_head="a" * 40) == expected_ids[1]
    with pytest.raises(ValueError, match="missing or ambiguous"):
        store.rework_contract_id("AIDP-INFRA-0001", 3, expected_head="a" * 40)


@pytest.mark.parametrize("mutation", (
    "missing_payload", "partial_payload", "wrong_task", "unauthorized_task", "wrong_iteration",
    "stale_head", "findings", "scope", "validators", "timestamp", "contract_id",
    "filename", "authorizing_result",
))
def test_rework_lineage_rejects_forged_or_malformed_authority(tmp_path, mutation):
    store = LocalRuntimeStore(tmp_path)
    contract = ReworkContract(
        "AIDP-INFRA-0001", 1, "a" * 40, ("a.py",), ("finding",), ("pytest",), NOW,
    )
    authorizing = "b" * 64
    contract_id = contract.canonical_id(authorizing)
    path = store.persist_rework_contract(contract_id, contract, authorizing)
    value = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "missing_payload":
        value.pop("rework_contract")
    elif mutation == "partial_payload":
        value["rework_contract"].pop("findings")
    elif mutation == "wrong_task":
        value["rework_contract"]["task_id"] = "TASK-0001"
    elif mutation == "unauthorized_task":
        value["rework_contract"]["task_id"] = "UNAUTHORIZED"
    elif mutation == "wrong_iteration":
        value["rework_contract"]["review_iteration"] = 2
    elif mutation == "stale_head":
        value["rework_contract"]["expected_head"] = "c" * 40
    elif mutation == "findings":
        value["rework_contract"]["findings"] = ["changed"]
    elif mutation == "scope":
        value["rework_contract"]["allowed_rework_scope"] = ["other.py"]
    elif mutation == "validators":
        value["rework_contract"]["required_validations"] = ["other"]
    elif mutation == "timestamp":
        value["rework_contract"]["created_at"] = "2026-09-01T00:00:00"
    elif mutation == "contract_id":
        value["contract_id"] = "c" * 64
    elif mutation == "authorizing_result":
        value["authorizing_review_result_id"] = "c" * 64
    path.write_text(json.dumps(value), encoding="utf-8")
    if mutation == "filename":
        renamed = path.with_name(f"1-{'c' * 64}.json")
        path.rename(renamed)
    with pytest.raises(ValueError):
        store.rework_contract_id("AIDP-INFRA-0001", 1, expected_head="a" * 40)
