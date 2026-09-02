from datetime import datetime, timedelta, timezone

from aidp_orchestration.contracts import (
    AIDPState, AuthenticatedProductOwner, ProductOwnerAcceptanceStatus,
    ProductOwnerApprovalContext, ProductOwnerAuthorizationEvidence,
    ProductOwnerOperation, canonical_digest,
)
from aidp_orchestration.product_owner_confirmation import (
    ProductOwnerConfirmationCommand, ProductOwnerConfirmationService,
)
from aidp_orchestration.runtime import LocalRuntimeStore


NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)
NONCE = "n" * 40


def context():
    import hashlib
    values = dict(
        schema_version="product-owner-approval-context-v1", task_id="TASK-0131",
        repository_identity="repository", repository_remote_identity="origin",
        expected_state=AIDPState.WAITING_FOR_PRODUCT_OWNER,
        expected_lifecycle_version="lifecycle", policy_version="policy-v1",
        implementation_execution_id="execution", architect_review_id="review",
        architect_result_digest="a" * 64, product_commit="b" * 40,
        issued_at=NOW, expires_at=NOW + timedelta(minutes=10),
        nonce_digest=hashlib.sha256(NONCE.encode()).hexdigest(),
    )
    identity = canonical_digest(values)
    return ProductOwnerApprovalContext(
        approval_context_id=identity, context_digest=identity, **values,
    )


class Authenticator:
    def authenticate(self, proof, approval):
        if proof != "valid-proof":
            raise PermissionError
        return AuthenticatedProductOwner(
            "po-1", "issuer", "subject", "auth-event", NOW,
            "webauthn", "phishing-resistant", "session",
        )


class Authorizer:
    def authorize(self, principal, approval, operation, *, at):
        return ProductOwnerAuthorizationEvidence(
            "authorization", principal.principal_id, operation, approval.task_id,
            approval.repository_identity, approval.policy_version, at,
            at + timedelta(minutes=5),
        )


def command(context_id, **changes):
    values = dict(
        approval_context_id=context_id, nonce=NONCE,
        operation=ProductOwnerOperation.ACCEPT, reason=None,
        command_id="command-1", client_identity="chat-client",
        authentication_proof="valid-proof",
    )
    values.update(changes)
    return ProductOwnerConfirmationCommand(**values)


def test_missing_identity_boundary_is_fail_closed(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    approval = context()
    store.persist_product_owner_approval_context(approval)
    result = ProductOwnerConfirmationService(
        store, authenticator=None, authorizer=None, clock=lambda: NOW,
    ).confirm(command(approval.approval_context_id))
    assert result.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert store.recorded_product_owner_decisions() == ()


def test_confirmation_records_immutable_decision_and_idempotent_replay(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    approval = context()
    store.persist_product_owner_approval_context(approval)
    service = ProductOwnerConfirmationService(
        store, authenticator=Authenticator(), authorizer=Authorizer(),
        context_validator=lambda context, at: None, clock=lambda: NOW,
    )
    first = service.confirm(command(approval.approval_context_id))
    second = service.confirm(command(approval.approval_context_id))
    assert first.status is ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION
    assert second.decision_id == first.decision_id
    assert len(store.recorded_product_owner_decisions()) == 1


def test_nonce_forgery_and_changed_idempotent_payload_are_rejected(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    approval = context()
    store.persist_product_owner_approval_context(approval)
    service = ProductOwnerConfirmationService(
        store, authenticator=Authenticator(), authorizer=Authorizer(),
        context_validator=lambda context, at: None, clock=lambda: NOW,
    )
    forged = service.confirm(command(approval.approval_context_id, nonce="x" * 40))
    assert forged.status is ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST
    assert service.confirm(command(approval.approval_context_id)).decision_id is not None
    altered = service.confirm(command(
        approval.approval_context_id, reason="changed",
    ))
    assert altered.status is ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST


def test_expired_and_unauthorized_confirmation_fail_closed(tmp_path):
    store = LocalRuntimeStore(tmp_path)
    approval = context()
    store.persist_product_owner_approval_context(approval)
    expired = ProductOwnerConfirmationService(
        store, authenticator=Authenticator(), authorizer=Authorizer(),
        context_validator=lambda context, at: None,
        clock=lambda: NOW + timedelta(hours=1),
    ).confirm(command(approval.approval_context_id))
    denied = ProductOwnerConfirmationService(
        store, authenticator=Authenticator(), authorizer=Authorizer(),
        context_validator=lambda context, at: None, clock=lambda: NOW,
    ).confirm(command(approval.approval_context_id, authentication_proof="forged"))
    assert expired.status is ProductOwnerAcceptanceStatus.REJECTED_STALE
    assert denied.status is ProductOwnerAcceptanceStatus.REJECTED_UNAUTHORIZED
