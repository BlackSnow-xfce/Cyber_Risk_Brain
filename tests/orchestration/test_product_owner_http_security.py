from pathlib import Path

from aidp_orchestration.product_owner_http import _SECURITY_HEADERS


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


def test_audit_boundary_hashes_correlation_and_swallows_sink_errors() -> None:
    events: list[tuple[str, str]] = []
    application = object.__new__(__import__(
        "aidp_orchestration.product_owner_http", fromlist=["ProductOwnerHTTPApplication"]
    ).ProductOwnerHTTPApplication)
    application.audit = lambda event, correlation: events.append((event, correlation))
    application._audit("logout", "secret-session-value")
    assert events[0][0] == "logout"
    assert len(events[0][1]) == 32
    assert "secret-session-value" not in events[0][1]

    application.audit = lambda event, correlation: (_ for _ in ()).throw(RuntimeError("down"))
    application._audit("dependency_failure", "secret")
