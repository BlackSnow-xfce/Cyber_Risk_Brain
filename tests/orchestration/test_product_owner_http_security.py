from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidp_orchestration.product_owner_http import ProductOwnerHTTPApplication, _SECURITY_HEADERS


def test_every_response_uses_restrictive_browser_security_headers() -> None:
    headers = dict(_SECURITY_HEADERS)
    assert headers["Cache-Control"] == "no-store"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Content-Security-Policy"] == (
        "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    )


def test_http_adapter_has_no_forbidden_authority_imports_or_calls() -> None:
    source = Path("aidp_orchestration/product_owner_http.py").read_text(encoding="utf-8")
    for forbidden in (
        "AIDPControlPlane", "AIDPLifecycleOnce", "ProductOwnerDecisionConsumer",
        "persist_product_owner_decision", "append_product_owner_decision_event", ".consume(",
    ):
        assert forbidden not in source
    assert "self.service.confirm(command)" in source


def test_audit_boundary_hashes_correlation_and_fails_closed_on_sink_error() -> None:
    events: list[tuple[str, str]] = []
    application = object.__new__(__import__(
        "aidp_orchestration.product_owner_http", fromlist=["ProductOwnerHTTPApplication"]
    ).ProductOwnerHTTPApplication)
    application.audit = lambda event, correlation: events.append((event, correlation))
    application._audit("logout", "secret-session-value")
    assert events[0][0] == "logout"
    assert len(events[0][1]) == 32
    assert "secret-session-value" not in events[0][1]

    application.audit = lambda event, correlation: (_ for _ in ()).throw(RuntimeError("sensitive detail"))
    with pytest.raises(RuntimeError, match="security audit unavailable"):
        application._audit("dependency_failure", "secret")


def test_top_level_rejection_remains_bounded_when_audit_sink_fails() -> None:
    application = object.__new__(ProductOwnerHTTPApplication)
    application.path = "/product-owner/confirm"
    application.sessions = SimpleNamespace(COOKIE_NAME="__Host-aidp_product_owner")
    application.rate_limiter = SimpleNamespace(check=lambda *_args: None)
    application.audit = lambda _event, _correlation: (_ for _ in ()).throw(
        RuntimeError("sensitive audit sink failure")
    )
    application._dispatch = lambda _environ: (_ for _ in ()).throw(
        PermissionError("sensitive request detail")
    )
    response: dict[str, object] = {}

    body = application(
        {
            "PATH_INFO": application.path,
            "REMOTE_ADDR": "192.0.2.1",
        },
        lambda status, headers: response.update(status=status, headers=headers),
    )

    assert response["status"] == "400 Bad Request"
    assert body == [b"Request rejected"]
    assert dict(response["headers"])["Content-Length"] == str(len(body[0]))
    assert b"sensitive" not in body[0]
    assert b"audit" not in body[0]


def test_missing_server_session_emits_sanitized_expiry_event() -> None:
    events: list[tuple[str, str]] = []
    application = object.__new__(__import__(
        "aidp_orchestration.product_owner_http", fromlist=["ProductOwnerHTTPApplication"]
    ).ProductOwnerHTTPApplication)
    application.sessions = SimpleNamespace(
        COOKIE_NAME="__Host-aidp_product_owner",
        get=lambda identifier: (_ for _ in ()).throw(PermissionError("expired secret")),
    )
    application.audit = lambda event, correlation: events.append((event, correlation))

    assert application._optional_session({"HTTP_COOKIE": "__Host-aidp_product_owner=secret-session"}) is None
    assert events == [("session_expiry", events[0][1])]
    assert len(events[0][1]) == 32
    assert "secret-session" not in events[0][1]


@pytest.mark.parametrize(
    "path",
    ("//attacker.example/confirm", "/confirm?next=//attacker.example", "/confirm#fragment", "/confirm\\callback"),
)
def test_adapter_rejects_unsafe_configured_confirmation_paths(path: str) -> None:
    oidc = SimpleNamespace(config=SimpleNamespace(redirect_uri=f"https://owner.example{path}/callback"))

    with pytest.raises(ValueError, match="unsafe HTTP adapter configuration"):
        ProductOwnerHTTPApplication(
            oidc=oidc,
            sessions=SimpleNamespace(),
            confirmation_service=SimpleNamespace(),
            challenge_resolver=lambda _: None,
            public_origin="https://owner.example",
            confirmation_path=path,
            audit=lambda _event, _correlation: None,
        )


@pytest.mark.parametrize(
    "origin",
    (
        "http://owner.example",
        "https://owner.example/confirm",
        "https://owner.example?next=/confirm",
        "https://owner.example#fragment",
        "https://user@owner.example",
        "https://owner.example:invalid",
        "https://owner.example\r\nInjected: value",
    ),
)
def test_adapter_rejects_values_that_are_not_exact_https_origins(origin: str) -> None:
    oidc = SimpleNamespace(config=SimpleNamespace(redirect_uri=f"{origin}/product-owner/confirm/callback"))

    with pytest.raises(ValueError, match="an exact HTTPS public origin is required"):
        ProductOwnerHTTPApplication(
            oidc=oidc,
            sessions=SimpleNamespace(),
            confirmation_service=SimpleNamespace(),
            challenge_resolver=lambda _: None,
            public_origin=origin,
            audit=lambda _event, _correlation: None,
        )


@pytest.mark.parametrize("maximum_body_bytes", (0, -1, 16_385))
def test_adapter_rejects_unsafe_body_size_configuration(maximum_body_bytes: int) -> None:
    oidc = SimpleNamespace(
        config=SimpleNamespace(redirect_uri="https://owner.example/product-owner/confirm/callback"),
        set_session_validator=lambda _validator: None,
    )

    with pytest.raises(ValueError, match="unsafe HTTP adapter configuration"):
        ProductOwnerHTTPApplication(
            oidc=oidc,
            sessions=SimpleNamespace(),
            confirmation_service=SimpleNamespace(),
            challenge_resolver=lambda _: None,
            public_origin="https://owner.example",
            maximum_body_bytes=maximum_body_bytes,
            audit=lambda _event, _correlation: None,
        )


@pytest.mark.parametrize("framing_header", ("HTTP_TRANSFER_ENCODING", "HTTP_CONTENT_LENGTH"))
def test_form_parser_rejects_ambiguous_request_framing(framing_header: str) -> None:
    application = object.__new__(ProductOwnerHTTPApplication)
    application.maximum_body_bytes = 128
    body = b"csrf=token&operation=ACCEPT&reason="
    environ = {
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
        framing_header: "chunked" if framing_header == "HTTP_TRANSFER_ENCODING" else str(len(body)),
    }

    with pytest.raises(PermissionError):
        application._form(environ)


def test_callback_redirect_url_encodes_the_server_resolved_context_locator() -> None:
    application = object.__new__(ProductOwnerHTTPApplication)
    application.path = "/product-owner/confirm"
    application.sessions = SimpleNamespace(
        rotate_authenticated=lambda _identifier, _proof: SimpleNamespace(
            session_id="rotated-session",
            approval_context=SimpleNamespace(approval_context_id="context&role=owner#fragment"),
        ),
    )
    application.oidc = SimpleNamespace(exchange_code=lambda **_kwargs: object())
    application.audit = lambda _event, _correlation: None
    application.rate_limiter = SimpleNamespace(check=lambda *_args: None)
    application._require_session = lambda _environ: SimpleNamespace(
        session_id="pre-auth-session",
        oidc_transaction=SimpleNamespace(state="expected-state"),
    )
    application._cookie = lambda identifier: f"cookie={identifier}"

    status, headers, body = application._callback(
        {
            "QUERY_STRING": "code=code&state=expected-state",
            "REMOTE_ADDR": "192.0.2.1",
        }
    )

    assert status.value == 303
    assert dict(headers)["Location"] == (
        "/product-owner/confirm?context=context%26role%3Downer%23fragment"
    )
    assert body == b""
