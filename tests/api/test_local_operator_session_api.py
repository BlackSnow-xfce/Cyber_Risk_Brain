import asyncio
import json
from http.cookies import SimpleCookie
from urllib.parse import urlencode

import api_app
from api_app import (
    app,
    get_hunt_hypothesis_creation_service,
    get_local_operator_authenticator,
    get_local_operator_session_store,
)
from application.hunt_hypothesis_creation import HuntHypothesisCreationResult
from application.local_operator import (
    AuthorizationDecision,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    LocalOperatorAuthenticator,
)
from application.local_operator_session import (
    LocalOperatorSessionConfiguration,
    LocalOperatorSessionStore,
)
from core.threat_hunting import HuntHypothesis, HuntHypothesisStatus
from datetime import datetime, timezone


TOKEN = "a-secure-local-operator-token-value-123456"
ORIGIN = "http://127.0.0.1:5173"
NOW = datetime(2026, 8, 24, 15, 0, tzinfo=timezone.utc)


def _authenticator() -> LocalOperatorAuthenticator:
    return LocalOperatorAuthenticator.from_values(
        mode_enabled="true",
        principal_id="product-owner",
        display_name="Product Owner",
        token=TOKEN,
        permissions=HUNT_HYPOTHESIS_CREATE_PERMISSION,
        allowed_origins=ORIGIN,
    )


def _store() -> LocalOperatorSessionStore:
    return LocalOperatorSessionStore(
        LocalOperatorSessionConfiguration.from_values(
            enabled="true",
            lifetime_seconds="1800",
            cookie_secure="false",
            cookie_name="predatorai_local_operator_session",
            allowed_origins=(ORIGIN,),
        ),
        clock=lambda: NOW,
    )


def test_bootstrap_page_is_loopback_host_restricted_and_hardened() -> None:
    status, headers, body = _request("GET", "/api/operator/session/bootstrap")
    assert status == 200
    assert headers["cache-control"] == "no-store"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert headers["referrer-policy"] == "no-referrer"
    text = body.decode("utf-8")
    assert "<script" not in text
    assert TOKEN not in text
    assert "product-owner" not in text

    assert _request("GET", "/api/operator/session/bootstrap", client="10.0.0.2")[0] == 403
    assert _request("GET", "/api/operator/session/bootstrap", host="localhost:8000")[0] == 403


def test_valid_bootstrap_creates_exact_hardened_cookie_without_secret_response() -> None:
    store = _store()
    status, headers, body = _request(
        "POST",
        "/api/operator/session/bootstrap",
        body=urlencode({"credential": TOKEN}).encode("utf-8"),
        content_type="application/x-www-form-urlencoded",
        store=store,
    )
    assert status == 303
    assert body == b""
    assert TOKEN not in str(headers)
    cookie_header = headers["set-cookie"]
    assert "HttpOnly" in cookie_header
    assert "SameSite=strict" in cookie_header
    assert "Path=/" in cookie_header
    assert "Max-Age=1800" in cookie_header
    assert "Domain=" not in cookie_header
    assert "Secure" not in cookie_header
    assert "product-owner" not in cookie_header
    assert HUNT_HYPOTHESIS_CREATE_PERMISSION not in cookie_header


def test_bootstrap_cookie_immediately_resolves_through_authoritative_factory(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_SESSION_ENABLED", "true")
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_SESSION_LIFETIME_SECONDS", "1800")
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_SESSION_COOKIE_SECURE", "false")
    monkeypatch.setattr(
        api_app,
        "LOCAL_OPERATOR_SESSION_COOKIE_NAME",
        "predatorai_local_operator_session",
    )
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_ALLOWED_ORIGINS", ORIGIN)
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_MODE_ENABLED", "true")
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_PRINCIPAL_ID", "product-owner")
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_DISPLAY_NAME", "Product Owner")
    monkeypatch.setattr(api_app, "LOCAL_OPERATOR_TOKEN", TOKEN)
    monkeypatch.setattr(
        api_app,
        "LOCAL_OPERATOR_PERMISSIONS",
        HUNT_HYPOTHESIS_CREATE_PERMISSION,
    )
    previous_store = api_app._local_operator_session_store
    api_app._local_operator_session_store = None
    try:
        status, headers, _ = _request(
            "POST",
            "/api/operator/session/bootstrap",
            body=urlencode({"credential": TOKEN}).encode("utf-8"),
            content_type="application/x-www-form-urlencoded",
            use_store_override=False,
            use_authenticator_override=False,
        )
        assert status == 303
        cookie = SimpleCookie()
        cookie.load(headers["set-cookie"])
        morsel = cookie["predatorai_local_operator_session"]

        status, _, body = _request(
            "GET",
            "/api/operator/session",
            headers={
                "cookie": f"predatorai_local_operator_session={morsel.value}",
                "origin": ORIGIN,
            },
            use_store_override=False,
            use_authenticator_override=False,
        )

        assert status == 200
        assert json.loads(body)["principal_id"] == "product-owner"
    finally:
        api_app._local_operator_session_store = previous_store


def test_session_lookup_uses_the_single_server_matching_cookie_candidate() -> None:
    store = _store()
    cookie = _bootstrap_cookie(store)
    name, issued_value = cookie.split("=", 1)

    status, _, body = _request(
        "GET",
        "/api/operator/session",
        headers={
            "cookie": f"{name}={issued_value}; {name}=historical-invalid-value",
            "origin": ORIGIN,
        },
        store=store,
    )

    assert status == 200
    assert json.loads(body)["principal_id"] == "product-owner"


def test_session_lookup_rejects_only_unknown_or_tampered_cookie_candidates() -> None:
    store = _store()
    _bootstrap_cookie(store)

    status, _, _ = _request(
        "GET",
        "/api/operator/session",
        headers={
            "cookie": (
                f"{store.configuration.cookie_name}=unknown; "
                f"{store.configuration.cookie_name}=tampered"
            ),
            "origin": ORIGIN,
        },
        store=store,
    )

    assert status == 401


def test_invalid_bootstrap_creates_no_session_and_does_not_echo_credential() -> None:
    status, headers, body = _request(
        "POST",
        "/api/operator/session/bootstrap",
        body=urlencode({"credential": "invalid-secret-value"}).encode("utf-8"),
        content_type="application/x-www-form-urlencoded",
    )
    assert status == 401
    assert "set-cookie" not in headers
    assert b"invalid-secret-value" not in body
    assert TOKEN.encode() not in body


def test_rebootstrap_rotates_session_and_session_response_is_safe() -> None:
    store = _store()
    first = _bootstrap_cookie(store)
    second = _bootstrap_cookie(store)
    assert first != second
    assert _session_request(store, first)[0] == 401

    status, _, body = _session_request(store, second)
    assert status == 200
    payload = json.loads(body)
    assert payload["principal_id"] == "product-owner"
    assert payload["granted_permissions"] == [HUNT_HYPOTHESIS_CREATE_PERMISSION]
    assert payload["csrf_token"]
    assert TOKEN not in json.dumps(payload)
    assert second not in json.dumps(payload)


def test_session_creation_requires_exact_origin_and_csrf_before_mutation() -> None:
    store = _store()
    cookie = _bootstrap_cookie(store)
    _, _, session_body = _session_request(store, cookie)
    csrf = json.loads(session_body)["csrf_token"]
    service = RecordingCreationService()

    valid = _creation_request(store, cookie, csrf, ORIGIN, service)
    assert valid[0] == 201
    assert service.calls == 1
    assert service.principal_id == "product-owner"

    for origin, token in (
        (None, csrf),
        ("http://malicious.example:5173", csrf),
        (ORIGIN, None),
        (ORIGIN, "wrong"),
    ):
        before = service.calls
        status, _, _ = _creation_request(store, cookie, token, origin, service)
        assert status == 403
        assert service.calls == before


def test_logout_revokes_session_and_expires_cookie() -> None:
    store = _store()
    cookie = _bootstrap_cookie(store)
    _, _, session_body = _session_request(store, cookie)
    csrf = json.loads(session_body)["csrf_token"]
    status, headers, _ = _request(
        "POST",
        "/api/operator/session/logout",
        headers={"cookie": cookie, "origin": ORIGIN, "x-csrf-token": csrf},
        store=store,
    )
    assert status == 204
    assert "Max-Age=0" in headers["set-cookie"]
    assert _session_request(store, cookie)[0] == 401


class RecordingCreationService:
    def __init__(self) -> None:
        self.calls = 0
        self.principal_id = None

    def create(self, request, principal):
        self.calls += 1
        self.principal_id = principal.principal_id
        hypothesis = HuntHypothesis(
            hypothesis_id="hypothesis-12345678-1234-4234-9234-123456789abc",
            title=request.title,
            statement=request.statement,
            rationale=request.rationale,
            target_references=request.target_references,
            threat_references=request.threat_references,
            created_by=principal.principal_id,
            created_at=NOW,
            status=HuntHypothesisStatus.DRAFT,
        )
        return HuntHypothesisCreationResult(
            hypothesis=hypothesis,
            authorization=AuthorizationDecision(
                principal_id=principal.principal_id,
                operation=HUNT_HYPOTHESIS_CREATE_PERMISSION,
                timestamp=NOW,
                outcome="allowed",
            ),
        )


def _bootstrap_cookie(store) -> str:
    status, headers, _ = _request(
        "POST",
        "/api/operator/session/bootstrap",
        body=urlencode({"credential": TOKEN}).encode(),
        content_type="application/x-www-form-urlencoded",
        store=store,
    )
    assert status == 303
    cookie = SimpleCookie()
    cookie.load(headers["set-cookie"])
    morsel = cookie[store.configuration.cookie_name]
    return f"{store.configuration.cookie_name}={morsel.value}"


def _session_request(store, cookie):
    return _request(
        "GET",
        "/api/operator/session",
        headers={"cookie": cookie, "origin": ORIGIN},
        store=store,
    )


def _creation_request(store, cookie, csrf, origin, service):
    headers = {"cookie": cookie, "content-type": "application/json"}
    if origin is not None:
        headers["origin"] = origin
    if csrf is not None:
        headers["x-csrf-token"] = csrf
    return _request(
        "POST",
        "/api/hunt-hypotheses",
        body=json.dumps(
            {
                "title": "Investigate service activity",
                "statement": "An exposed service may warrant investigation.",
                "rationale": "Human-authored investigative assumption.",
                "target_references": [],
                "threat_references": [],
            }
        ).encode(),
        headers=headers,
        store=store,
        creation_service=service,
    )


def _request(
    method,
    path,
    *,
    body=b"",
    headers=None,
    content_type=None,
    client="127.0.0.1",
    host="127.0.0.1:8000",
    store=None,
    creation_service=None,
    use_store_override=True,
    use_authenticator_override=True,
):
    store = store or (_store() if use_store_override else None)
    if use_authenticator_override:
        app.dependency_overrides[get_local_operator_authenticator] = _authenticator
    if use_store_override:
        app.dependency_overrides[get_local_operator_session_store] = lambda: store
    if creation_service is not None:
        app.dependency_overrides[get_hunt_hypothesis_creation_service] = (
            lambda: creation_service
        )
    previous_store = api_app._local_operator_session_store
    if use_store_override:
        api_app._local_operator_session_store = store
    request_headers = {"host": host, **(headers or {})}
    if content_type:
        request_headers["content-type"] = content_type
    if body:
        request_headers["content-length"] = str(len(body))
    try:
        return asyncio.run(
            _asgi_request(method, path, body, request_headers, client)
        )
    finally:
        if use_store_override:
            api_app._local_operator_session_store = previous_store
        if use_authenticator_override:
            app.dependency_overrides.pop(get_local_operator_authenticator, None)
        app.dependency_overrides.pop(get_local_operator_session_store, None)
        app.dependency_overrides.pop(get_hunt_hypothesis_creation_service, None)


async def _asgi_request(method, path, body, headers, client):
    messages = []
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [(key.encode(), value.encode()) for key, value in headers.items()],
            "client": (client, 50000),
            "server": ("127.0.0.1", 8000),
        },
        receive,
        send,
    )
    start = next(item for item in messages if item["type"] == "http.response.start")
    response_headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return start["status"], response_headers, response_body
