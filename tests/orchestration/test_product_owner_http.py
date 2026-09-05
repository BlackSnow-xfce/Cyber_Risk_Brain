from io import BytesIO

import pytest

from aidp_orchestration.product_owner_http import ProductOwnerHTTPApplication, _RateLimiter


def bare_application() -> ProductOwnerHTTPApplication:
    application = object.__new__(ProductOwnerHTTPApplication)
    application.maximum_body_bytes = 128
    return application


def test_form_parser_accepts_only_exact_bounded_urlencoded_input() -> None:
    application = bare_application()
    body = b"csrf=token&operation=ACCEPT&reason="
    environ: dict[str, object] = {
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    assert application._form(environ) == {
        "csrf": ["token"], "operation": ["ACCEPT"], "reason": [""]
    }


@pytest.mark.parametrize(
    "environ",
    [
        {"CONTENT_TYPE": "text/plain", "CONTENT_LENGTH": "0", "wsgi.input": BytesIO()},
        {"CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": "129", "wsgi.input": BytesIO()},
        {"CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": "3", "wsgi.input": BytesIO(b"x=1")},
    ],
)
def test_form_parser_fails_closed(environ: dict[str, object]) -> None:
    with pytest.raises(PermissionError):
        bare_application()._form(environ)


def test_parameter_parser_rejects_duplicates_and_unexpected_fields() -> None:
    with pytest.raises(PermissionError):
        ProductOwnerHTTPApplication._one({"csrf": ["a", "b"]}, "csrf", maximum=32)
    with pytest.raises(PermissionError):
        ProductOwnerHTTPApplication._parameters("context=ok&role=owner", {"context"})


def test_rate_limiter_uses_trusted_peer_and_fails_closed() -> None:
    limiter = _RateLimiter(limit=2)
    limiter.check("login", "192.0.2.1", "transaction-a")
    limiter.check("login", "192.0.2.1", "transaction-a")
    with pytest.raises(PermissionError):
        limiter.check("login", "192.0.2.1", "transaction-a")
    limiter.check("callback", "192.0.2.1", "transaction-a")
    with pytest.raises(PermissionError):
        limiter.check("login", "", "transaction-a")


def test_rate_limiter_cannot_be_bypassed_by_rotating_peer_addresses() -> None:
    limiter = _RateLimiter(limit=2)
    limiter.check("callback", "192.0.2.1", "transaction-a")
    limiter.check("callback", "192.0.2.2", "transaction-a")
    with pytest.raises(PermissionError):
        limiter.check("callback", "192.0.2.3", "transaction-a")
    limiter.check("callback", "192.0.2.3", "transaction-b")


def test_peer_identity_ignores_forwarded_headers() -> None:
    assert ProductOwnerHTTPApplication._peer({
        "REMOTE_ADDR": "192.0.2.10", "HTTP_X_FORWARDED_FOR": "203.0.113.7",
    }) == "192.0.2.10"


def test_rate_limiter_has_bounded_identity_storage() -> None:
    limiter = _RateLimiter(maximum_keys=2)
    limiter.check("login", "192.0.2.1", "transaction-a")
    with pytest.raises(PermissionError):
        limiter.check("login", "192.0.2.2", "transaction-b")
