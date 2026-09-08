from __future__ import annotations

import base64
import io
import json
import os
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import aidp_orchestration.product_owner_deployment as deployment
from aidp_orchestration.product_owner_deployment import ProductOwnerDeploymentConfig, WindowsDPAPISecretProvider
from aidp_orchestration.product_owner_service import ProductOwnerServiceApplication, _ChallengeRegistry
from aidp_orchestration.product_owner_confirmation import ApprovalChallenge
from aidp_orchestration.contracts import AIDPState, ProductOwnerApprovalContext, utc_now


def _config(tmp_path: Path, monkeypatch=None, **overrides) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    cert = tmp_path / "tls.crt"
    key = tmp_path / "tls.key"
    secret = tmp_path / "oidc-secret.json"
    issuer_secret = tmp_path / "issuer-secret.json"
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    for path in (cert, key, secret, issuer_secret):
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
        "trusted_issuer_token_file": str(issuer_secret),
        "security_audit_file": str(audit_dir / "security.jsonl"),
    }
    values.update(overrides)
    path = tmp_path / "deployment.json"
    path.write_text(json.dumps(values), encoding="utf-8")
    if monkeypatch is not None:
        monkeypatch.setattr(deployment, "_registered_worktrees", lambda root: (Path(values["repository_root"]).resolve(),))
        monkeypatch.setattr(deployment, "_validate_windows_acl", lambda path, label: None)
        monkeypatch.setattr(deployment.subprocess, "check_output", _git_check_output)
    return path


def _git_check_output(args, cwd=None, text=None, stderr=None):
    if tuple(args[:3]) == ("git", "worktree", "list"):
        return f"worktree {Path(cwd).resolve()}\n"
    if tuple(args[:3]) == ("git", "rev-parse", "--git-common-dir"):
        return str(Path(cwd).resolve() / ".git")
    raise AssertionError(args)


def test_deployment_config_is_strict_loopback_and_protected(tmp_path: Path, monkeypatch) -> None:
    config = ProductOwnerDeploymentConfig.load(_config(tmp_path, monkeypatch))
    config.validate_files()
    assert config.bind_host == "127.0.0.1"

    with pytest.raises(ValueError):
        ProductOwnerDeploymentConfig.load(_config(tmp_path / "bad-host", monkeypatch, bind_host="0.0.0.0"))
    with pytest.raises(ValueError):
        ProductOwnerDeploymentConfig.load(_config(tmp_path / "bad-origin", monkeypatch, public_origin="http://127.0.0.1:8443"))
    with pytest.raises(ValueError):
        ProductOwnerDeploymentConfig.load(_config(tmp_path / "unknown", monkeypatch, unexpected=True))


def test_protected_material_inside_worktree_is_rejected(tmp_path: Path, monkeypatch) -> None:
    path = _config(tmp_path, monkeypatch)
    config = ProductOwnerDeploymentConfig.load(path)
    monkeypatch.setattr(deployment, "_registered_worktrees", lambda root: (tmp_path.resolve(),))
    with pytest.raises(ValueError, match="outside governed Git worktrees"):
        config.validate_files()


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


def _call(app, method: str, path: str, query: str = "", *, token: str | None = None,
          peer: str = "127.0.0.1") -> tuple[str, dict[str, str], bytes]:
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": "0",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(b""),
        "REMOTE_ADDR": peer,
    }
    if token is not None:
        environ["HTTP_AUTHORIZATION"] = "Bearer " + token
    body = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], body


def _application(challenge: ApprovalChallenge | None = None):
    class Issuer:
        def issue(self):
            if challenge is None:
                raise AssertionError("issuer should not be called")
            return challenge

    class Confirmation:
        def __call__(self, environ, start_response):
            raise AssertionError("confirmation adapter should not be called")

    return ProductOwnerServiceApplication(
        issuer=Issuer(), confirmation=Confirmation(), registry=_ChallengeRegistry(),
        public_origin="https://127.0.0.1:8443", issuance_token="t" * 64,
        audit=lambda event, correlation: None,
    )


def test_issue_endpoint_requires_trusted_loopback_bearer() -> None:
    app = _application()
    assert _call(app, "POST", "/product-owner/issue")[0].startswith("403")
    assert _call(app, "POST", "/product-owner/issue", token="t" * 64, peer="10.0.0.5")[0].startswith("403")
    assert _call(app, "POST", "/product-owner/issue", token="x" * 64)[0].startswith("403")


def test_issue_endpoint_projects_locator_without_nonce_or_secret() -> None:
    context = _context()
    challenge = ApprovalChallenge(context, "n" * 64)
    app = _application(challenge)
    status, _headers, body = _call(app, "POST", "/product-owner/issue", token="t" * 64)
    assert status.startswith("201")
    payload = json.loads(body)
    assert payload["status"] == "WAITING_FOR_PRODUCT_OWNER"
    assert payload["task_id"] == "AIDP-INFRA-0002"
    assert payload["confirmation_url"].startswith("https://127.0.0.1:8443/product-owner/confirm?context=")
    encoded = json.dumps(payload)
    assert "nonce" not in encoded.lower()
    assert "secret" not in encoded.lower()
    assert "tttt" not in encoded


def test_status_endpoint_is_locator_only() -> None:
    context = _context()
    registry = _ChallengeRegistry()
    registry.add(ApprovalChallenge(context, "n" * 64))
    app = ProductOwnerServiceApplication(
        issuer=SimpleNamespace(issue=lambda: None), confirmation=SimpleNamespace(),
        registry=registry, public_origin="https://127.0.0.1:8443",
        issuance_token="t" * 64, audit=lambda event, correlation: None,
    )
    status, _headers, body = _call(app, "GET", "/product-owner/status", "context=" + context.approval_context_id)
    assert status.startswith("200")
    payload = json.loads(body)
    assert set(payload) == {
        "status", "task_id", "approval_context_id", "confirmation_url", "expires_at", "architect_review_id"
    }


def test_keycloak_template_binds_password_and_totp_flow() -> None:
    template = json.loads((Path(__file__).parents[2] / "deploy/product-owner-confirmation/keycloak-realm.template.json").read_text(encoding="utf-8"))
    assert template["browserFlow"] == "aidp-product-owner-browser"
    flow = next(value for value in template["authenticationFlows"] if value["alias"] == template["browserFlow"])
    executions = {(value["authenticator"], value["requirement"]) for value in flow["authenticationExecutions"]}
    assert ("auth-username-password-form", "REQUIRED") in executions
    assert ("auth-otp-form", "REQUIRED") in executions
    assert template["acrToLoAMapping"]["urn:keycloak:acr:totp"] == 1


def test_launcher_uses_argument_vector_not_python_source_interpolation() -> None:
    script = (Path(__file__).parents[2] / "deploy/product-owner-confirmation/Start-ProductOwnerConfirmation.ps1").read_text(encoding="utf-8")
    assert "python -c" not in script
    assert "-m aidp_orchestration.product_owner_service --config $resolved" in script


@pytest.mark.skipif(os.name != "nt", reason="DPAPI principal binding is Windows-only")
def test_dpapi_provider_rejects_wrong_principal_scope(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "secret.json"
    monkeypatch.setattr(deployment, "_current_windows_sid", lambda: "S-1-5-21-current")
    monkeypatch.setattr(deployment, "_crypt_unprotect", lambda value, *, entropy: b"secret")
    payload = {
        "schema_version": "aidp-dpapi-secret-v2",
        "client_id": "aidp-product-owner",
        "protection_scope": "current-user",
        "principal_sid": "S-1-5-21-other",
        "ciphertext": base64.b64encode(b"ciphertext").decode("ascii"),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    provider = WindowsDPAPISecretProvider(path, expected_client_id="aidp-product-owner")
    with pytest.raises(RuntimeError):
        provider.client_secret("aidp-product-owner")
    payload["principal_sid"] = "S-1-5-21-current"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert provider.client_secret("aidp-product-owner") == "secret"
