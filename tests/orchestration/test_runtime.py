from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from aidp_orchestration.architect_review import create_review_request, create_review_result
from aidp_orchestration.contracts import (
    ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance, CodexExecutionResult, ExecutionStatus,
    ReworkContract, ScopeCompliance, ValidationResult,
)
from aidp_orchestration.runtime import LocalRuntimeStore


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def test_latest_execution_result_preserves_authoritative_failure_evidence(tmp_path) -> None:
    store = LocalRuntimeStore(tmp_path)
    first = CodexExecutionResult(
        "exec-1", "AIDP-INFRA-0002", "1" * 40, "2" * 40, ("a.py",),
        (ValidationResult("pytest", False, "exit_code=1"),), ExecutionStatus.TEST_FAILED,
        "one or more validations failed", ScopeCompliance.COMPLIANT,
    )
    store.persist_result(first)
    assert store.latest_execution_result("AIDP-INFRA-0002") == first
    assert store.latest_execution_result("AIDP-INFRA-9999") is None


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


def _review_result(
    *, iteration=0, disposition=ArchitectReviewDisposition.FAIL,
    task_id="AIDP-INFRA-0001", expected_parent="a" * 40,
):
    findings = ()
    scope = ()
    validators = ()
    failure_reason = "blocked" if disposition is ArchitectReviewDisposition.BLOCKED else None
    if disposition is ArchitectReviewDisposition.FAIL:
        findings = (ArchitectFinding(
            f"F-{iteration}", "rule", "high", "finding", ("a.py",), "fix", "change",
        ),)
        scope = ("a.py",)
        validators = ("pytest",)
    return create_review_result(
        review_request_id=f"{iteration + 1:x}" * 64, task_id=task_id,
        execution_id=f"execution-{iteration}", review_iteration=iteration,
        disposition=disposition, reviewed_head="b" * 40, expected_head=expected_parent,
        reviewed_tree_hash="c" * 40, findings=findings, allowed_rework_scope=scope,
        required_validations=validators,
        provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
        failure_reason=failure_reason, authority_claims=(), created_at=NOW,
    )


def _persist_authorized_rework(store, result, projection_commit):
    store.persist_architect_result(result)
    store.append_projection_event(result.review_result_id, {
        "task_id": result.task_id, "review_result_id": result.review_result_id,
        "branch": "product", "expected_parent": result.expected_head,
        "projection_commit": projection_commit, "disposition": result.disposition,
        "state": "PUBLISHED", "timestamp": NOW,
    })
    contract = ReworkContract(
        result.task_id, result.review_iteration + 1, projection_commit,
        result.allowed_rework_scope,
        tuple(f"{finding.fingerprint}:{finding.rule_id}:{finding.action_id}" for finding in result.findings),
        result.required_validations, result.created_at,
    )
    contract_id = contract.canonical_id(result.review_result_id)
    return contract, contract_id, store.persist_rework_contract(
        contract_id, contract, result.review_result_id,
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
    for review_iteration, projection_commit in ((0, "d" * 40), (1, "e" * 40)):
        result = _review_result(iteration=review_iteration)
        _, contract_id, _ = _persist_authorized_rework(store, result, projection_commit)
        expected_ids.append(contract_id)
    assert store.rework_contract_id("AIDP-INFRA-0001", 1, expected_head="d" * 40) == expected_ids[0]
    assert store.rework_contract_id("AIDP-INFRA-0001", 2, expected_head="e" * 40) == expected_ids[1]
    with pytest.raises(ValueError, match="missing or ambiguous"):
        store.rework_contract_id("AIDP-INFRA-0001", 3, expected_head="a" * 40)


@pytest.mark.parametrize("mutation", (
    "missing_payload", "partial_payload", "wrong_task", "unauthorized_task", "wrong_iteration",
    "stale_head", "findings", "scope", "validators", "timestamp", "contract_id",
    "filename", "authorizing_result",
))
def test_rework_lineage_rejects_forged_or_malformed_authority(tmp_path, mutation):
    store = LocalRuntimeStore(tmp_path)
    result = _review_result()
    contract, contract_id, path = _persist_authorized_rework(store, result, "d" * 40)
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
        value["rework_contract"]["expected_head"] = "e" * 40
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
        store.rework_contract_id("AIDP-INFRA-0001", 1, expected_head="d" * 40)


def test_self_consistent_forged_rework_without_persisted_fail_is_rejected(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    contract = ReworkContract(
        "AIDP-INFRA-0001", 1, "d" * 40, ("product.py",),
        ("fabricated",), ("unauthorized-validator",), NOW,
    )
    forged_result_id = "f" * 64
    forged_contract_id = contract.canonical_id(forged_result_id)
    store.persist_rework_contract(forged_contract_id, contract, forged_result_id)
    with pytest.raises(ValueError, match="is missing"):
        store.rework_contract_id("AIDP-INFRA-0001", 1, expected_head="d" * 40)


@pytest.mark.parametrize("disposition", (
    ArchitectReviewDisposition.PASS, ArchitectReviewDisposition.BLOCKED,
))
def test_non_fail_architect_result_cannot_authorize_rework(tmp_path, disposition):
    store = LocalRuntimeStore(tmp_path)
    result = _review_result(disposition=disposition)
    store.persist_architect_result(result)
    contract = ReworkContract(result.task_id, 1, "d" * 40, ("a.py",), ("fabricated",), ("pytest",), NOW)
    contract_id = contract.canonical_id(result.review_result_id)
    store.persist_rework_contract(contract_id, contract, result.review_result_id)
    with pytest.raises(ValueError, match="only ArchitectReviewResult.FAIL"):
        store.rework_contract_id(result.task_id, 1, expected_head="d" * 40)


def test_malformed_and_wrong_identity_authorizing_results_are_rejected(tmp_path):
    result = _review_result()
    contract = ReworkContract(
        result.task_id, 1, "d" * 40, result.allowed_rework_scope,
        tuple(f"{finding.fingerprint}:{finding.rule_id}:{finding.action_id}" for finding in result.findings),
        result.required_validations, result.created_at,
    )
    for index, malformed in enumerate((
        {"wrong": {}}, {"architect_review_result": {"review_result_id": result.review_result_id}},
    )):
        candidate = LocalRuntimeStore(tmp_path / str(index))
        contract_id = contract.canonical_id(result.review_result_id)
        candidate.persist_rework_contract(contract_id, contract, result.review_result_id)
        path = candidate.root / "architect-review-results" / f"{result.review_result_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(malformed), encoding="utf-8")
        with pytest.raises(ValueError, match="is malformed"):
            candidate.rework_contract_id(result.task_id, 1, expected_head="d" * 40)
    source = LocalRuntimeStore(tmp_path / "source")
    persisted_result = source.persist_architect_result(result)
    wrong_id = "f" * 64
    candidate = LocalRuntimeStore(tmp_path / "wrong-id")
    contract_id = contract.canonical_id(wrong_id)
    candidate.persist_rework_contract(contract_id, contract, wrong_id)
    result_path = candidate.root / "architect-review-results" / f"{wrong_id}.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_bytes(persisted_result.read_bytes())
    with pytest.raises(ValueError, match="identity mismatch"):
        candidate.rework_contract_id(result.task_id, 1, expected_head="d" * 40)


@pytest.mark.parametrize("mismatch", (
    "task", "iteration", "head", "findings", "scope", "validators", "timestamp",
))
def test_recomputed_contract_identity_cannot_override_fail_result_authority(tmp_path, mismatch):
    store = LocalRuntimeStore(tmp_path)
    result = _review_result()
    store.persist_architect_result(result)
    store.append_projection_event(result.review_result_id, {
        "task_id": result.task_id, "review_result_id": result.review_result_id,
        "branch": "product", "expected_parent": result.expected_head,
        "projection_commit": "d" * 40, "disposition": result.disposition,
        "state": "PUBLISHED", "timestamp": NOW,
    })
    values = {
        "task_id": result.task_id, "review_iteration": 1, "expected_head": "d" * 40,
        "allowed_rework_scope": result.allowed_rework_scope,
        "findings": tuple(f"{finding.fingerprint}:{finding.rule_id}:{finding.action_id}" for finding in result.findings),
        "required_validations": result.required_validations, "created_at": result.created_at,
    }
    if mismatch == "task": values["task_id"] = "TASK-0001"
    elif mismatch == "iteration": values["review_iteration"] = 2
    elif mismatch == "head": values["expected_head"] = "e" * 40
    elif mismatch == "findings": values["findings"] = ("changed",)
    elif mismatch == "scope": values["allowed_rework_scope"] = ("other.py",)
    elif mismatch == "validators": values["required_validations"] = ("other",)
    elif mismatch == "timestamp": values["created_at"] = datetime(2026, 9, 2, tzinfo=timezone.utc)
    contract = ReworkContract(**values)
    contract_id = contract.canonical_id(result.review_result_id)
    path = store.persist_rework_contract(contract_id, contract, result.review_result_id)
    if mismatch in {"task", "iteration"}:
        target = store.root / "rework-contracts" / result.task_id / f"1-{contract_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        path.replace(target)
    with pytest.raises(ValueError):
        store.rework_contract_id(result.task_id, 1, expected_head="d" * 40)


@pytest.mark.parametrize("field", ("expected_parent", "projection_commit", "disposition", "task_id"))
def test_wrong_published_projection_cannot_authorize_rework(tmp_path, field):
    store = LocalRuntimeStore(tmp_path)
    result = _review_result()
    contract, _, _ = _persist_authorized_rework(store, result, "d" * 40)
    projection = store.root / "lifecycle-projections" / f"{result.review_result_id}.jsonl"
    wrapper = json.loads(projection.read_text(encoding="utf-8"))
    wrapper["projection_event"][field] = "wrong"
    projection.write_text(json.dumps(wrapper), encoding="utf-8")
    with pytest.raises(ValueError, match="projection"):
        store.rework_contract_id(result.task_id, contract.review_iteration, expected_head="d" * 40)
