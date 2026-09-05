from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from aidp_orchestration.product_owner_oidc import (
    KeycloakOIDCClient,
    ProductOwnerOIDCConfig,
    new_oidc_transaction,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class SecretProvider:
    def client_secret(self, client_id: str) -> str:
        assert client_id == "aidp"
        return "protected-secret"


class DiscoveryTransport:
    def get_json(self, url: str) -> dict[str, object]:
        assert url == "https://id.example/realms/aidp/.well-known/openid-configuration"
        return {
            "issuer": "https://id.example/realms/aidp",
            "authorization_endpoint": "https://id.example/realms/aidp/protocol/openid-connect/auth",
        }

    def post_form(self, url: str, form: dict[str, str], *, client_secret: str) -> dict[str, object]:
        raise AssertionError("authorization URL construction must not exchange tokens")


def config(**changes: object) -> ProductOwnerOIDCConfig:
    values: dict[str, object] = {
        "issuer": "https://id.example/realms/aidp",
        "client_id": "aidp",
        "audience": "aidp",
        "redirect_uri": "https://aidp.example/product-owner/confirm/callback",
        "post_logout_redirect_uri": "https://aidp.example/signed-out",
        "repository_identity": "repository",
        "policy_version": "policy-v1",
    }
    values.update(changes)
    return ProductOwnerOIDCConfig(**values)  # type: ignore[arg-type]


def test_authorization_url_is_code_flow_with_pkce_and_transaction_binding() -> None:
    transaction = new_oidc_transaction(now=NOW)
    client = KeycloakOIDCClient(
        config(), secrets_provider=SecretProvider(), transport=DiscoveryTransport(),
        audit=lambda event, correlation: None,
    )

    url = urlsplit(client.authorization_url(transaction))
    query = parse_qs(url.query)

    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == [transaction.state]
    assert query["nonce"] == [transaction.nonce]
    assert transaction.code_verifier not in url.geturl()
    assert "client_secret" not in query


@pytest.mark.parametrize(
    "change",
    [
        {"issuer": "http://id.example/realms/aidp"},
        {"redirect_uri": "https://user@aidp.example/callback"},
        {"post_logout_redirect_uri": "https://aidp.example/out?next=evil"},
        {"post_logout_redirect_uri": "https://evil.example/signed-out"},
        {"post_logout_redirect_uri": "https://aidp.example/not-allowlisted"},
        {"algorithms": ("HS256",)},
        {"clock_skew_seconds": 61},
    ],
)
def test_configuration_rejects_insecure_or_ambiguous_bindings(change: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        config(**change)


def test_oidc_client_requires_a_deployable_audit_sink() -> None:
    with pytest.raises(ValueError):
        KeycloakOIDCClient(
            config(), secrets_provider=SecretProvider(), transport=DiscoveryTransport(), audit=None,  # type: ignore[arg-type]
        )
