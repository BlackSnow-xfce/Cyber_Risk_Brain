from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidp_orchestration.contracts import (
    ArchitectReviewDisposition, ArchitectReviewProvenance, CodexExecutionResult, ContractInboxItem,
    ExecutionAttemptV1, ExecutionStatus, ProductOwnerGateDependencyRecoveryAuthorityV1,
    ProductOwnerGateDependencyState, ScopeCompliance, ValidationResult, canonical_digest, utc_now,
)
from aidp_orchestration.architect_review import create_review_result
from aidp_orchestration.gate_dependency_recovery import RecoveringProductOwnerGateDependencyRunner
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.terminal_gate_dependency_recovery import (
    GateDependencyRecoveryJournal, TerminalGateDependencyRecovery,
    VerifiedGateDependencyRecoveryEvidence, execution_terms_digest,
)
from aidp_orchestration.trigger_publisher import LocalContractInbox, ProductOwnerGateDependencyRunner, serialize_contract_inbox_item
from test_product_owner_gate_dependency import _bound_authority, _git, _repository


def reidentify(authority, **changes):
    values = asdict(authority)
    values.update(changes)
    values.pop("authority_id")
    return ProductOwnerGateDependencyRecoveryAuthorityV1(authority_id=canonical_digest(values), **values)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def scenario(tmp_path, monkeypatch):
    root, _ = _repository(tmp_path)
    predecessor = _bound_authority(root)
    (root / "advancement.txt").write_text("approved advancement\n")
    _git(root, "add", "advancement.txt")
    _git(root, "commit", "-m", "approved advancement")
    source = _bound_authority(root, supersedes_authority_id="a" * 64)
    inbox_root = tmp_path / "shared"
    inbox = LocalContractInbox(inbox_root)
    for value in (predecessor, source):
        inbox.persist(ContractInboxItem(value.authority_id, value, utc_now()))
    runner = RecoveringProductOwnerGateDependencyRunner(AIDPRepository(root, task_namespace="infrastructure"),
                                                       runtime_root=inbox_root, architect=object())
    store = runner.store
    old_execution = "old-execution"
    claim = store.claim_product_owner_gate_dependency(predecessor, old_execution)
    terminal = store.persist_product_owner_gate_dependency_status(predecessor.authority_id, predecessor.dependency_id,
                                                                  "BLOCKED", "gate dependency blocked: CalledProcessError",
                                                                  execution_id=old_execution)
    now = utc_now()
    values = dict(schema_version="aidp-product-owner-gate-dependency-recovery-authority-v1",
                  predecessor_authority_id=predecessor.authority_id, predecessor_authority_digest=predecessor.expected_id(),
                  predecessor_claim_digest=sha(claim), predecessor_execution_id=old_execution, claim_state="CONSUMED",
                  terminal_status_digest=sha(terminal), terminal_state="BLOCKED",
                  terminal_reason="gate dependency blocked: CalledProcessError", dependency_id=source.dependency_id,
                  parent_task_id=source.parent_task_id, parent_lifecycle_digest=runner._parent_snapshot(source.parent_task_id),
                  execution_source_authority_id=source.authority_id, execution_source_digest=source.expected_id(),
                  execution_terms_digest=execution_terms_digest(source), evidence_digest="b" * 64,
                  product_owner_decision_digest="c" * 64, advancement_evidence_digest="d" * 64,
                  repository_id=source.repository_id, git_common_id=source.git_common_id,
                  repository_remote_id=source.repository_remote_id, branch=source.branch,
                  original_expected_head=predecessor.expected_head, expected_head=source.expected_head,
                  retry_budget=1, issued_by="authorized test issuer", issued_at=now, expires_at=now + timedelta(hours=1))
    authority = ProductOwnerGateDependencyRecoveryAuthorityV1(authority_id=canonical_digest(values), **values)
    evidence = VerifiedGateDependencyRecoveryEvidence(
        proposal_digest=authority.proposal_digest(), product_owner_decision_digest=authority.product_owner_decision_digest,
        evidence_digest=authority.evidence_digest, advancement_evidence_digest=authority.advancement_evidence_digest,
        predecessor_execution_id=old_execution, verifier_identity="test evidence service", product_owner_identity="test PO",
        permission="RECOVER_GATE_DEPENDENCY", approved=True, approved_advancement=True, mode="PRE_LAUNCH_FAILURE",
        pre_launch_failure_proven=True, no_active_process=True, residuals_clean=True, inventory_digest="e" * 64,
        result_digest=None, attempt_digest=None, execution_store_roots=(store.root,), verified_at=now,
        valid_until=now + timedelta(minutes=10),
    )
    verifier = SimpleNamespace(verify=lambda *args, **kwargs: evidence)
    runner.recovery_evidence_verifier = verifier
    coordinator = TerminalGateDependencyRecovery(runner, verifier)
    monkeypatch.setattr("aidp_orchestration.trigger_publisher.tempfile.gettempdir", lambda: str(tmp_path / "workspaces"))
    return SimpleNamespace(root=root, predecessor=predecessor, source=source, authority=authority, evidence=evidence,
                           runner=runner, coordinator=coordinator, store=store, inbox=inbox, claim=claim, terminal=terminal,
                           verifier=verifier, tmp_path=tmp_path)


def publish(s):
    s.inbox.persist(ContractInboxItem(s.authority.authority_id, s.authority, utc_now()))


def test_recovery_schema_round_trip_and_default_deny(scenario):
    s = scenario
    item = ContractInboxItem(s.authority.authority_id, s.authority, utc_now())
    encoded = serialize_contract_inbox_item(item)
    assert LocalContractInbox.parse(encoded.encode()) == item
    for mutation in ("unknown", "missing", "duplicate", "boolean_budget"):
        payload = json.loads(encoded)
        c = payload["contract_inbox_item"]["contract"]
        if mutation == "unknown": c["unknown"] = True
        elif mutation == "missing": del c["evidence_digest"]
        elif mutation == "boolean_budget": c["retry_budget"] = True
        raw = json.dumps(payload)
        if mutation == "duplicate": raw = raw.replace('"retry_budget": 1', '"retry_budget": 1, "retry_budget": 1')
        with pytest.raises(ValueError): LocalContractInbox.parse(raw.encode())
    s.runner.recovery_evidence_verifier = None
    publish(s)
    result = s.runner.run_once()
    assert "verifier is not configured" in result.reason
    assert not s.coordinator.journal.reservations()


@pytest.mark.parametrize("field,value", [
    ("predecessor_authority_id", "f" * 64), ("predecessor_authority_digest", "f" * 64),
    ("predecessor_claim_digest", "f" * 64), ("predecessor_execution_id", "wrong-execution"),
    ("terminal_status_digest", "f" * 64), ("terminal_reason", "different reason"),
    ("dependency_id", "AIDP-PO-DEP-0003"), ("parent_task_id", "AIDP-INFRA-0003"),
    ("parent_lifecycle_digest", "f" * 64), ("execution_source_authority_id", "f" * 64),
    ("execution_source_digest", "f" * 64), ("execution_terms_digest", "f" * 64),
    ("repository_id", "f" * 64), ("git_common_id", "f" * 64), ("repository_remote_id", "f" * 64),
    ("branch", "other"), ("original_expected_head", "f" * 40), ("expected_head", "f" * 40),
])
def test_mismatched_recovery_bindings_are_rejected(scenario, field, value):
    s = scenario
    result = s.coordinator.run_once(reidentify(s.authority, **{field: value}), s.inbox.pending())
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert not s.coordinator.journal.reservations()


@pytest.mark.parametrize("changes", [
    {"permission": "ACCEPT"}, {"approved": False}, {"product_owner_identity": ""},
    {"verifier_identity": ""}, {"proposal_digest": "f" * 64}, {"product_owner_decision_digest": "f" * 64},
    {"evidence_digest": "f" * 64}, {"advancement_evidence_digest": "f" * 64}, {"approved_advancement": False},
    {"predecessor_execution_id": "wrong"}, {"no_active_process": False}, {"residuals_clean": False},
    {"inventory_digest": ""}, {"mode": "UNKNOWN_EXECUTION_OUTCOME"}, {"pre_launch_failure_proven": False},
    {"mode": "PERSISTED_FAILURE"}, {"execution_store_roots": ()},
])
def test_authenticated_approval_cannot_override_evidence_guards(scenario, changes):
    s = scenario
    s.verifier.verify = lambda *args, **kwargs: replace(s.evidence, **changes)
    result = s.coordinator.run_once(s.authority, s.inbox.pending())
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert not s.coordinator.journal.reservations()


def test_expiry_and_evidence_freshness(scenario):
    s = scenario
    now = utc_now()
    expired = reidentify(s.authority, issued_at=now-timedelta(days=2), expires_at=now-timedelta(days=1))
    with pytest.raises(ValueError): s.coordinator.validate(expired, s.inbox.pending())
    s.verifier.verify = lambda *args, **kwargs: replace(s.evidence, valid_until=now-timedelta(seconds=1))
    with pytest.raises(PermissionError): s.coordinator.validate(s.authority, s.inbox.pending())


def test_missing_result_with_contradictory_attempt_is_blocked(scenario):
    s = scenario
    path = s.store.root / "execution-attempts" / "old-execution.json"
    path.parent.mkdir()
    path.write_text("{}")
    with pytest.raises(ValueError, match="contradictory"):
        s.coordinator.validate(s.authority, s.inbox.pending())


def test_persisted_failure_requires_bound_result_and_attempt(scenario):
    s = scenario
    p = s.predecessor
    attempt = ExecutionAttemptV1("aidp-execution-attempt-v1", "old-execution", p.authority_id, p.dependency_id,
                                 "product-owner-gate-dependency", p.repository_id, p.expected_head,
                                 canonical_digest({"allowed": p.allowed_scope, "prohibited": p.prohibited_actions}),
                                 0, 0, utc_now())
    ap = s.store.persist_execution_attempt(attempt)
    result = CodexExecutionResult("old-execution", p.dependency_id, p.expected_head, p.expected_head,
                                  (), (), ExecutionStatus.ERROR, "failed", ScopeCompliance.COMPLIANT)
    rp = s.store.persist_result(result)
    evidence = replace(s.evidence, mode="PERSISTED_FAILURE", pre_launch_failure_proven=False,
                       attempt_digest=sha(ap), result_digest=sha(rp))
    s.verifier.verify = lambda *args, **kwargs: evidence
    assert s.coordinator.validate(s.authority, s.inbox.pending())[0] == s.source
    payload = json.loads(rp.read_text())
    payload["codex_execution_result"]["status"] = "SUCCESS"
    rp.write_text(json.dumps(payload))
    evidence = replace(evidence, result_digest=sha(rp))
    with pytest.raises(ValueError, match="persisted failure"):
        s.coordinator.validate(s.authority, s.inbox.pending())


@pytest.mark.parametrize("mutation", ["dirty", "head", "parent", "claim", "status"])
def test_changed_repository_or_history_is_blocked(scenario, mutation):
    s = scenario
    if mutation == "dirty": (s.root / "untracked.txt").write_text("dirty")
    elif mutation == "head": _git(s.root, "commit", "--allow-empty", "-m", "unapproved advancement")
    elif mutation == "parent": (s.root / ".ai/tasks/review/AIDP-INFRA-0002.md").write_text("altered")
    elif mutation == "claim": s.claim.write_text("{}")
    else: s.terminal.write_text("{}")
    with pytest.raises((ValueError, OSError)):
        s.coordinator.validate(s.authority, s.inbox.pending())


def test_exact_source_and_recovery_ambiguity(scenario):
    s = scenario
    other = _bound_authority(s.root, supersedes_authority_id="a" * 64)
    s.inbox.persist(ContractInboxItem(other.authority_id, other, utc_now()))
    with pytest.raises(ValueError):
        s.coordinator.validate(reidentify(s.authority, execution_source_authority_id=other.authority_id), s.inbox.pending())
    with pytest.raises(PermissionError):
        s.coordinator.validate(reidentify(s.authority, execution_source_authority_id=other.authority_id,
                                         execution_source_digest=other.expected_id()), s.inbox.pending())
    publish(s)
    newer = reidentify(s.authority, issued_at=s.authority.issued_at+timedelta(seconds=1))
    s.inbox.persist(ContractInboxItem(newer.authority_id, newer, utc_now()))
    assert "ambiguous" in s.runner.run_once().reason
    assert not s.coordinator.journal.reservations()


def test_atomic_reservation_concurrency_replay_and_ordinary_consumption(scenario):
    s = scenario
    def reserve():
        try:
            return GateDependencyRecoveryJournal(s.store).reserve(s.authority)
        except RuntimeError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(lambda _: reserve(), range(2)))
    assert sum(value is not None for value in values) == 1
    reservation = next(value for value in values if value is not None)
    assert reservation["execution_id"] != s.authority.predecessor_execution_id
    assert "relaunch prohibited" in s.runner.run_once().reason
    ordinary = ProductOwnerGateDependencyRunner(s.runner.repository, runtime_root=s.inbox.root.parent, architect=object())
    assert "reservation" in ordinary.run_once().reason
    with pytest.raises(RuntimeError): s.coordinator.journal.reserve(s.authority)


@pytest.mark.parametrize("boundary", ["AUTHORIZED", "RESERVED", "LAUNCH_INTENT", "STARTED", "RESULT_RECORDED", "REVIEWED"])
def test_audit_failure_blocks_and_never_relaunches_reserved_work(scenario, monkeypatch, boundary):
    s = scenario
    install_successful_execution(s, monkeypatch)
    original = GateDependencyRecoveryJournal.event
    def event(self, authority, kind, **kwargs):
        if kind == boundary: raise OSError("audit unavailable")
        return original(self, authority, kind, **kwargs)
    monkeypatch.setattr(GateDependencyRecoveryJournal, "event", event)
    publish(s)
    result = s.runner.run_once()
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    if boundary == "AUTHORIZED":
        assert not s.coordinator.journal.reservations()
    else:
        assert s.coordinator.journal.reservations()
        assert "relaunch prohibited" in s.runner.run_once().reason


def install_successful_execution(s, monkeypatch):
    def execute(self, request, **kwargs):
        path = Path(request.repository) / "aidp_orchestration/product_owner_http.py"
        path.write_text("INITIAL = True\nRECOVERED = True\n")
        return CodexExecutionResult(request.execution_id, request.task_id, request.expected_head, request.expected_head,
                                    ("aidp_orchestration/product_owner_http.py",),
                                    (ValidationResult("python -m pytest tests/orchestration", True, "pass"),),
                                    ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT)
    monkeypatch.setattr("aidp_orchestration.executor.CodexExecutionService.execute", execute)

    class Architect:
        def __init__(self, workspace):
            self.workspace = workspace
            self.identity_guard = self
        def validate(self, *, expected_head=None, **kwargs):
            assert _git(self.workspace, "rev-parse", "HEAD") == expected_head
            common = Path(_git(self.workspace, "rev-parse", "--git-common-dir"))
            return dict(repository=str(self.workspace.resolve()), git_common_dir=str(common.resolve()),
                        branch=_git(self.workspace, "branch", "--show-current"), remote_url=_git(self.workspace, "remote", "get-url", "origin"))
        def review(self, request, **kwargs):
            assert request.authority_contract_id == s.authority.authority_id
            provenance = ArchitectReviewProvenance("process", "launcher", "model", utc_now(), utc_now(), "architect-review-result-v1")
            return create_review_result(review_request_id=request.review_request_id, task_id=request.task_id,
                                        execution_id=request.execution_id, review_iteration=0, disposition=ArchitectReviewDisposition.PASS,
                                        reviewed_head=request.reviewed_head, expected_head=request.expected_current_head,
                                        reviewed_tree_hash=request.reviewed_tree_hash, findings=(), allowed_rework_scope=(),
                                        required_validations=(), provenance=provenance, failure_reason=None, authority_claims=(), created_at=utc_now())
        def revalidate(self, request): self.validate(expected_head=request.expected_current_head)
    monkeypatch.setattr(ProductOwnerGateDependencyRunner, "_workspace_architect", lambda self, workspace, branch: Architect(workspace))


def test_success_preserves_history_and_parent_and_records_new_lineage(scenario, monkeypatch):
    s = scenario
    install_successful_execution(s, monkeypatch)
    before = (s.claim.read_bytes(), s.terminal.read_bytes(), s.runner._parent_snapshot(s.source.parent_task_id), s.runner.repository.head)
    publish(s)
    result = s.runner.run_once()
    assert result.state is ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING, result.reason
    assert result.authority_id == s.authority.authority_id
    assert result.execution_id != s.authority.predecessor_execution_id
    assert (s.claim.read_bytes(), s.terminal.read_bytes(), s.runner._parent_snapshot(s.source.parent_task_id), s.runner.repository.head) == before
    events = [json.loads(p.read_text()) for p in sorted((s.coordinator.journal.root / "events" / s.authority.authority_id).glob("*.json"))]
    assert [e["kind"] for e in events] == ["AUTHORIZED", "RESERVED", "LAUNCH_INTENT", "STARTED", "RESULT_RECORDED", "REVIEWED", "TERMINAL"]
    assert s.coordinator.journal.status(s.authority.authority_id)["kind"] == "TERMINAL"
    assert not s.store.product_owner_gate_dependency_claimed(s.source.authority_id)
    assert not (s.store.root / "decision-journal").exists()
    assert "relaunch prohibited" in s.runner.run_once().reason
    assert not (s.store.root / "product-owner-gate-dependency-status" / f"{s.authority.authority_id}.json").exists()


def test_evidence_rechecked_before_reservation(scenario):
    s = scenario
    calls = []
    def verify(*args, **kwargs):
        calls.append(1)
        return s.evidence if len(calls) == 1 else replace(s.evidence, no_active_process=False)
    s.verifier.verify = verify
    result = s.coordinator.run_once(s.authority, s.inbox.pending())
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert not s.coordinator.journal.reservations()


def test_changed_clean_inventory_still_requires_new_authorization(scenario):
    s = scenario
    calls = []
    def verify(*args, **kwargs):
        calls.append(1)
        return s.evidence if len(calls) == 1 else replace(s.evidence, inventory_digest="f" * 64)
    s.verifier.verify = verify
    result = s.coordinator.run_once(s.authority, s.inbox.pending())
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert "evidence changed" in result.reason
    assert not s.coordinator.journal.reservations()


@pytest.mark.parametrize("field,value", [("retry_budget", 0), ("retry_budget", 2), ("retry_budget", True),
                                         ("claim_state", "RECEIVED"), ("terminal_state", "SUCCESS"),
                                         ("predecessor_execution_id", "../escape")])
def test_recovery_budget_and_terminal_schema_constraints(scenario, field, value):
    with pytest.raises(ValueError):
        reidentify(scenario.authority, **{field: value})


def test_untrusted_or_stale_assessment_is_rejected(scenario):
    s = scenario
    for value in (asdict(s.evidence), replace(s.evidence, verified_at=utc_now()-timedelta(minutes=2))):
        s.verifier.verify = lambda *args, **kwargs: value
        with pytest.raises(PermissionError):
            s.coordinator.validate(s.authority, s.inbox.pending())


def test_execution_terms_cannot_expand_under_approved_recovery(scenario):
    s = scenario
    changed = _bound_authority(s.root, allowed_scope=("aidp_orchestration/product_owner_deployment.py",))
    s.inbox.persist(ContractInboxItem(changed.authority_id, changed, utc_now()))
    authority = reidentify(s.authority, execution_source_authority_id=changed.authority_id,
                           execution_source_digest=changed.expected_id(), execution_terms_digest=execution_terms_digest(changed))
    with pytest.raises(ValueError, match="execution terms"):
        s.coordinator.validate(authority, s.inbox.pending())


def test_ancestry_is_required_even_when_other_bindings_match(scenario, monkeypatch):
    import subprocess

    s = scenario
    real_run = subprocess.run
    def run(command, **kwargs):
        if tuple(command[:3]) == ("git", "merge-base", "--is-ancestor"):
            raise subprocess.CalledProcessError(1, command)
        return real_run(command, **kwargs)
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        s.coordinator.validate(s.authority, s.inbox.pending())


@pytest.mark.parametrize("boundary", ["RESERVED", "LAUNCH_INTENT", "STARTED"])
def test_process_crash_keeps_reservation_without_relaunch(scenario, monkeypatch, boundary):
    s = scenario
    install_successful_execution(s, monkeypatch)
    original = GateDependencyRecoveryJournal.event
    def event(self, authority, kind, **kwargs):
        original(self, authority, kind, **kwargs)
        if kind == boundary:
            raise SystemExit("simulated process crash")
    monkeypatch.setattr(GateDependencyRecoveryJournal, "event", event)
    publish(s)
    before = (s.claim.read_bytes(), s.terminal.read_bytes())
    with pytest.raises(SystemExit): s.runner.run_once()
    assert "relaunch prohibited" in s.runner.run_once().reason
    assert (s.claim.read_bytes(), s.terminal.read_bytes()) == before


def test_concurrent_recovery_dispatch_launches_at_most_once(scenario, monkeypatch):
    s = scenario
    install_successful_execution(s, monkeypatch)
    publish(s)
    second = RecoveringProductOwnerGateDependencyRunner(s.runner.repository, runtime_root=s.inbox.root.parent,
                                                        architect=object(), recovery_evidence_verifier=s.verifier)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda runner: runner.run_once(), (s.runner, second)))
    assert sum(r.state is ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING for r in results) == 1
    assert len(s.coordinator.journal.reservations()) == 1


def test_independent_review_failure_does_not_accept_parent(scenario, monkeypatch):
    s = scenario
    install_successful_execution(s, monkeypatch)
    def unavailable(*args): raise RuntimeError("independent Architect unavailable")
    monkeypatch.setattr(ProductOwnerGateDependencyRunner, "_workspace_architect", unavailable)
    publish(s)
    before = s.runner._parent_snapshot(s.source.parent_task_id)
    result = s.runner.run_once()
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert s.coordinator.journal.status(s.authority.authority_id)["kind"] == "BLOCKED"
    assert s.runner._parent_snapshot(s.source.parent_task_id) == before


def test_ingress_reconsiders_unchanged_recovery_object_under_new_policy(scenario, tmp_path, monkeypatch):
    from aidp_orchestration.architect_ingress import ArchitectGitIngress
    from aidp_orchestration.architect_ingress_acceptance import INGRESS_E2E_BRANCH
    from aidp_orchestration.contracts import IngressStatus
    from test_architect_ingress import _setup

    repository, _remote, architect, runtime, _contract = _setup(tmp_path / "transport")
    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().status is IngressStatus.MATERIALIZED
    a = scenario.authority
    relative = f".ai/orchestration/architect-contracts/{a.authority_id}.json"
    content = serialize_contract_inbox_item(ContractInboxItem(a.authority_id, a, utc_now())).encode()
    (architect / relative).write_bytes(content)
    _git(architect, "add", "--", relative)
    _git(architect, "commit", "-m", "isolated recovery fixture")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)
    commit = _git(architect, "rev-parse", "HEAD")
    blob = _git(architect, "rev-parse", f"{commit}:{relative}")
    history = runtime / "architect-ingress.jsonl"
    old_policy = "utf8-sig-v3-dependency-replacement-lineage"
    event = {"architect_ingress_event": dict(contract_id="rejected-path-sha256:fixture", remote_commit=commit,
                                             blob_id=blob, status="BLOCKED", identity_kind="rejection",
                                             remote_path=relative, parser_policy=old_policy,
                                             reason="remote contract rejected: ValueError")}
    with history.open("a", encoding="utf-8") as stream: stream.write(json.dumps(event) + "\n")
    before = history.read_bytes()
    with monkeypatch.context() as context:
        context.setattr("aidp_orchestration.architect_ingress.PARSER_POLICY", old_policy)
        assert ingress.run_once().status is IngressStatus.NO_ACTION
        assert history.read_bytes() == before
    result = ingress.run_once()
    assert result.status is IngressStatus.MATERIALIZED and result.blob_id == blob
    assert result.contract_id == a.authority_id and history.read_bytes().startswith(before)
    assert (architect / relative).read_bytes() == content
    assert not (runtime / "gate-dependency-recovery").exists()
