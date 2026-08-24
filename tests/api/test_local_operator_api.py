import asyncio
import json

import pytest
from fastapi import HTTPException

from api_app import (
    app,
    get_local_operator_authenticator,
    require_hunt_hypothesis_create_authority,
)
from application.local_operator import (
    AuthenticatedPrincipal,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    LocalOperatorAuthenticator,
)


TOKEN = "a-secure-local-operator-token-value-123456"


def _authenticator(*, permissions: str = HUNT_HYPOTHESIS_CREATE_PERMISSION):
    return LocalOperatorAuthenticator.from_values(
        mode_enabled="true",
        principal_id="configured-operator",
        display_name="Configured Operator",
        token=TOKEN,
        permissions=permissions,
        allowed_origins="http://localhost:5173",
    )


def test_operator_me_returns_safe_configured_principal_metadata() -> None:
    status, headers, payload = _request(f"Bearer {TOKEN}")

    assert status == 200
    assert payload == {
        "principal_id": "configured-operator",
        "display_name": "Configured Operator",
        "principal_type": "human/operator",
        "granted_permissions": [HUNT_HYPOTHESIS_CREATE_PERMISSION],
    }
    assert TOKEN not in json.dumps(payload)
    assert "authorization" not in json.dumps(payload).lower()


@pytest.mark.parametrize("authorization", [None, "Bearer invalid", "Basic invalid"])
def test_operator_me_rejects_missing_invalid_and_malformed_credentials(authorization) -> None:
    status, headers, payload = _request(authorization)

    assert status == 401
    assert headers["www-authenticate"] == "Bearer"
    assert payload == {"detail": "Local Operator authentication failed."}


def test_caller_identity_or_permission_headers_cannot_override_server_policy() -> None:
    status, _, payload = _request(
        f"Bearer {TOKEN}",
        extra_headers=[
            (b"x-principal-id", b"attacker"),
            (b"x-permissions", b"admin"),
        ],
    )

    assert status == 200
    assert payload["principal_id"] == "configured-operator"
    assert payload["granted_permissions"] == [HUNT_HYPOTHESIS_CREATE_PERMISSION]


def test_unconfigured_operator_endpoint_is_service_unavailable() -> None:
    app.dependency_overrides.pop(get_local_operator_authenticator, None)
    status, _, payload = asyncio.run(_asgi_get("/api/operator/me", []))

    assert status == 503
    assert payload == {"detail": "Local Operator mode is not configured."}


def test_authenticated_operator_without_create_permission_is_forbidden() -> None:
    principal = _authenticator(permissions="").authenticate(f"Bearer {TOKEN}")

    with pytest.raises(HTTPException) as error:
        require_hunt_hypothesis_create_authority(principal)
    assert error.value.status_code == 403


def test_application_cors_never_uses_wildcard_or_cookie_credentials() -> None:
    middleware = next(item for item in app.user_middleware if item.cls.__name__ == "CORSMiddleware")
    assert "*" not in middleware.kwargs["allow_origins"]
    assert middleware.kwargs["allow_credentials"] is False
    assert middleware.kwargs["allow_headers"] == ["Authorization", "Content-Type"]


def _request(authorization: str | None, extra_headers=None):
    app.dependency_overrides[get_local_operator_authenticator] = _authenticator
    headers = list(extra_headers or [])
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("ascii")))
    try:
        return asyncio.run(_asgi_get("/api/operator/me", headers))
    finally:
        app.dependency_overrides.pop(get_local_operator_authenticator, None)


async def _asgi_get(path: str, headers: list[tuple[bytes, bytes]]):
    messages: list[dict] = []
    sent = False

    async def receive() -> dict:
        nonlocal sent
        if sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )
    start = next(item for item in messages if item["type"] == "http.response.start")
    body = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
    response_headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    return start["status"], response_headers, json.loads(body.decode("utf-8"))
