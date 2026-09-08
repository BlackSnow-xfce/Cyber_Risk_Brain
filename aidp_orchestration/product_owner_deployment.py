"""Production deployment primitives for the Product Owner confirmation service."""

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
        if not isinstance(raw, dict):
            raise ValueError("deployment configuration must be an object")
        required = {
            "repository_root", "bind_host", "bind_port", "public_origin", "issuer",
            "client_id", "audience", "policy_version", "tls_certificate",
            "tls_private_key", "protected_secret_file", "trusted_issuer_token_file",
            "security_audit_file",
        }
        optional = {"oidc_ca_bundle"}
        if set(raw) != required | (set(raw) & optional) or not required.issubset(raw):
            raise ValueError("deployment configuration contains missing or unknown fields")
        base = resolved_config.parent

        def absolute(value: object, name: str) -> Path:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty path")
            candidate = Path(value)
            candidate = candidate if candidate.is_absolute() else base / candidate
            return candidate.resolve()

        bind_host = raw["bind_host"]
        bind_port = raw["bind_port"]
        public_origin = raw["public_origin"]
        if not isinstance(bind_host, str) or bind_host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("confirmation service must bind to loopback")
        if type(bind_port) is not int or not 1 <= bind_port <= 65535:
            raise ValueError("invalid confirmation service port")
        if not isinstance(public_origin, str):
            raise ValueError("public_origin must be explicit")
        parsed = urlsplit(public_origin)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("public_origin must be an exact HTTPS origin")
        for field in ("issuer", "client_id", "audience", "policy_version"):
            value = raw[field]
            if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
                raise ValueError(f"{field} must be explicit")
        ca = raw.get("oidc_ca_bundle")
        return cls(
            deployment_config_file=resolved_config,
            repository_root=absolute(raw["repository_root"], "repository_root"),
            bind_host=bind_host,
            bind_port=bind_port,
            public_origin=public_origin,
            issuer=raw["issuer"],
            client_id=raw["client_id"],
            audience=raw["audience"],
            policy_version=raw["policy_version"],
            tls_certificate=absolute(raw["tls_certificate"], "tls_certificate"),
            tls_private_key=absolute(raw["tls_private_key"], "tls_private_key"),
            protected_secret_file=absolute(raw["protected_secret_file"], "protected_secret_file"),
            trusted_issuer_token_file=absolute(raw["trusted_issuer_token_file"], "trusted_issuer_token_file"),
            security_audit_file=absolute(raw["security_audit_file"], "security_audit_file"),
            oidc_ca_bundle=None if ca is None else absolute(ca, "oidc_ca_bundle"),
        )

    def validate_files(self) -> None:
        if not self.repository_root.is_dir():
            raise ValueError("repository_root is unavailable")
        protected = (
            (self.deployment_config_file, "deployment configuration", True),
            (self.tls_private_key, "TLS private key", True),
            (self.protected_secret_file, "protected OIDC credential", True),
            (self.trusted_issuer_token_file, "trusted issuance credential", True),
            (self.security_audit_file, "security audit destination", False),
        )
        if not self.tls_certificate.is_file():
            raise ValueError("TLS certificate is unavailable")
        for path, label, must_exist in protected:
            _validate_protected_path(path, label, self.repository_root, must_exist=must_exist)
        if self.oidc_ca_bundle is not None and not self.oidc_ca_bundle.is_file():
            raise ValueError("OIDC CA bundle is unavailable")
        self.security_audit_file.parent.mkdir(parents=True, exist_ok=True)

    def oidc_config(self) -> ProductOwnerOIDCConfig:
        return ProductOwnerOIDCConfig(
            issuer=self.issuer,
            client_id=self.client_id,
            audience=self.audience,
            redirect_uri=self.public_origin + "/product-owner/confirm/callback",
            post_logout_redirect_uri=self.public_origin + "/signed-out",
            repository_identity=_repository_identity(self.repository_root),
            policy_version=self.policy_version,
            maximum_authentication_age=timedelta(minutes=5),
        )


class WindowsDPAPISecretProvider(ProtectedSecretProvider):
    """Read a current-user DPAPI value bound to the intended Windows principal."""

    def __init__(self, path: Path, *, expected_client_id: str) -> None:
        self.path = path
        self.expected_client_id = expected_client_id

    def client_secret(self, client_id: str) -> str:
        if os.name != "nt" or client_id != self.expected_client_id:
            raise RuntimeError("protected credential unavailable")
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        required = {"schema_version", "client_id", "protection_scope", "principal_sid", "ciphertext"}
        if not isinstance(payload, dict) or set(payload) != required:
            raise RuntimeError("protected credential unavailable")
        current_sid = _current_windows_sid()
        if (
            payload["schema_version"] != "aidp-dpapi-secret-v2"
            or payload["client_id"] != client_id
            or payload["protection_scope"] != "current-user"
            or payload["principal_sid"] != current_sid
        ):
            raise RuntimeError("protected credential unavailable")
        try:
            encrypted = base64.b64decode(payload["ciphertext"], validate=True)
            entropy = canonical_digest({"client_id": client_id, "principal_sid": current_sid}).encode("ascii")
            plaintext = _crypt_unprotect(encrypted, entropy=entropy).decode("utf-8", "strict")
        except Exception as exc:
            raise RuntimeError("protected credential unavailable") from exc
        if not plaintext or len(plaintext) > 4096 or "\x00" in plaintext:
            raise RuntimeError("protected credential unavailable")
        return plaintext


class JsonLineSecurityAuditSink(SecurityAuditSink):
    """Append bounded, sanitized security events only."""

    _ALLOWED = {
        "authentication_failure", "request_failure", "login_initiation",
        "authentication_success", "confirmation_result", "logout",
        "dependency_failure", "authorization_success", "authorization_failure",
        "revocation", "issuance_failure", "issuance_success",
    }

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, event: str, correlation: str) -> None:
        if event not in self._ALLOWED or not isinstance(correlation, str) or not correlation:
            raise RuntimeError("invalid security audit event")
        import hashlib
        from datetime import datetime, timezone

        record = {
            "schema_version": "aidp-product-owner-security-audit-v1",
            "event": event,
            "correlation_digest": hashlib.sha256(correlation.encode("utf-8")).hexdigest(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())


def _registered_worktrees(repository_root: Path) -> tuple[Path, ...]:
    output = subprocess.check_output(
        ("git", "worktree", "list", "--porcelain"), cwd=repository_root, text=True,
    )
    values = []
    for line in output.splitlines():
        if line.startswith("worktree "):
            values.append(Path(line.removeprefix("worktree ")).resolve())
    return tuple(values)


def _validate_protected_path(path: Path, label: str, repository_root: Path, *, must_exist: bool) -> None:
    resolved = path.resolve()
    if must_exist and not resolved.is_file():
        raise ValueError(f"{label} is unavailable")
    target = resolved if resolved.exists() else resolved.parent
    if not target.exists():
        raise ValueError(f"{label} parent is unavailable")
    for parent in (target, *target.parents):
        try:
            attributes = getattr(os.lstat(parent), "st_file_attributes", 0)
        except OSError as exc:
            raise ValueError(f"{label} cannot be validated") from exc
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"{label} may not traverse a reparse point")
    for worktree in _registered_worktrees(repository_root):
        if _is_within(resolved, worktree):
            raise ValueError(f"{label} must be outside governed Git worktrees")
    common = subprocess.check_output(
        ("git", "rev-parse", "--git-common-dir"), cwd=repository_root, text=True,
    ).strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (repository_root / common_path).resolve()
    if _is_within(resolved, common_path):
        raise ValueError(f"{label} must be outside Git metadata")
    if os.name == "nt":
        _validate_windows_acl(target, label)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_windows_acl(path: Path, label: str) -> None:
    script = r'''
$p = $args[0]
$acl = Get-Acl -LiteralPath $p
$current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$owner = $acl.Owner
try { $owner = (New-Object System.Security.Principal.NTAccount($owner)).Translate([System.Security.Principal.SecurityIdentifier]).Value } catch {}
$bad = @()
foreach ($entry in $acl.Access) {
  try { $sid = $entry.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value } catch { continue }
  if ($sid -in @('S-1-1-0','S-1-5-11','S-1-5-32-545')) {
    $rights = [string]$entry.FileSystemRights
    if ($entry.AccessControlType -eq 'Allow' -and $rights -match 'Write|Modify|FullControl|TakeOwnership|ChangePermissions|Delete') { $bad += $sid }
  }
}
@{ current=$current; owner=$owner; bad=$bad } | ConvertTo-Json -Compress
'''
    try:
        raw = subprocess.check_output(
            ("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script, str(path)),
            text=True, stderr=subprocess.STDOUT,
        )
        value = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"{label} ACL cannot be validated") from exc
    if value.get("owner") not in {value.get("current"), "S-1-5-18", "S-1-5-32-544"} or value.get("bad"):
        raise ValueError(f"{label} ACL is unsafe")


def _repository_identity(root: Path) -> str:
    common = subprocess.check_output(
        ("git", "rev-parse", "--git-common-dir"), cwd=root, text=True,
    ).strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = root / common_path
    return canonical_digest({"root": str(root.resolve()), "git_common_dir": str(common_path.resolve())})


def _current_windows_sid() -> str:
    if os.name != "nt":
        raise RuntimeError("Windows identity unavailable")
    try:
        return subprocess.check_output(
            ("powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"),
            text=True, stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        raise RuntimeError("Windows identity unavailable") from exc


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[_DATA_BLOB, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _crypt_unprotect(ciphertext: bytes, *, entropy: bytes) -> bytes:
    source, source_buffer = _blob(ciphertext)
    entropy_blob, entropy_buffer = _blob(entropy)
    destination = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, ctypes.byref(entropy_blob), None, None, 0, ctypes.byref(destination),
    ):
        raise OSError("CryptUnprotectData failed")
    _ = (source_buffer, entropy_buffer)
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)
