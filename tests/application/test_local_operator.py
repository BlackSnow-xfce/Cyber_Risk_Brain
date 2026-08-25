from datetime import datetime, timezone

import pytest

from application.local_operator import (
    AI_MODEL_SELECTION_UPDATE_PERMISSION,
    AIModelSelectionWriteAuthority,
    AuthenticatedPrincipal,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    HuntHypothesisWriteAuthority,
    LocalOperatorAuthenticationError,
    LocalOperatorAuthenticator,
    LocalOperatorAuthorizationError,
    LocalOperatorConfigurationIntegrityError,
    LocalOperatorConfigurationUnavailableError,
    parse_local_operator_allowed_origins,
)


TOKEN = "a-secure-local-operator-token-value-123456"


def test_ai_model_selection_authority_requires_exact_server_permission() -> None:
    authorized = _authenticator(
        permissions=AI_MODEL_SELECTION_UPDATE_PERMISSION
    ).authenticate(f"Bearer {TOKEN}")
    unauthorized = _authenticator().authenticate(f"Bearer {TOKEN}")

    assert AIModelSelectionWriteAuthority().require(authorized).outcome == "allowed"
    with pytest.raises(LocalOperatorAuthorizationError):
        AIModelSelectionWriteAuthority().require(unauthorized)


def _authenticator(*, permissions: str = HUNT_HYPOTHESIS_CREATE_PERMISSION):
    return LocalOperatorAuthenticator.from_values(
        mode_enabled="true",
        principal_id="local-product-owner",
        display_name="Local Product Owner",
        token=TOKEN,
        permissions=permissions,
        allowed_origins="http://127.0.0.1:5173,http://localhost:5173",
    )


def test_valid_credential_resolves_only_configured_principal() -> None:
    principal = _authenticator().authenticate(f"Bearer {TOKEN}")

    assert principal == AuthenticatedPrincipal(
        principal_id="local-product-owner",
        display_name="Local Product Owner",
        principal_type="human/operator",
        permissions=frozenset({HUNT_HYPOTHESIS_CREATE_PERMISSION}),
    )
    assert TOKEN not in repr(_authenticator())


@pytest.mark.parametrize("authorization", [None, "", "Basic abc", "Bearer", "Bearer wrong", "bearer token", "Bearer töken"])
def test_missing_malformed_or_invalid_credential_is_unauthenticated(authorization) -> None:
    with pytest.raises(LocalOperatorAuthenticationError):
        _authenticator().authenticate(authorization)


def test_no_anonymous_fallback_when_mode_is_disabled_or_missing() -> None:
    for mode in (None, "false"):
        with pytest.raises(LocalOperatorConfigurationUnavailableError):
            LocalOperatorAuthenticator.from_values(
                mode_enabled=mode,
                principal_id=None,
                display_name=None,
                token=None,
                permissions=None,
                allowed_origins=None,
            )


@pytest.mark.parametrize(
    "overrides",
    [
        {"principal_id": ""},
        {"display_name": ""},
        {"token": "too-short"},
        {"permissions": "hunt_hypothesis:create,hunt_hypothesis:create"},
        {"permissions": "hunt_hypothesis:create-any"},
        {"allowed_origins": "*"},
    ],
)
def test_structurally_invalid_configuration_fails_closed(overrides) -> None:
    values = {
        "mode_enabled": "true",
        "principal_id": "operator-1",
        "display_name": "Operator One",
        "token": TOKEN,
        "permissions": HUNT_HYPOTHESIS_CREATE_PERMISSION,
        "allowed_origins": "http://localhost:5173",
    }
    values.update(overrides)
    with pytest.raises(LocalOperatorConfigurationIntegrityError):
        LocalOperatorAuthenticator.from_values(**values)


def test_authentication_and_creation_authorization_are_distinct() -> None:
    authorized = _authenticator().authenticate(f"Bearer {TOKEN}")
    unauthorized = _authenticator(permissions="").authenticate(f"Bearer {TOKEN}")
    now = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)
    authority = HuntHypothesisWriteAuthority(clock=lambda: now)

    assert authority.require(authorized).outcome == "allowed"
    denied = authority.evaluate(unauthorized)
    assert denied.principal_id == "local-product-owner"
    assert denied.operation == HUNT_HYPOTHESIS_CREATE_PERMISSION
    assert denied.timestamp == now
    assert denied.outcome == "denied"
    with pytest.raises(LocalOperatorAuthorizationError):
        authority.require(unauthorized)


def test_only_explicit_local_origins_are_accepted() -> None:
    assert parse_local_operator_allowed_origins(
        "http://127.0.0.1:5173,http://localhost:5173"
    ) == ("http://127.0.0.1:5173", "http://localhost:5173")

    for value in (
        "https://example.com:5173",
        "http://localhost",
        "http://localhost:5173/path",
        "http://localhost:5173,http://localhost:5173",
    ):
        with pytest.raises(LocalOperatorConfigurationIntegrityError):
            parse_local_operator_allowed_origins(value)
