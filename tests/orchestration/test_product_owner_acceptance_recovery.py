from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from aidp_orchestration.architect_review import create_review_result
from aidp_orchestration.contracts import (
    AIDPState, ArchitectReviewDisposition, ArchitectReviewProvenance,
    AuthenticatedProductOwner, OrchestrationDecision, ProductOwnerAcceptanceStatus,
    ProductOwnerApprovalContext, ProductOwnerAuthorizationEvidence,
    ProductOwnerDecision, ProductOwnerDecisionState, ProductOwnerOperation,
    canonical_digest,
)
from aidp_orchestration.product_owner_acceptance import ProductOwnerDecisionConsumer
from aidp_orchestration.product_owner_confirmation import create_recorded_decision_event
from aidp_orchestration.runtime import LocalRuntimeStore


NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


class Repository:
    root = Path(".").resolve()
    branch = "topic"
    original = "a" * 40
    projected = "b" * 40

    def __init__(self): self.head = self.original
    def inspect(self):
        state = AIDPState.WAITING_FOR_PRODUCT_OWNER if self.head == self.original else AIDPState.DONE
        return OrchestrationDecision("TASK-0131", state, None, self.branch, self.head, (), NOW)
    def _git(self, *args):
        if args == ("rev-parse", f"{self.projected}^"):
            return self.original
        raise ValueError(args)


class Authorizer:
    def authorize(self, principal, context, operation, *, at):
        return ProductOwnerAuthorizationEvidence(
            "authorization", principal.principal_id, operation, context.task_id,
            context.repository_identity, context.policy_version, at, at + timedelta(minutes=5),
        )


class Projection:
    def __init__(self, repository, crash=True): self.repository, self.crash = repository, crash
    def project_product_owner_decision(self, decision):
        self.repository.head = self.repository.projected
        if self.crash:
            self.crash = False
            raise RuntimeError("simulated crash after commit")
        return self.repository.projected
    def verify_product_owner_projection(self, decision, commit):
        assert commit == self.repository.projected
    def push(self, branch): return self.repository.projected


def setup(store, repository):
    result = create_review_result(
        review_request_id="1" * 64, task_id="TASK-0131", execution_id="execution",
        review_iteration=0, disposition=ArchitectReviewDisposition.PASS,
        reviewed_head="2" * 40, expected_head="3" * 40, reviewed_tree_hash="4" * 40,
        findings=(), allowed_rework_scope=(), required_validations=(),
        provenance=ArchitectReviewProvenance("process", "launcher", "model", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    store.persist_architect_result(result)
    lifecycle_version = canonical_digest({
        "task_id": "TASK-0131", "state": AIDPState.WAITING_FOR_PRODUCT_OWNER,
        "commit": repository.original, "execution_id": result.execution_id,
        "review_result_id": result.review_result_id,
    })
    values = dict(
        schema_version="product-owner-approval-context-v1", task_id="TASK-0131",
        repository_identity="repository", repository_remote_identity="origin",
        expected_state=AIDPState.WAITING_FOR_PRODUCT_OWNER,
        expected_lifecycle_version=lifecycle_version, policy_version="policy-v1",
        implementation_execution_id=result.execution_id, architect_review_id=result.review_result_id,
        architect_result_digest=canonical_digest({"architect_review_result": result}),
        product_commit=repository.original, issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10), nonce_digest="5" * 64,
    )
    context_id = canonical_digest(values)
    context = ProductOwnerApprovalContext(
        approval_context_id=context_id, context_digest=context_id, **values,
    )
    principal = AuthenticatedProductOwner(
        "po-1", "issuer", "subject", "event", NOW, "oidc", "high", "session",
    )
    authorization = Authorizer().authorize(principal, context, ProductOwnerOperation.ACCEPT, at=NOW)
    decision_values = dict(
        schema_version="product-owner-decision-v1", approval_context_id=context_id,
        approval_context_digest=context_id, principal=principal, authorization=authorization,
        operation=ProductOwnerOperation.ACCEPT, reason=None, decided_at=NOW,
        client_identity="client", command_id="command", command_payload_digest="6" * 64,
        nonce_digest=context.nonce_digest,
    )
    decision_id = canonical_digest(decision_values)
    decision = ProductOwnerDecision(decision_id=decision_id, integrity_digest=decision_id, **decision_values)
    store.persist_product_owner_approval_context(context)
    store.persist_product_owner_decision(decision)
    store.append_product_owner_decision_event(create_recorded_decision_event(decision, NOW))
    return decision


def test_restart_recovers_commit_after_persisted_intent(tmp_path, monkeypatch):
    repository = Repository()
    store = LocalRuntimeStore(tmp_path)
    decision = setup(store, repository)
    monkeypatch.setattr(
        "aidp_orchestration.product_owner_acceptance._repository_identities",
        lambda root: ("repository", "origin"),
    )
    projection = Projection(repository)
    first = ProductOwnerDecisionConsumer(
        repository, store, projection, authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert first.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert store.product_owner_transaction(decision.decision_id)[-1]["state"] == "INTENT"

    second = ProductOwnerDecisionConsumer(
        repository, store, projection, authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW + timedelta(hours=1),
    ).consume()
    assert second.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED
    assert store.product_owner_transaction(decision.decision_id)[-1]["state"] == "PUBLISHED"


def test_tampered_recovery_transaction_blocks_without_terminal_decision(tmp_path, monkeypatch):
    repository = Repository()
    store = LocalRuntimeStore(tmp_path)
    decision = setup(store, repository)
    monkeypatch.setattr(
        "aidp_orchestration.product_owner_acceptance._repository_identities",
        lambda root: ("repository", "origin"),
    )
    projection = Projection(repository)
    assert ProductOwnerDecisionConsumer(
        repository, store, projection, authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume().status is ProductOwnerAcceptanceStatus.BLOCKED
    path = tmp_path / "product-owner-transactions" / f"{decision.decision_id}.jsonl"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["product_owner_transaction"]["binding_digest"] = "f" * 64
    path.write_text(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    result = ProductOwnerDecisionConsumer(
        repository, store, projection, authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert result.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert store.product_owner_decision_events(decision.decision_id)[-1].current_state is ProductOwnerDecisionState.RECORDED


def test_persisted_operation_substitution_is_rejected(tmp_path, monkeypatch):
    repository = Repository()
    store = LocalRuntimeStore(tmp_path)
    decision = setup(store, repository)
    monkeypatch.setattr(
        "aidp_orchestration.product_owner_acceptance._repository_identities",
        lambda root: ("repository", "origin"),
    )
    projection = Projection(repository)
    assert ProductOwnerDecisionConsumer(
        repository, store, projection, authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume().status is ProductOwnerAcceptanceStatus.BLOCKED
    path = tmp_path / "product-owner-transactions" / f"{decision.decision_id}.jsonl"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    event = envelope["product_owner_transaction"]
    event["operation"] = ProductOwnerOperation.REQUEST_REWORK.value
    unsigned = dict(event)
    unsigned.pop("event_digest")
    event["event_digest"] = canonical_digest(unsigned)
    path.write_text(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    result = ProductOwnerDecisionConsumer(
        repository, store, projection, authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert result.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert repository.head == repository.projected


def test_failure_before_intent_cannot_transition_lifecycle(tmp_path, monkeypatch):
    repository = Repository()
    store = LocalRuntimeStore(tmp_path)
    decision = setup(store, repository)
    monkeypatch.setattr(
        "aidp_orchestration.product_owner_acceptance._repository_identities",
        lambda root: ("repository", "origin"),
    )
    monkeypatch.setattr(store, "append_product_owner_transaction", lambda *args: (_ for _ in ()).throw(OSError("disk")))
    result = ProductOwnerDecisionConsumer(
        repository, store, Projection(repository, crash=False), authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert result.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert repository.head == repository.original
    assert store.product_owner_decision_events(decision.decision_id)[-1].current_state is ProductOwnerDecisionState.RECORDED


def test_restart_after_committed_journal_finishes_publication_and_consumption(tmp_path, monkeypatch):
    repository = Repository()
    store = LocalRuntimeStore(tmp_path)
    decision = setup(store, repository)
    monkeypatch.setattr(
        "aidp_orchestration.product_owner_acceptance._repository_identities",
        lambda root: ("repository", "origin"),
    )

    class FailPush(Projection):
        def push(self, branch): raise RuntimeError("upstream unavailable")

    first = ProductOwnerDecisionConsumer(
        repository, store, FailPush(repository, crash=False), authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert first.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert store.product_owner_transaction(decision.decision_id)[-1]["state"] == "COMMITTED"
    second = ProductOwnerDecisionConsumer(
        repository, store, Projection(repository, crash=False), authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW + timedelta(hours=1),
    ).consume()
    assert second.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED
    assert store.product_owner_transaction(decision.decision_id)[-1]["state"] == "PUBLISHED"


def test_restart_after_published_journal_finishes_consumption_once(tmp_path, monkeypatch):
    repository = Repository()
    store = LocalRuntimeStore(tmp_path)
    decision = setup(store, repository)
    monkeypatch.setattr(
        "aidp_orchestration.product_owner_acceptance._repository_identities",
        lambda root: ("repository", "origin"),
    )
    original_append = store.append_product_owner_decision_event
    failed = {"value": False}

    def fail_consumed(event):
        if event.current_state is ProductOwnerDecisionState.CONSUMED and not failed["value"]:
            failed["value"] = True
            raise OSError("journal unavailable")
        return original_append(event)

    monkeypatch.setattr(store, "append_product_owner_decision_event", fail_consumed)
    first = ProductOwnerDecisionConsumer(
        repository, store, Projection(repository, crash=False), authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert first.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert store.product_owner_transaction(decision.decision_id)[-1]["state"] == "PUBLISHED"
    second = ProductOwnerDecisionConsumer(
        repository, store, Projection(repository, crash=False), authorizer=Authorizer(),
        policy_version="policy-v1", clock=lambda: NOW + timedelta(hours=1),
    ).consume()
    assert second.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED
    assert len(store.product_owner_decision_events(decision.decision_id)) == 2
