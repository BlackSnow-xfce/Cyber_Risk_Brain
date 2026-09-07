from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from aidp_orchestration.architect_review import create_review_request, create_review_result
from aidp_orchestration.contracts import (
    AIDPState, ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance,
    ArchitectReviewRecoveryAuthorityV1, ArchitectTaskContract, CodexExecutionResult,
    ContractInboxItem, ExecutionAttemptV1, ExecutionStatus, OrchestrationDecision,
    ReworkContract, ScopeCompliance, ValidationResult, canonical_digest,
)
from aidp_orchestration.lifecycle import AIDPLifecycleOnce
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.trigger_publisher import AIDPWatchOnce, LocalContractInbox, serialize_contract_inbox_item


NOW = datetime(2026, 9, 7, 20, tzinfo=timezone.utc)


class Repo:
    def __init__(self, root: Path, states=(AIDPState.READY_FOR_ARCHITECT,)):
        self.root = root
        self.ai_root = root / ".ai"
        self.head = "3" * 40
        self.states = iter(states)
        self.task_namespace = "infrastructure"

    def inspect(self):
        return OrchestrationDecision("AIDP-INFRA-0002", next(self.states), None, "branch", self.head, (), NOW)

    def _git(self, *args):
        if args == ("rev-parse", "--git-common-dir"): return str(self.root / ".git")
        if args == ("remote", "get-url", "origin"): return "origin"
        if args[0] == "rev-parse" and args[1].endswith("^{tree}"): return "4" * 40
        raise AssertionError(args)

    def accepts_task_id(self, task_id): return task_id.startswith("AIDP-INFRA-")


class Architect:
    def __init__(self): self.calls = 0
    def review(self, request, *, schema_path):
        self.calls += 1
        return create_review_result(
            review_request_id=request.review_request_id, task_id=request.task_id,
            execution_id=request.execution_id, review_iteration=request.review_iteration,
            disposition=ArchitectReviewDisposition.PASS, reviewed_head=request.reviewed_head,
            expected_head=request.expected_current_head, reviewed_tree_hash=request.reviewed_tree_hash,
            findings=(), allowed_rework_scope=(), required_validations=(),
            provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
            failure_reason=None, authority_claims=(), created_at=NOW,
        )
    def revalidate(self, request): return None


class Projection:
    def project_architect_result(self, result): return "5" * 40
    def push(self, branch): return None


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_authority(authority, **changes):
    values = {field.name: getattr(authority, field.name) for field in fields(authority) if field.name != "authority_id"}
    values.update(changes)
    return ArchitectReviewRecoveryAuthorityV1(authority_id=canonical_digest(values), **values)


def _write_ingress_event(root: Path, authority_id: str, path: Path) -> None:
    content = path.read_bytes()
    blob = hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()
    (root / "architect-ingress.jsonl").write_text(json.dumps({"architect_ingress_event": {
        "contract_id": authority_id, "remote_commit": "f" * 40, "blob_id": blob,
        "status": "MATERIALIZED", "identity_kind": "contract_id",
    }}) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path):
    repository = Repo(tmp_path)
    runtime = LocalRuntimeStore(tmp_path / "runtime")
    inbox_root = tmp_path / "authority"
    original = ArchitectTaskContract(
        "AIDP-INFRA-0002", "task", "IMPLEMENTATION", "0" * 40, ("a.py",), ("no product",),
        ("pytest",), ("pass",), True, NOW,
    )
    LocalContractInbox(inbox_root).persist(ContractInboxItem("original", original, NOW))
    prior_request = create_review_request(
        task_id=original.task_id, review_iteration=0, execution_id="old", repository="repo",
        git_common_dir="git", branch="branch", remote_url="origin", authority_contract_id="original",
        authority_contract_digest=canonical_digest(original), original_allowed_scope=original.allowed_scope,
        original_prohibited_actions=original.prohibited_actions,
        original_validation_requirements=original.validation_requirements,
        original_acceptance_criteria=original.acceptance_criteria, product_owner_gate=True,
        review_envelope_path="old.json", review_envelope_digest="1" * 64,
        execution_status=ExecutionStatus.SUCCESS, start_commit="0" * 40, resulting_commit="1" * 40,
        review_envelope_commit="1" * 40, changed_files=("a.py",),
        validation_results=(ValidationResult("pytest", True, "passed"),),
        scope_compliance=ScopeCompliance.COMPLIANT, expected_current_head="1" * 40,
        current_head="1" * 40, reviewed_head="1" * 40, reviewed_tree_hash="4" * 40,
        previous_review_result_id=None, previous_rework_contract_id=None,
        previous_finding_fingerprints=(), created_at=NOW,
    )
    prior = create_review_result(
        review_request_id=prior_request.review_request_id, task_id=original.task_id,
        execution_id="old", review_iteration=0, disposition=ArchitectReviewDisposition.FAIL,
        reviewed_head="1" * 40, expected_head="1" * 40, reviewed_tree_hash="4" * 40,
        findings=(ArchitectFinding("finding", "rule", "HIGH", "summary", ("a.py",), "action", "change"),),
        allowed_rework_scope=("a.py",), required_validations=("pytest",),
        provenance=ArchitectReviewProvenance("p", "l", "m", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    result_path = runtime.persist_architect_result(prior)
    legacy = ReworkContract(original.task_id, 2, "1" * 40, ("a.py",), ("finding",), ("pytest",), NOW)
    legacy_id = "a" * 64
    legacy_path = runtime.root / "rework-contracts" / original.task_id / f"2-{legacy_id}.json"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(json.dumps({"rework_contract": {
        "task_id": legacy.task_id, "review_iteration": legacy.review_iteration,
        "expected_head": legacy.expected_head, "allowed_rework_scope": list(legacy.allowed_rework_scope),
        "findings": list(legacy.findings), "required_validations": list(legacy.required_validations),
        "created_at": legacy.created_at.isoformat(),
    }}, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    LocalContractInbox(inbox_root).persist(ContractInboxItem(legacy_id, legacy, NOW))
    validations = (ValidationResult("pytest", True, "passed"),)
    execution = CodexExecutionResult(
        "exec", original.task_id, "1" * 40, "1" * 40, ("a.py",), validations,
        ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT,
    )
    execution_path = runtime.persist_result(execution)
    repository_id = canonical_digest(str(repository.root.resolve()).lower())
    runtime.persist_execution_attempt(ExecutionAttemptV1(
        "aidp-execution-attempt-v1", "exec", legacy_id, original.task_id, "infrastructure",
        repository_id, "1" * 40, "b" * 64, 1, 0, NOW,
    ))
    envelope = {
        "task_id": original.task_id, "execution_id": "exec", "branch": "branch",
        "start_commit": "1" * 40, "resulting_commit": "2" * 40,
        "execution_status": "SUCCESS", "changed_files": ["a.py"],
        "scope_compliance": "COMPLIANT",
        "validation_results": [{"name": "pytest", "passed": True, "detail": "passed"}],
        "published_at": NOW.isoformat(),
    }
    envelope_path = repository.ai_root / "orchestration/review-inbox/AIDP-INFRA-0002-exec.json"
    envelope_path.parent.mkdir(parents=True)
    envelope_path.write_text(json.dumps({"architect_review_envelope": envelope}, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    values = dict(
        schema_version="aidp-architect-review-recovery-authority-v1", task_id=original.task_id,
        authorizing_review_result_id=prior.review_result_id,
        authorizing_review_result_digest=_digest(result_path), legacy_rework_contract_id=legacy_id,
        legacy_rework_contract_digest=_digest(legacy_path), legacy_authorizing_lineage_missing=True,
        execution_id="exec", execution_start_head="1" * 40, implementation_commit="2" * 40,
        lifecycle_projection_commit="3" * 40, changed_files=("a.py",),
        scope_compliance=ScopeCompliance.COMPLIANT, validator_evidence_digest=canonical_digest(validations),
        execution_result_digest=_digest(execution_path), review_envelope_id=canonical_digest(envelope),
        review_envelope_digest=_digest(envelope_path), repository_id=repository_id, branch="branch",
        expected_lifecycle_state=AIDPState.READY_FOR_ARCHITECT, issued_by="product-owner",
        issued_at=NOW - timedelta(minutes=1), expires_at=NOW + timedelta(hours=1),
    )
    authority = ArchitectReviewRecoveryAuthorityV1(authority_id=canonical_digest(values), **values)
    authority_path = LocalContractInbox(inbox_root).persist(ContractInboxItem(authority.authority_id, authority, NOW))
    _write_ingress_event(inbox_root, authority.authority_id, authority_path)
    return repository, runtime, inbox_root, authority


def test_valid_authority_launches_one_architect_review_and_is_consumed(tmp_path):
    repository, runtime, inbox, authority = _fixture(tmp_path)
    repository.states = iter((AIDPState.READY_FOR_ARCHITECT, AIDPState.READY_FOR_ARCHITECT, AIDPState.WAITING_FOR_PRODUCT_OWNER))
    architect = Architect()
    result = AIDPLifecycleOnce(
        repository, codex=object(), architect=architect, runtime_store=runtime, projection=Projection(),
        authority_inbox_root=inbox, clock=lambda: NOW,
    ).run_once()
    assert result.state is AIDPState.WAITING_FOR_PRODUCT_OWNER
    assert architect.calls == 1
    assert runtime.architect_review_recovery_authority_claimed(authority.authority_id)
    with pytest.raises(RuntimeError, match="authority replay"):
        runtime.claim_architect_review_recovery_authority(authority, "9" * 64)


@pytest.mark.parametrize("field,value", [
    ("execution_id", "wrong"), ("execution_start_head", "9" * 40),
    ("implementation_commit", "8" * 40), ("lifecycle_projection_commit", "7" * 40),
    ("changed_files", ("a.py", "extra.py")), ("validator_evidence_digest", "6" * 64),
    ("authorizing_review_result_digest", "5" * 64), ("legacy_rework_contract_digest", "4" * 64),
    ("review_envelope_digest", "3" * 64), ("repository_id", "2" * 64),
    ("branch", "wrong"),
    ("expires_at", NOW),
])
def test_tampered_or_mismatched_authority_fails_before_review(tmp_path, field, value):
    repository, runtime, inbox, authority = _fixture(tmp_path)
    altered = _replace_authority(authority, **{field: value})
    authority_path = inbox / "contract-inbox" / f"{authority.authority_id}.json"
    authority_path.unlink()
    altered_path = LocalContractInbox(inbox).persist(ContractInboxItem(altered.authority_id, altered, NOW))
    _write_ingress_event(inbox, altered.authority_id, altered_path)
    repository.states = iter((AIDPState.READY_FOR_ARCHITECT, AIDPState.READY_FOR_ARCHITECT))
    architect = Architect()
    result = AIDPLifecycleOnce(repository, codex=object(), architect=architect, runtime_store=runtime, projection=Projection(), authority_inbox_root=inbox, clock=lambda: NOW).run_once()
    assert result.status.value == "BLOCKED"
    assert architect.calls == 0


def test_review_recovery_authority_is_not_a_codex_contract(tmp_path):
    repository, _, _, authority = _fixture(tmp_path)
    inbox = tmp_path / "review-only-inbox"
    LocalContractInbox(inbox).persist(ContractInboxItem(authority.authority_id, authority, NOW))
    result = AIDPWatchOnce(
        repository, runtime_root=inbox, writer=object(), control_plane=object(), publisher=object(),
    ).run_once()
    assert result.status.value == "NO_ACTION"
    assert result.contract_id is None
    assert not (inbox / "consumption-events.jsonl").exists()


def test_review_recovery_authority_rejects_duplicate_unknown_and_missing_fields(tmp_path):
    _, _, _, authority = _fixture(tmp_path)
    encoded = serialize_contract_inbox_item(ContractInboxItem(authority.authority_id, authority, NOW))
    duplicate = encoded.replace('"schema_version":', '"schema_version":"forged","schema_version":', 1)
    with pytest.raises(ValueError, match="duplicate JSON field"):
        LocalContractInbox.parse(duplicate.encode())
    payload = json.loads(encoded)
    payload["contract_inbox_item"]["contract"]["unknown"] = "forged"
    with pytest.raises(ValueError, match="invalid ArchitectReviewRecoveryAuthorityV1 schema"):
        LocalContractInbox.parse(json.dumps(payload).encode())
    del payload["contract_inbox_item"]["contract"]["unknown"]
    del payload["contract_inbox_item"]["contract"]["execution_id"]
    with pytest.raises(ValueError, match="invalid ArchitectReviewRecoveryAuthorityV1 schema"):
        LocalContractInbox.parse(json.dumps(payload).encode())


def test_concurrent_review_recovery_claim_has_exactly_one_winner(tmp_path):
    _, runtime, _, authority = _fixture(tmp_path)
    barrier = threading.Barrier(2)
    results = []

    def claim():
        barrier.wait()
        try:
            runtime.claim_architect_review_recovery_authority(authority, "9" * 64)
            results.append("won")
        except RuntimeError:
            results.append("replay")

    workers = [threading.Thread(target=claim) for _ in range(2)]
    for worker in workers: worker.start()
    for worker in workers: worker.join()
    assert sorted(results) == ["replay", "won"]
