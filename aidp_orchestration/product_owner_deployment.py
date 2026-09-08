from __future__ import annotations

import base64
import ctypes
import json
import os
import stat
import subprocess
from ctypes import wintypes
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from .contracts import canonical_digest
from .product_owner_oidc import ProductOwnerOIDCConfig, ProtectedSecretProvider, SecurityAuditSink


@dataclass(frozen=True, slots=True)
class ProductOwnerDeploymentConfig:
    deployment_config_file: Path
    repository_root: Path
    bind_host: str
    bind_port: int
    public_origin: str
    issuer: str
    client_id: str
    audience: str
    policy_version: str
    tls_certificate: Path
    tls_private_key: Path
    protected_secret_file: Path
    trusted_issuer_token_file: Path
    security_audit_file: Path
    oidc_ca_bundle: Path | None = None

    @classmethod
    def load(cls, path: Path) -> "ProductOwnerDeploymentConfig":
        resolved_config = path.resolve()
        raw = json.loads(resolved_config.read_text(encoding="utf-8"))
        if not isinstance(raw, dict): raise ValueError("deployment configuration must be an object")
        required = {"repository_root","bind_host","bind_port","public_origin","issuer","client_id","audience","policy_version","tls_certificate","tls_private_key","protected_secret_file","trusted_issuer_token_file","security_audit_file"}
        optional = {"oidc_ca_bundle"}
        if set(raw) != required | (set(raw) & optional) or not required.issubset(raw): raise ValueError("deployment configuration contains missing or unknown fields")
        base = resolved_config.parent
        def absolute(value: object, name: str) -> Path:
            if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must be a non-empty path")
            candidate = Path(value); candidate = candidate if candidate.is_absolute() else base / candidate
            return candidate.resolve()
        bind_host, bind_port, public_origin = raw["bind_host"], raw["bind_port"], raw["public_origin"]
        if not isinstance(bind_host, str) or bind_host not in {"127.0.0.1","::1","localhost"}: raise ValueError("confirmation service must bind to loopback")
        if type(bind_port) is not int or not 1 <= bind_port <= 65535: raise ValueError("invalid confirmation service port")
        if not isinstance(public_origin, str): raise ValueError("public_origin must be explicit")
        parsed = urlsplit(public_origin)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment: raise ValueError("public_origin must be an exact HTTPS origin")
        for field in ("issuer","client_id","audience","policy_version"):
            value = raw[field]
            if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value: raise ValueError(f"{field} must be explicit")
        ca = raw.get("oidc_ca_bundle")
        return cls(resolved_config, absolute(raw["repository_root"],"repository_root"), bind_host, bind_port, public_origin, raw["issuer"], raw["client_id"], raw["audience"], raw["policy_version"], absolute(raw["tls_certificate"],"tls_certificate"), absolute(raw["tls_private_key"],"tls_private_key"), absolute(raw["protected_secret_file"],"protected_secret_file"), absolute(raw["trusted_issuer_token_file"],"trusted_issuer_token_file"), absolute(raw["security_audit_file"],"security_audit_file"), None if ca is None else absolute(ca,"oidc_ca_bundle"))

    def validate_files(self) -> None:
        if not self.repository_root.is_dir(): raise ValueError("repository_root is unavailable")
        if not self.tls_certificate.is_file(): raise ValueError("TLS certificate is unavailable")
        for path,label,must_exist in ((self.deployment_config_file,"deployment configuration",True),(self.tls_private_key,"TLS private key",True),(self.protected_secret_file,"protected OIDC credential",True),(self.trusted_issuer_token_file,"trusted issuance credential",True),(self.security_audit_file,"security audit destination",False)):
            _validate_protected_path(path,label,self.repository_root,must_exist=must_exist)
        if self.oidc_ca_bundle is not None and not self.oidc_ca_bundle.is_file(): raise ValueError("OIDC CA bundle is unavailable")
        self.security_audit_file.parent.mkdir(parents=True, exist_ok=True)

    def oidc_config(self) -> ProductOwnerOIDCConfig:
        return ProductOwnerOIDCConfig(issuer=self.issuer,client_id=self.client_id,audience=self.audience,redirect_uri=self.public_origin+"/product-owner/confirm/callback",post_logout_redirect_uri=self.public_origin+"/signed-out",repository_identity=_repository_identity(self.repository_root),policy_version=self.policy_version,maximum_authentication_age=timedelta(minutes=5))


class WindowsDPAPISecretProvider(ProtectedSecretProvider):
    def __init__(self, path: Path, *, expected_client_id: str) -> None: self.path,self.expected_client_id=path,expected_client_id
    def client_secret(self, client_id: str) -> str:
        if os.name != "nt" or client_id != self.expected_client_id: raise RuntimeError("protected credential unavailable")
        payload=json.loads(self.path.read_text(encoding="utf-8")); required={"schema_version","client_id","protection_scope","principal_sid","ciphertext","provisioning_digest"}
        if not isinstance(payload,dict) or set(payload)!=required: raise RuntimeError("protected credential unavailable")
        current_sid=_current_windows_sid()
        evidence=canonical_digest({"schema_version":payload.get("schema_version"),"client_id":payload.get("client_id"),"protection_scope":payload.get("protection_scope"),"principal_sid":payload.get("principal_sid"),"ciphertext":payload.get("ciphertext")})
        if payload.get("schema_version")!="aidp-dpapi-secret-v3" or payload.get("client_id")!=client_id or payload.get("protection_scope")!="current-user" or payload.get("principal_sid")!=current_sid or payload.get("provisioning_digest")!=evidence: raise RuntimeError("protected credential unavailable")
        try:
            encrypted=base64.b64decode(payload["ciphertext"],validate=True); entropy=canonical_digest({"client_id":client_id,"principal_sid":current_sid}).encode("ascii"); plaintext=_crypt_unprotect(encrypted,entropy=entropy).decode("utf-8","strict")
        except Exception as exc: raise RuntimeError("protected credential unavailable") from exc
        if not plaintext or len(plaintext)>4096 or "\x00" in plaintext: raise RuntimeError("protected credential unavailable")
        return plaintext


def provision_current_user_dpapi_secret(path: Path, *, client_id: str, plaintext: str) -> None:
    if os.name != "nt" or not plaintext or len(plaintext)>4096: raise RuntimeError("secret provisioning unavailable")
    sid=_current_windows_sid(); entropy=canonical_digest({"client_id":client_id,"principal_sid":sid}).encode("ascii")
    ciphertext=_crypt_protect(plaintext.encode("utf-8"),entropy=entropy)
    values={"schema_version":"aidp-dpapi-secret-v3","client_id":client_id,"protection_scope":"current-user","principal_sid":sid,"ciphertext":base64.b64encode(ciphertext).decode("ascii")}
    values["provisioning_digest"]=canonical_digest(values)
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(values,sort_keys=True,separators=(",",":")),encoding="utf-8")
    _validate_windows_acl(path,"provisioned DPAPI credential")


class JsonLineSecurityAuditSink(SecurityAuditSink):
    _ALLOWED={"authentication_failure","request_failure","login_initiation","authentication_success","confirmation_result","logout","dependency_failure","authorization_success","authorization_failure","revocation","issuance_failure","issuance_success"}
    def __init__(self,path:Path)->None: self.path=path; self.path.parent.mkdir(parents=True,exist_ok=True)
    def __call__(self,event:str,correlation:str)->None:
        if event not in self._ALLOWED or not isinstance(correlation,str) or not correlation: raise RuntimeError("invalid security audit event")
        import hashlib; from datetime import datetime,timezone
        record={"schema_version":"aidp-product-owner-security-audit-v1","event":event,"correlation_digest":hashlib.sha256(correlation.encode()).hexdigest(),"timestamp":datetime.now(timezone.utc).isoformat()}
        with self.path.open("a",encoding="utf-8",newline="\n") as stream: stream.write(json.dumps(record,sort_keys=True,separators=(",",":"))+"\n"); stream.flush(); os.fsync(stream.fileno())


def _registered_worktrees(repository_root:Path)->tuple[Path,...]:
    output=subprocess.check_output(("git","worktree","list","--porcelain"),cwd=repository_root,text=True); return tuple(Path(line[9:]).resolve() for line in output.splitlines() if line.startswith("worktree "))

def _inside_any_git_repository(path:Path)->bool:
    for parent in (path if path.is_dir() else path.parent, *(path if path.is_dir() else path.parent).parents):
        if (parent/".git").exists(): return True
    return False

def _validate_protected_path(path:Path,label:str,repository_root:Path,*,must_exist:bool)->None:
    resolved=path.resolve()
    if must_exist and not resolved.is_file(): raise ValueError(f"{label} is unavailable")
    target=resolved if resolved.exists() else resolved.parent
    if not target.exists(): raise ValueError(f"{label} parent is unavailable")
    for parent in (target,*target.parents):
        try: attributes=getattr(os.lstat(parent),"st_file_attributes",0)
        except OSError as exc: raise ValueError(f"{label} cannot be validated") from exc
        if attributes & getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0): raise ValueError(f"{label} may not traverse a reparse point")
    if _inside_any_git_repository(resolved): raise ValueError(f"{label} must be outside every Git repository")
    for worktree in _registered_worktrees(repository_root):
        if _is_within(resolved,worktree): raise ValueError(f"{label} must be outside governed Git worktrees")
    if os.name=="nt": _validate_windows_acl(target,label)

def _is_within(path:Path,root:Path)->bool:
    try: path.relative_to(root); return True
    except ValueError: return False

def _validate_windows_acl(path:Path,label:str)->None:
    script=r'''$acl=Get-Acl -LiteralPath $args[0]; $current=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; $allowed=@($current,'S-1-5-18','S-1-5-32-544'); $owner=$acl.Owner; try{$owner=(New-Object System.Security.Principal.NTAccount($owner)).Translate([System.Security.Principal.SecurityIdentifier]).Value}catch{}; $bad=@(); foreach($entry in $acl.Access){try{$sid=$entry.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value}catch{$bad+='UNRESOLVED';continue}; $rights=[string]$entry.FileSystemRights; if($entry.AccessControlType -eq 'Allow' -and $rights -match 'Write|Modify|FullControl|TakeOwnership|ChangePermissions|Delete' -and $sid -notin $allowed){$bad+=$sid}}; @{current=$current;owner=$owner;bad=$bad}|ConvertTo-Json -Compress'''
    try: value=json.loads(subprocess.check_output(("powershell.exe","-NoProfile","-NonInteractive","-Command",script,str(path)),text=True,stderr=subprocess.STDOUT))
    except Exception as exc: raise ValueError(f"{label} ACL cannot be validated") from exc
    if value.get("owner") not in {value.get("current"),"S-1-5-18","S-1-5-32-544"} or value.get("bad"): raise ValueError(f"{label} ACL is unsafe")

def _repository_identity(root:Path)->str:
    common=subprocess.check_output(("git","rev-parse","--git-common-dir"),cwd=root,text=True).strip(); common_path=Path(common); common_path=common_path if common_path.is_absolute() else root/common_path
    return canonical_digest({"root":str(root.resolve()),"git_common_dir":str(common_path.resolve())})

def _current_windows_sid()->str:
    if os.name!="nt": raise RuntimeError("Windows identity unavailable")
    return subprocess.check_output(("powershell.exe","-NoProfile","-NonInteractive","-Command","[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"),text=True,stderr=subprocess.STDOUT).strip()

class _DATA_BLOB(ctypes.Structure): _fields_=[("cbData",wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_byte))]
def _blob(data:bytes):
    buffer=ctypes.create_string_buffer(data); return _DATA_BLOB(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_byte))),buffer
def _crypt_unprotect(ciphertext:bytes,*,entropy:bytes)->bytes:
    source,sb=_blob(ciphertext); ent,eb=_blob(entropy); destination=_DATA_BLOB(); crypt32=ctypes.windll.crypt32; kernel32=ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(ctypes.byref(source),None,ctypes.byref(ent),None,None,0,ctypes.byref(destination)): raise OSError("CryptUnprotectData failed")
    _=(sb,eb)
    try:return ctypes.string_at(destination.pbData,destination.cbData)
    finally:kernel32.LocalFree(destination.pbData)
def _crypt_protect(plaintext:bytes,*,entropy:bytes)->bytes:
    source,sb=_blob(plaintext); ent,eb=_blob(entropy); destination=_DATA_BLOB(); crypt32=ctypes.windll.crypt32; kernel32=ctypes.windll.kernel32
    # flags=0 is deliberately current-user scope; CRYPTPROTECT_LOCAL_MACHINE is never supplied.
    if not crypt32.CryptProtectData(ctypes.byref(source),None,ctypes.byref(ent),None,None,0,ctypes.byref(destination)): raise OSError("CryptProtectData failed")
    _=(sb,eb)
    try:return ctypes.string_at(destination.pbData,destination.cbData)
    finally:kernel32.LocalFree(destination.pbData)
