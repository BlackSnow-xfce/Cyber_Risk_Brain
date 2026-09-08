from __future__ import annotations

import io
import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidp_orchestration.product_owner_deployment import ProductOwnerDeploymentConfig
from aidp_orchestration.product_owner_service import ProductOwnerServiceApplication, _ChallengeRegistry
from aidp_orchestration.product_owner_confirmation import ApprovalChallenge
from aidp_orchestration.contracts import AIDPState, ProductOwnerApprovalContext, utc_now


def _config(tmp_path: Path, **overrides) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    cert = tmp_path / "tls.crt"
    key = tmp_path / "tls.key"
    secret = tmp_path / "oidc-secret.json"
    for path in (cert, key, secret):
        path.write_text("fixture", encoding="utf-8")
    values = {
        "repository_root": str(repo),
        "bind_host": "127.0.0.1",
        "bind_port": 8443,
        "public_origin": "https://127.0.0.1:8443",
        "issuer": "https://id.example.invalid/realms/predatorai",
        "client_id": "aidp-product-owner",
        "audience": "aidp-product-owner",
        "policy_version": "product-owner-confirmation-v1",
        "tls_certificate": str(cert),
        "tls_private_key": str(key),
        "protected_secret_file": str(secret),
        "security_audit_file": str(tmp_path / "audit" / "security.jsonl"),
    }
    values.update(overrides)
    path = tmp_path / "deployment.json"
    path.write_text(json.dumps(values), encoding="utf-8")
    return path


def test_deployment_config_is_strict_and_loopback_only(tmp_path: Path) -> None:
    config = ProductOwnerDeploymentConfig.load(_config(tmp_path))
    config.validate_files()
    assert config.bind_host == "127.0.0.1"

    with pytest.raises(ValueError):
        ProductOwnerDeploymentConfig.load(_config(tmp_path / "bad-host", bind_host="0.0.0.0"))
    with pytest.raises(ValueError):
        ProductOwnerDeploymentConfig.load(_config(tmp_path / "bad-origin", public_origin="http://127.0.0.1:8443"))
    with pytest.raises(ValueError):
        ProductOwnerDeploymentConfig.load(_config(tmp_path / "unknown", unexpected=True))


def _context() -> ProductOwnerApprovalContext:
    now = utc_now()
    values = dict(
        schema_version="product-owner-approval-context-v1",
        task_id="AIDP-INFRA-0002",
        repository_identity="1" * 64,
        repository_remote_identity="2" * 64,
        expected_state=AIDPState.WAITING_FOR_PRODUCT_OWNER,
        expected_lifecycle_version="3" * 64,
        policy_version="product-owner-confirmation-v1",
        implementation_execution_id="execution-1",
        architect_review_id="review-1",
        architect_result_digest="4" * 64,
        product_commit="5" * 40,
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
        nonce_digest="6" * 64,
    )
    from aidp_orchestration.contracts import canonical_digest
    identifier = canonical_digest(values)
    return ProductOwnerApprovalContext(approval_context_id=identifier, context_digest=identifier, **values)


def _call(app, method: str, path: str, query: str = "") -> tuple[str, dict[str, str], bytes]:
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)
    body = b"".join(app({
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": "0",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(b""),
    }, start_response))
    return captured["status"], captured["headers"], body


def test_issue_endpoint_projects_locator_without_nonce_or_secret() -> None:
    context = _context()
    challenge = ApprovalChallenge(context, "n" * 64)

    class Issuer:
        def issue(self):
            return challenge

    class Confirmation:
        def __call__(self, environ, start_response):
            raise AssertionError("confirmation adapter should not be called")

    app = ProductOwnerServiceApplication(
        issuer=Issuer(), confirmation=Confirmation(), registry=_ChallengeRegistry(),
        public_origin="https://127.0.0.1:8443",
    )
    status, _headers, body = _call(app, "POST", "/product-owner/issue")
    assert status.startswith("201")
    payload = json.loads(body)
    assert payload["status"] == "WAITING_FOR_PRODUCT_OWNER"
    assert payload["task_id"] == "AIDP-INFRA-0002"
    assert payload["confirmation_url"].startswith("https://127.0.0.1:8443/product-owner/confirm?context=")
    encoded = json.dumps(payload)
    assert "nonce" not in encoded.lower()
    assert "secret" not in encoded.lower()


def test_status_endpoint_is_locator_only() -> None:
    context = _context()
    registry = _ChallengeRegistry()
    registry.add(ApprovalChallenge(context, "n" * 64))
    app = ProductOwnerServiceApplication(
        issuer=SimpleNamespace(issue=lambda: None), confirmation=SimpleNamespace(),
        registry=registry, public_origin="https://127.0.0.1:8443",
    )
    status, _headers, body = _call(app, "GET", "/product-owner/status", "context=" + context.approval_context_id)
    assert status.startswith("200")
    payload = json.loads(body)
    assert set(payload) == {
        "status", "task_id", "approval_context_id", "confirmation_url", "expires_at", "architect_review_id"
    }
