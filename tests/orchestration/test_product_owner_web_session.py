from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import cast

import pytest

from aidp_orchestration.contracts import ProductOwnerApprovalContext
from aidp_orchestration.product_owner_oidc import OIDCSessionProof
from aidp_orchestration.product_owner_web_session import ProductOwnerWebSessionStore


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def context() -> ProductOwnerApprovalContext:
    return cast(ProductOwnerApprovalContext, SimpleNamespace(expires_at=NOW + timedelta(minutes=10)))


def test_session_is_opaque_rotated_and_csrf_is_single_use() -> None:
    store = ProductOwnerWebSessionStore(clock=lambda: NOW)
    session = store.create(context(), "n" * 32)
    first = store.issue_csrf(session.session_id)
    second = store.issue_csrf(session.session_id)

    with pytest.raises(PermissionError):
        store.consume_csrf(session.session_id, first)
    store.consume_csrf(session.session_id, second)
    with pytest.raises(PermissionError):
        store.consume_csrf(session.session_id, second)

    rotated = store.rotate_authenticated(
        session.session_id,
        OIDCSessionProof("", "subject", "server-token", NOW),
    )
    assert rotated.session_id != session.session_id
    assert rotated.proof is not None and rotated.proof.session_id == rotated.session_id
    with pytest.raises(PermissionError):
        store.get(session.session_id)


def test_session_policy_is_bounded_and_cookie_is_host_only() -> None:
    store = ProductOwnerWebSessionStore(clock=lambda: NOW)
    assert store.COOKIE_NAME.startswith("__Host-")
    assert store.cookie_attributes == "Path=/; Secure; HttpOnly; SameSite=Strict"
    assert "Domain=" not in store.cookie_attributes

    with pytest.raises(ValueError):
        ProductOwnerWebSessionStore(absolute_lifetime=timedelta(0))
    with pytest.raises(ValueError):
        ProductOwnerWebSessionStore(maximum_sessions=4097)
