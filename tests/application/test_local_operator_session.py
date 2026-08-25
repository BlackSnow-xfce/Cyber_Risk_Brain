from datetime import datetime, timedelta, timezone

import pytest

from application.local_operator import (
    AuthenticatedPrincipal,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    LocalOperatorConfigurationIntegrityError,
    LocalOperatorConfigurationUnavailableError,
)
from application.local_operator_session import (
    LocalOperatorSessionAuthenticationError,
    LocalOperatorSessionConfiguration,
    LocalOperatorSessionCsrfError,
    LocalOperatorSessionStore,
)


NOW = datetime(2026, 8, 24, 15, 0, tzinfo=timezone.utc)


def _configuration(**overrides) -> LocalOperatorSessionConfiguration:
    values = {
        "enabled": "true",
        "lifetime_seconds": "1800",
        "cookie_secure": "false",
        "cookie_name": "predatorai_local_operator_session",
        "allowed_origins": ("http://127.0.0.1:5173",),
    }
    values.update(overrides)
    return LocalOperatorSessionConfiguration.from_values(**values)


def _principal(principal_id: str = "product-owner") -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        principal_id=principal_id,
        display_name="Product Owner",
        principal_type="human/operator",
        permissions=frozenset({HUNT_HYPOTHESIS_CREATE_PERMISSION}),
    )


def test_configuration_is_explicit_and_insecure_cookie_is_loopback_only() -> None:
    configuration = _configuration()
    assert configuration.lifetime_seconds == 1800
    assert configuration.cookie_secure is False

    with pytest.raises(LocalOperatorConfigurationUnavailableError):
        _configuration(enabled=None)
    with pytest.raises(LocalOperatorConfigurationIntegrityError):
        _configuration(allowed_origins=("https://example.com:443",))
    with pytest.raises(LocalOperatorConfigurationIntegrityError):
        _configuration(lifetime_seconds="0")


def test_session_rotation_prevents_fixation_and_invalidates_predecessor() -> None:
    tokens = iter(["a" * 43, "b" * 43])
    store = LocalOperatorSessionStore(
        _configuration(), clock=lambda: NOW, token_factory=lambda: next(tokens)
    )
    first = store.create(_principal())
    second = store.create(_principal())

    assert first.session_id != second.session_id
    with pytest.raises(LocalOperatorSessionAuthenticationError):
        store.resolve(first.session_id, _principal())
    assert store.resolve(second.session_id, _principal()).principal_id == "product-owner"


def test_principal_is_bound_server_side_and_not_supplied_by_session() -> None:
    store = LocalOperatorSessionStore(
        _configuration(), clock=lambda: NOW, token_factory=lambda: "s" * 43
    )
    created = store.create(_principal())

    with pytest.raises(LocalOperatorSessionAuthenticationError):
        store.resolve(created.session_id, _principal("spoofed"))


def test_expiry_logout_and_store_reset_invalidate_session() -> None:
    current = NOW
    store = LocalOperatorSessionStore(
        _configuration(), clock=lambda: current, token_factory=lambda: "s" * 43
    )
    created = store.create(_principal())
    current = NOW + timedelta(seconds=1800)
    with pytest.raises(LocalOperatorSessionAuthenticationError):
        store.resolve(created.session_id, _principal())

    current = NOW
    created = store.create(_principal())
    store.revoke(created.session_id)
    with pytest.raises(LocalOperatorSessionAuthenticationError):
        store.resolve(created.session_id, _principal())

    restarted = LocalOperatorSessionStore(_configuration(), clock=lambda: current)
    with pytest.raises(LocalOperatorSessionAuthenticationError):
        restarted.resolve(created.session_id, _principal())


def test_csrf_is_independent_session_bound_and_constant_policy() -> None:
    tokens = iter(["s" * 43, "c" * 43])
    store = LocalOperatorSessionStore(
        _configuration(), clock=lambda: NOW, token_factory=lambda: next(tokens)
    )
    created = store.create(_principal())
    session, csrf = store.issue_csrf(created.session_id, _principal())

    assert csrf != created.session_id
    assert session.csrf_digest
    store.require_mutation(
        created.session_id,
        _principal(),
        origin="http://127.0.0.1:5173",
        csrf_token=csrf,
    )
    for origin, token in (
        (None, csrf),
        ("http://malicious.example:5173", csrf),
        ("http://127.0.0.1:5173", None),
        ("http://127.0.0.1:5173", "wrong"),
    ):
        with pytest.raises(LocalOperatorSessionCsrfError):
            store.require_mutation(
                created.session_id,
                _principal(),
                origin=origin,
                csrf_token=token,
            )
