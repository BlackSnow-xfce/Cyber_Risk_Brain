from datetime import datetime, timedelta, timezone

import pytest

from aidp_orchestration.contracts import (
    AIDPState, AuthenticatedProductOwner, ProductOwnerApprovalContext,
    ProductOwnerAuthorizationEvidence, ProductOwnerDecision, ProductOwnerOperation,
    canonical_digest,
)


NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


def context(**changes):
    values = dict(
        schema_version="product-owner-approval-context-v1", task_id="TASK-0131",
        repository_identity="repository", repository_remote_identity="origin",
        expected_state=AIDPState.WAITING_FOR_PRODUCT_OWNER,
        expected_lifecycle_version="lifecycle-v1", policy_version="policy-v1",
        implementation_execution_id="execution", architect_review_id="review",
        architect_result_digest="a" * 64, product_commit="b" * 40,
        issued_at=NOW, expires_at=NOW + timedelta(minutes=10), nonce_digest="c" * 64,
    )
    values.update(changes)
    identity = canonical_digest(values)
    return ProductOwnerApprovalContext(approval_context_id=identity, context_digest=identity, **values)


def decision(operation=ProductOwnerOperation.ACCEPT, reason=None):
    approval = context()
    principal = AuthenticatedProductOwner(
        "po-1", "issuer", "subject", "auth-event", NOW, "webauthn", "phishing-resistant", "session",
    )
    authorization = ProductOwnerAuthorizationEvidence(
        "authorization", principal.principal_id, operation, approval.task_id,
        approval.repository_identity, approval.policy_version, NOW, NOW + timedelta(minutes=5),
    )
    values = dict(
        schema_version="product-owner-decision-v1", approval_context_id=approval.approval_context_id,
        approval_context_digest=approval.context_digest, principal=principal,
        authorization=authorization, operation=operation, reason=reason, decided_at=NOW,
        client_identity="chat-client", command_id="command-1",
        command_payload_digest="d" * 64, nonce_digest=approval.nonce_digest,
    )
    identity = canonical_digest(values)
    return ProductOwnerDecision(decision_id=identity, integrity_digest=identity, **values)


def test_approval_context_is_content_bound_and_requires_gate():
    assert context().approval_context_id == context().expected_digest()
    with pytest.raises(ValueError):
        context(expected_state=AIDPState.READY_FOR_ARCHITECT)


def test_request_rework_requires_bounded_reason():
    with pytest.raises(ValueError):
        decision(ProductOwnerOperation.REQUEST_REWORK)
    assert decision(ProductOwnerOperation.REQUEST_REWORK, "Risk explanation is misleading").reason
    with pytest.raises(ValueError):
        decision(ProductOwnerOperation.REQUEST_REWORK, "x" * 2049)


def test_decision_rejects_principal_authorization_substitution():
    value = decision()
    wrong = ProductOwnerAuthorizationEvidence(
        "authorization", "attacker", value.operation, value.authorization.task_id,
        value.authorization.repository_identity, value.authorization.policy_version, NOW,
    )
    fields = value.__dict__ if hasattr(value, "__dict__") else {
        name: getattr(value, name) for name in value.__dataclass_fields__
    }
    fields = dict(fields)
    fields["authorization"] = wrong
    with pytest.raises(ValueError):
        ProductOwnerDecision(**fields)
