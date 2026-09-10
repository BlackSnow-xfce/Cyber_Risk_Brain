"""Production deployment primitives for Product Owner confirmation."""
from __future__ import annotations

import argparse
import base64
import ctypes
import getpass
import json
import os
import secrets
import stat
import subprocess
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .contracts import canonical_digest
from .product_owner_oidc import ProductOwnerOIDCConfig, ProtectedSecretProvider, SecurityAuditSink

DPAPI_SCHEMA = "aidp-dpapi-secret-v4"
PROVISIONING_SCHEMA = "aidp-dpapi-trusted-provisioning-v1"
ISSUER_CLIENT_ID = "aidp-product-owner-issuer"


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
    service_principal_sid: str
    tls_certificate: Path
    tls_private_key: Path
    protected_secret_file: Path
    trusted_issuer_token_file: Path
    security_audit_file: Path
    oidc_ca_bundle: Path | None = None

    @classmethod
    def load(cls, path: Path) -> "ProductOwnerDeploymentConfig":
        config_path = path.resolve()
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        required = {
            "repository_root", "bind_host", "bind_port", "public_origin", "issuer",
            "client_id", "audience", "policy_version", "service_principal_sid",
            "tls_certificate", "tls_private_key", "protected_secret_file",
            "trusted_issuer_token_file", "security_audit_file",
        }
        optional = {"oidc_ca_bundle"}
        if not isinstance(raw, dict) or set(raw) != required | (set(raw) & optional):
            raise ValueError("deployment configuration contains missing or unknown fields")
        base = config_path.parent

        def path_value(name: str) -> Path:
            value = raw[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty path")
            candidate = Path(value)
            return (candidate if candidate.is_absolute() else base / candidate).resolve()

        host, port, origin = raw["bind_host"], raw["bind_port"], raw["public_origin"]
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("confirmation service must bind to loopback")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("invalid confirmation service port")
        if not isinstance(origin, str):
            raise ValueError("public_origin must be explicit")
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("public_origin must be an exact HTTPS origin")
        strings = ("issuer", "client_id", "audience", "policy_version", "service_principal_sid")
        if any(not isinstance(raw[name], str) or not raw[name].strip() or "\n" in raw[name] or "\r" in raw[name] for name in strings):
            raise ValueError("deployment identity values must be explicit")
        ca = raw.get("oidc_ca_bundle")
        return cls(
            config_path, path_value("repository_root"), host, port, origin,
            raw["issuer"], raw["client_id"], raw["audience"], raw["policy_version"],
            raw["service_principal_sid"], path_value("tls_certificate"),
            path_value("tls_private_key"), path_value("protected_secret_file"),
            path_value("trusted_issuer_token_file"), path_value("security_audit_file"),
            None if ca is None else path_value("oidc_ca_bundle"),
        )

    def validate_files(self) -> None:
        if not self.repository_root.is_dir():
            raise ValueError("repository_root is unavailable")
        if os.name != "nt" or _current_windows_sid() != self.service_principal_sid:
            raise ValueError("configured service principal is not active")
        if not self.tls_certificate.is_file():
            raise ValueError("TLS certificate is unavailable")
        protected = (
            (self.deployment_config_file, "deployment configuration", True),
            (self.tls_private_key, "TLS private key", True),
            (self.protected_secret_file, "protected OIDC credential", True),
            (provisioning_evidence_path(self.protected_secret_file), "OIDC provisioning evidence", True),
            (self.trusted_issuer_token_file, "trusted issuance credential", True),
            (provisioning_evidence_path(self.trusted_issuer_token_file), "issuance provisioning evidence", True),
            (self.security_audit_file, "security audit destination", False),
        )
        for candidate, label, must_exist in protected:
            validate_protected_path(candidate, label, self.repository_root, self.service_principal_sid, must_exist)
        if self.oidc_ca_bundle is not None and not self.oidc_ca_bundle.is_file():
            raise ValueError("OIDC CA bundle is unavailable")
        self.security_audit_file.parent.mkdir(parents=True, exist_ok=True)

    def validate_provisioning_authority(self) -> None:
        """Validate the trusted operator boundary before creating credentials."""
        if not self.repository_root.is_dir():
            raise ValueError("repository_root is unavailable")
        if os.name != "nt" or _current_windows_sid() != self.service_principal_sid:
            raise ValueError("configured service principal is not active")
        validate_protected_path(
            self.deployment_config_file,
            "deployment configuration",
            self.repository_root,
            self.service_principal_sid,
            True,
        )

    def oidc_config(self) -> ProductOwnerOIDCConfig:
        return ProductOwnerOIDCConfig(
            issuer=self.issuer, client_id=self.client_id, audience=self.audience,
            redirect_uri=self.public_origin + "/product-owner/confirm/callback",
            post_logout_redirect_uri=self.public_origin + "/signed-out",
            repository_identity=_repository_identity(self.repository_root),
            policy_version=self.policy_version,
            maximum_authentication_age=timedelta(minutes=5),
        )


class WindowsDPAPISecretProvider(ProtectedSecretProvider):
    """Read a DPAPI artifact admitted by protected provisioning evidence."""

    def __init__(
        self,
        path: Path,
        *,
        expected_client_id: str,
        expected_principal_sid: str,
        repository_root: Path,
    ) -> None:
        self.path = path.resolve()
        self.expected_client_id = expected_client_id
        self.expected_principal_sid = expected_principal_sid
        self.repository_root = repository_root.resolve()

    def client_secret(self, client_id: str) -> str:
        try:
            if (
                os.name != "nt"
                or client_id != self.expected_client_id
                or _current_windows_sid() != self.expected_principal_sid
            ):
                raise RuntimeError
            for candidate, label in (
                (self.path, "protected credential"),
                (provisioning_evidence_path(self.path), "provisioning evidence"),
            ):
                validate_protected_path(
                    candidate,
                    label,
                    self.repository_root,
                    self.expected_principal_sid,
                    True,
                )
            payload = _strict_json(
                self.path,
                {
                    "schema_version",
                    "client_id",
                    "protection_scope",
                    "principal_sid",
                    "ciphertext",
                    "artifact_digest",
                },
            )
            digest = _artifact_digest(payload)
            if (
                payload.get("artifact_digest") != digest
                or payload.get("schema_version") != DPAPI_SCHEMA
                or payload.get("client_id") != client_id
                or payload.get("protection_scope") != "current-user"
                or payload.get("principal_sid") != self.expected_principal_sid
            ):
                raise RuntimeError
            evidence = _strict_json(
                provisioning_evidence_path(self.path),
                {
                    "schema_version",
                    "artifact_digest",
                    "client_id",
                    "principal_sid",
                    "provisioned_at",
                    "provisioning_method",
                    "evidence_id",
                },
            )
            evidence_id = canonical_digest(
                {key: value for key, value in evidence.items() if key != "evidence_id"}
            )
            if (
                evidence.get("schema_version") != PROVISIONING_SCHEMA
                or evidence.get("artifact_digest") != digest
                or evidence.get("client_id") != client_id
                or evidence.get("principal_sid") != self.expected_principal_sid
                or evidence.get("provisioning_method")
                != "crypt-protect-data-current-user-flags-0"
                or evidence.get("evidence_id") != evidence_id
            ):
                raise RuntimeError
            if datetime.fromisoformat(str(evidence["provisioned_at"])).utcoffset() is None:
                raise RuntimeError
            encrypted = base64.b64decode(str(payload["ciphertext"]), validate=True)
            plaintext = _crypt_unprotect(encrypted, entropy=_entropy(client_id, self.expected_principal_sid)).decode("utf-8", "strict")
        except Exception as exc:
            raise RuntimeError("protected credential unavailable") from exc
        if not plaintext or len(plaintext) > 4096 or "\x00" in plaintext:
            raise RuntimeError("protected credential unavailable")
        return plaintext


def provision_current_user_dpapi_secret(
    config: ProductOwnerDeploymentConfig,
    *,
    client_id: str,
    path: Path,
    plaintext: str,
) -> str:
    """Create one credential; exact principal plus ACL custody is authority."""
    target = path.resolve()
    config.validate_provisioning_authority()
    if (
        client_id not in {config.client_id, ISSUER_CLIENT_ID}
        or target not in {config.protected_secret_file, config.trusted_issuer_token_file}
        or not plaintext
        or len(plaintext) > 4096
        or "\x00" in plaintext
    ):
        raise RuntimeError("secret provisioning unavailable")
    sid = _current_windows_sid()
    if sid != config.service_principal_sid:
        raise RuntimeError("secret provisioning unavailable")
    evidence_path = provisioning_evidence_path(target)
    if target.exists() or evidence_path.exists():
        raise RuntimeError("credential already provisioned")
    _validate_destination(target, config.repository_root, sid)
    ciphertext = _crypt_protect(plaintext.encode(), entropy=_entropy(client_id, sid))
    artifact: dict[str, object] = {
        "schema_version": DPAPI_SCHEMA,
        "client_id": client_id,
        "protection_scope": "current-user",
        "principal_sid": sid,
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }
    artifact["artifact_digest"] = _artifact_digest(artifact)
    evidence: dict[str, object] = {
        "schema_version": PROVISIONING_SCHEMA,
        "artifact_digest": artifact["artifact_digest"],
        "client_id": client_id,
        "principal_sid": sid,
        "provisioned_at": datetime.now(timezone.utc).isoformat(),
        "provisioning_method": "crypt-protect-data-current-user-flags-0",
    }
    evidence["evidence_id"] = canonical_digest(evidence)
    _write_protected_json(target, artifact, sid)
    try:
        _write_protected_json(evidence_path, evidence, sid)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return str(evidence["evidence_id"])


class JsonLineSecurityAuditSink(SecurityAuditSink):
    _ALLOWED = {"authentication_failure", "request_failure", "login_initiation", "authentication_success", "confirmation_result", "logout", "dependency_failure", "authorization_success", "authorization_failure", "revocation", "issuance_failure", "issuance_success"}
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def __call__(self, event: str, correlation: str) -> None:
        if event not in self._ALLOWED or not isinstance(correlation, str) or not correlation:
            raise RuntimeError("invalid security audit event")
        import hashlib
        record = {"schema_version": "aidp-product-owner-security-audit-v1", "event": event, "correlation_digest": hashlib.sha256(correlation.encode()).hexdigest(), "timestamp": datetime.now(timezone.utc).isoformat()}
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())


def provisioning_evidence_path(path: Path) -> Path:
    return path.with_name(path.name + ".provisioning.json")


def _strict_json(path: Path, fields: set[str]) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != fields:
        raise RuntimeError("protected credential unavailable")
    return value


def _artifact_digest(payload: dict[str, object]) -> str:
    return canonical_digest({key: value for key, value in payload.items() if key != "artifact_digest"})


def _entropy(client_id: str, sid: str) -> bytes:
    return canonical_digest({"client_id": client_id, "principal_sid": sid}).encode("ascii")


def _write_protected_json(path: Path, value: dict[str, object], sid: str) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")))
            stream.flush()
            os.fsync(stream.fileno())
        _apply_windows_acl(path, sid)
        _validate_windows_acl(path, "provisioned credential", sid)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _registered_worktrees(root: Path) -> tuple[Path, ...]:
    output = subprocess.check_output(("git", "worktree", "list", "--porcelain"), cwd=root, text=True)
    return tuple(Path(line[9:]).resolve() for line in output.splitlines() if line.startswith("worktree "))


def _inside_any_git_repository(path: Path) -> bool:
    start = path if path.is_dir() else path.parent
    return any((parent / ".git").exists() for parent in (start, *start.parents))


def _validate_destination(path: Path, repository_root: Path, sid: str) -> None:
    if _inside_any_git_repository(path) or any(_is_within(path, root) for root in _registered_worktrees(repository_root)):
        raise ValueError("protected credential must be outside every Git repository")
    if not path.parent.is_dir():
        raise ValueError("protected credential parent is unavailable")
    _reject_reparse(path.parent, "protected credential")
    _validate_windows_acl(path.parent, "protected credential parent", sid)


def validate_protected_path(path: Path, label: str, repository_root: Path, sid: str, must_exist: bool) -> None:
    resolved = path.resolve()
    if must_exist and not resolved.is_file():
        raise ValueError(f"{label} is unavailable")
    target = resolved if resolved.exists() else resolved.parent
    if not target.exists():
        raise ValueError(f"{label} parent is unavailable")
    _reject_reparse(target, label)
    if _inside_any_git_repository(resolved) or any(_is_within(resolved, root) for root in _registered_worktrees(repository_root)):
        raise ValueError(f"{label} must be outside every Git repository")
    if os.name == "nt":
        _validate_windows_acl(target, label, sid)
        _validate_windows_acl(target.parent, f"{label} parent", sid)


def _reject_reparse(path: Path, label: str) -> None:
    for candidate in (path, *path.parents):
        try:
            attributes = getattr(os.lstat(candidate), "st_file_attributes", 0)
        except OSError as exc:
            raise ValueError(f"{label} cannot be validated") from exc
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"{label} may not traverse a reparse point")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_windows_acl(path: Path, label: str, sid: str) -> None:
    script = r"""$acl=Get-Acl -LiteralPath $args[0]; $allowed=@($args[1],'S-1-5-18','S-1-5-32-544'); $owner=$acl.Owner; try{$owner=(New-Object System.Security.Principal.NTAccount($owner)).Translate([System.Security.Principal.SecurityIdentifier]).Value}catch{}; $bad=@(); foreach($entry in $acl.Access){try{$entrySid=$entry.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value}catch{$bad+='UNRESOLVED';continue}; $rights=[string]$entry.FileSystemRights; if($entry.AccessControlType -eq 'Allow' -and $rights -match 'Write|Modify|FullControl|TakeOwnership|ChangePermissions|Delete' -and $entrySid -notin $allowed){$bad+=$entrySid}}; @{owner=$owner;bad=$bad}|ConvertTo-Json -Compress"""
    try:
        result = json.loads(subprocess.check_output(("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script, str(path), sid), text=True, stderr=subprocess.STDOUT))
    except Exception as exc:
        raise ValueError(f"{label} ACL cannot be validated") from exc
    if result.get("owner") not in {sid, "S-1-5-18", "S-1-5-32-544"} or result.get("bad"):
        raise ValueError(f"{label} ACL is unsafe")


def _apply_windows_acl(path: Path, sid: str) -> None:
    script = r"""$path=$args[0]; $sid=New-Object System.Security.Principal.SecurityIdentifier($args[1]); $system=New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18'); $admins=New-Object System.Security.Principal.SecurityIdentifier('S-1-5-32-544'); $acl=Get-Acl -LiteralPath $path; $acl.SetAccessRuleProtection($true,$false); foreach($entry in @($acl.Access)){[void]$acl.RemoveAccessRuleSpecific($entry)}; foreach($principal in @($sid,$system,$admins)){$rule=New-Object System.Security.AccessControl.FileSystemAccessRule($principal,'FullControl','Allow'); $acl.AddAccessRule($rule)}; $acl.SetOwner($sid); Set-Acl -LiteralPath $path -AclObject $acl"""
    try:
        subprocess.check_output(("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script, str(path), sid), text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        raise RuntimeError("protected ACL provisioning failed") from exc


def _repository_identity(root: Path) -> str:
    common = Path(subprocess.check_output(("git", "rev-parse", "--git-common-dir"), cwd=root, text=True).strip())
    if not common.is_absolute():
        common = root / common
    return canonical_digest({"root": str(root.resolve()), "git_common_dir": str(common.resolve())})


def _current_windows_sid() -> str:
    if os.name != "nt":
        raise RuntimeError("Windows identity unavailable")
    return subprocess.check_output(("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"), text=True, stderr=subprocess.STDOUT).strip()


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _crypt_unprotect(ciphertext: bytes, *, entropy: bytes) -> bytes:
    source, source_buffer = _blob(ciphertext)
    entropy_blob, entropy_buffer = _blob(entropy)
    destination = _DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source), None, ctypes.byref(entropy_blob), None, None, 0, ctypes.byref(destination)):
        raise OSError("CryptUnprotectData failed")
    _ = (source_buffer, entropy_buffer)
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(destination.pbData)


def _crypt_protect(plaintext: bytes, *, entropy: bytes) -> bytes:
    source, source_buffer = _blob(plaintext)
    entropy_blob, entropy_buffer = _blob(entropy)
    destination = _DATA_BLOB()
    # flags=0 is the governed current-user creation path. DPAPI does not expose
    # the original scope during decryption; trusted evidence plus ACL custody does.
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(source), None, ctypes.byref(entropy_blob), None, None, 0, ctypes.byref(destination)):
        raise OSError("CryptProtectData failed")
    _ = (source_buffer, entropy_buffer)
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(destination.pbData)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision Product Owner credentials")
    parser.add_argument("provision", choices=("provision",))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--credential", choices=("oidc-client", "trusted-issuer"), required=True)
    args = parser.parse_args(argv)
    config = ProductOwnerDeploymentConfig.load(args.config)
    if _current_windows_sid() != config.service_principal_sid:
        raise RuntimeError("provisioning must run as the configured service principal")
    target, client_id = (config.protected_secret_file, config.client_id) if args.credential == "oidc-client" else (config.trusted_issuer_token_file, ISSUER_CLIENT_ID)
    first = getpass.getpass("Secret: ")
    second = getpass.getpass("Confirm secret: ")
    if not first or not secrets.compare_digest(first, second):
        raise RuntimeError("secret confirmation failed")
    evidence_id = provision_current_user_dpapi_secret(config, client_id=client_id, path=target, plaintext=first)
    print(f"PROVISIONED {client_id} evidence={evidence_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
