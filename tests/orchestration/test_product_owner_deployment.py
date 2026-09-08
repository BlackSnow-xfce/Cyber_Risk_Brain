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
from aidp_orchestration.contracts import AIDPState, ProductOwnerApprovalContext, canonical_digest, utc_now


def _config(tmp_path: Path, monkeypatch=None, **overrides) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True); repo=tmp_path/"repo"; repo.mkdir(); audit_dir=tmp_path/"audit"; audit_dir.mkdir()
    cert,key,secret,issuer_secret=(tmp_path/"tls.crt",tmp_path/"tls.key",tmp_path/"oidc-secret.json",tmp_path/"issuer-secret.json")
    for path in (cert,key,secret,issuer_secret): path.write_text("fixture",encoding="utf-8")
    values={"repository_root":str(repo),"bind_host":"127.0.0.1","bind_port":8443,"public_origin":"https://127.0.0.1:8443","issuer":"https://id.example.invalid/realms/predatorai","client_id":"aidp-product-owner","audience":"aidp-product-owner","policy_version":"product-owner-confirmation-v1","tls_certificate":str(cert),"tls_private_key":str(key),"protected_secret_file":str(secret),"trusted_issuer_token_file":str(issuer_secret),"security_audit_file":str(audit_dir/"security.jsonl")}
    values.update(overrides); path=tmp_path/"deployment.json"; path.write_text(json.dumps(values),encoding="utf-8")
    if monkeypatch is not None:
        monkeypatch.setattr(deployment,"_registered_worktrees",lambda root:(Path(values["repository_root"]).resolve(),)); monkeypatch.setattr(deployment,"_validate_windows_acl",lambda path,label:None); monkeypatch.setattr(deployment,"_inside_any_git_repository",lambda path:False); monkeypatch.setattr(deployment.subprocess,"check_output",_git_check_output)
    return path

def _git_check_output(args,cwd=None,text=None,stderr=None):
    if tuple(args[:3])==("git","worktree","list"): return f"worktree {Path(cwd).resolve()}\n"
    if tuple(args[:3])==("git","rev-parse","--git-common-dir"): return str(Path(cwd).resolve()/".git")
    raise AssertionError(args)

def test_deployment_config_is_strict_loopback_and_protected(tmp_path,monkeypatch):
    config=ProductOwnerDeploymentConfig.load(_config(tmp_path,monkeypatch)); config.validate_files(); assert config.bind_host=="127.0.0.1"
    with pytest.raises(ValueError): ProductOwnerDeploymentConfig.load(_config(tmp_path/"bad-host",monkeypatch,bind_host="0.0.0.0"))
    with pytest.raises(ValueError): ProductOwnerDeploymentConfig.load(_config(tmp_path/"bad-origin",monkeypatch,public_origin="http://127.0.0.1:8443"))
    with pytest.raises(ValueError): ProductOwnerDeploymentConfig.load(_config(tmp_path/"unknown",monkeypatch,unexpected=True))

def test_protected_material_inside_worktree_is_rejected(tmp_path,monkeypatch):
    path=_config(tmp_path,monkeypatch); config=ProductOwnerDeploymentConfig.load(path); monkeypatch.setattr(deployment,"_registered_worktrees",lambda root:(tmp_path.resolve(),))
    with pytest.raises(ValueError,match="outside governed Git worktrees"): config.validate_files()

def test_protected_material_inside_different_git_repository_is_rejected(tmp_path,monkeypatch):
    path=_config(tmp_path,monkeypatch); config=ProductOwnerDeploymentConfig.load(path); monkeypatch.setattr(deployment,"_inside_any_git_repository",lambda value: value==config.tls_private_key)
    with pytest.raises(ValueError,match="outside every Git repository"): config.validate_files()

def test_acl_policy_rejects_arbitrary_writable_sid(monkeypatch,tmp_path):
    monkeypatch.setattr(deployment.os,"name","nt"); payload=json.dumps({"current":"S-1-current","owner":"S-1-current","bad":["S-1-arbitrary"]})
    monkeypatch.setattr(deployment.subprocess,"check_output",lambda *a,**k:payload)
    with pytest.raises(ValueError,match="ACL is unsafe"): deployment._validate_windows_acl(tmp_path,"secret")

def _context():
    now=utc_now(); values=dict(schema_version="product-owner-approval-context-v1",task_id="AIDP-INFRA-0002",repository_identity="1"*64,repository_remote_identity="2"*64,expected_state=AIDPState.WAITING_FOR_PRODUCT_OWNER,expected_lifecycle_version="3"*64,policy_version="product-owner-confirmation-v1",implementation_execution_id="execution-1",architect_review_id="review-1",architect_result_digest="4"*64,product_commit="5"*40,issued_at=now,expires_at=now+timedelta(minutes=10),nonce_digest="6"*64); identifier=canonical_digest(values); return ProductOwnerApprovalContext(approval_context_id=identifier,context_digest=identifier,**values)
def _call(app,method,path,query="",*,token=None,peer="127.0.0.1"):
    captured={}; start=lambda status,headers:(captured.update(status=status,headers=dict(headers))); environ={"REQUEST_METHOD":method,"PATH_INFO":path,"QUERY_STRING":query,"CONTENT_LENGTH":"0","wsgi.url_scheme":"https","wsgi.input":io.BytesIO(b""),"REMOTE_ADDR":peer};
    if token is not None: environ["HTTP_AUTHORIZATION"]="Bearer "+token
    body=b"".join(app(environ,start)); return captured["status"],captured["headers"],body
def _application(challenge=None):
    class Issuer:
        def issue(self):
            if challenge is None: raise AssertionError("issuer should not be called")
            return challenge
    class Confirmation:
        def __call__(self,environ,start_response): raise AssertionError("confirmation adapter should not be called")
    return ProductOwnerServiceApplication(issuer=Issuer(),confirmation=Confirmation(),registry=_ChallengeRegistry(),public_origin="https://127.0.0.1:8443",issuance_token="t"*64,audit=lambda e,c:None)
def test_issue_endpoint_requires_trusted_loopback_bearer():
    app=_application(); assert _call(app,"POST","/product-owner/issue")[0].startswith("403"); assert _call(app,"POST","/product-owner/issue",token="t"*64,peer="10.0.0.5")[0].startswith("403"); assert _call(app,"POST","/product-owner/issue",token="x"*64)[0].startswith("403")
def test_issue_endpoint_projects_locator_without_nonce_or_secret():
    context=_context(); status,_,body=_call(_application(ApprovalChallenge(context,"n"*64)),"POST","/product-owner/issue",token="t"*64); assert status.startswith("201"); payload=json.loads(body); assert payload["task_id"]=="AIDP-INFRA-0002"; encoded=json.dumps(payload); assert "nonce" not in encoded.lower() and "secret" not in encoded.lower() and "tttt" not in encoded
def test_status_endpoint_is_locator_only():
    context=_context(); registry=_ChallengeRegistry(); registry.add(ApprovalChallenge(context,"n"*64)); app=ProductOwnerServiceApplication(issuer=SimpleNamespace(issue=lambda:None),confirmation=SimpleNamespace(),registry=registry,public_origin="https://127.0.0.1:8443",issuance_token="t"*64,audit=lambda e,c:None); status,_,body=_call(app,"GET","/product-owner/status","context="+context.approval_context_id); assert status.startswith("200"); assert set(json.loads(body))=={"status","task_id","approval_context_id","confirmation_url","expires_at","architect_review_id"}
def test_keycloak_template_binds_password_and_totp_flow():
    template=json.loads((Path(__file__).parents[2]/"deploy/product-owner-confirmation/keycloak-realm.template.json").read_text()); assert template["browserFlow"]=="aidp-product-owner-browser"; flow=next(v for v in template["authenticationFlows"] if v["alias"]==template["browserFlow"]); executions={(v["authenticator"],v["requirement"]) for v in flow["authenticationExecutions"]}; assert ("auth-username-password-form","REQUIRED") in executions and ("auth-otp-form","REQUIRED") in executions
def test_launcher_uses_argument_vector_not_python_source_interpolation():
    script=(Path(__file__).parents[2]/"deploy/product-owner-confirmation/Start-ProductOwnerConfirmation.ps1").read_text(); assert "python -c" not in script and "-m aidp_orchestration.product_owner_service --config $resolved" in script

@pytest.mark.skipif(os.name!="nt",reason="DPAPI is Windows-only")
def test_dpapi_trusted_provisioning_and_tamper_rejection(tmp_path,monkeypatch):
    path=tmp_path/"secret.json"; monkeypatch.setattr(deployment,"_current_windows_sid",lambda:"S-1-current"); monkeypatch.setattr(deployment,"_crypt_protect",lambda value,*,entropy:b"user-scope-cipher"); monkeypatch.setattr(deployment,"_crypt_unprotect",lambda value,*,entropy:b"secret"); monkeypatch.setattr(deployment,"_validate_windows_acl",lambda p,l:None); deployment.provision_current_user_dpapi_secret(path,client_id="aidp-product-owner",plaintext="secret"); payload=json.loads(path.read_text()); assert payload["schema_version"]=="aidp-dpapi-secret-v3" and payload["protection_scope"]=="current-user"; provider=WindowsDPAPISecretProvider(path,expected_client_id="aidp-product-owner"); assert provider.client_secret("aidp-product-owner")=="secret"; payload["protection_scope"]="local-machine"; path.write_text(json.dumps(payload));
    with pytest.raises(RuntimeError): provider.client_secret("aidp-product-owner")

@pytest.mark.skipif(os.name!="nt",reason="DPAPI principal isolation is Windows-only")
def test_real_dpapi_blob_cannot_be_unprotected_with_other_principal_entropy(tmp_path):
    # Real Windows DPAPI smoke test: a current-user blob is bound to SID-derived entropy; another principal binding fails.
    plaintext=b"predatorai-dpapi-principal-test"; current=_current_sid_for_test(); good=canonical_digest({"client_id":"aidp-product-owner","principal_sid":current}).encode("ascii"); bad=canonical_digest({"client_id":"aidp-product-owner","principal_sid":current+"-other"}).encode("ascii"); cipher=deployment._crypt_protect(plaintext,entropy=good); assert deployment._crypt_unprotect(cipher,entropy=good)==plaintext
    with pytest.raises(OSError): deployment._crypt_unprotect(cipher,entropy=bad)
def _current_sid_for_test(): return deployment._current_windows_sid()
