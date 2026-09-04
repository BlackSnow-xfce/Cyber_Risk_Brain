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
