"""Production deployment primitives for the Product Owner confirmation service."""

from __future__ import annotations

import base64
import ctypes
import json
import os
from ctypes import wintypes
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from .product_owner_oidc import ProductOwnerOIDCConfig, ProtectedSecretProvider, SecurityAuditSink


@dataclass(frozen=True, slots=True)
class ProductOwnerDeploymentConfig:
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
    security_audit_file: Path
    oidc_ca_bundle: Path | None = None

    @classmethod
    def load(cls, path: Path) -> "ProductOwnerDeploymentConfig":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("deployment configuration must be an object")
        required = {
            "repository_root", "bind_host", "bind_port", "public_origin", "issuer",
            "client_id", "audience", "policy_version", "tls_certificate",
            "tls_private_key", "protected_secret_file", "security_audit_file",
        }
        optional = {"oidc_ca_bundle"}
        if set(raw) != required | (set(raw) & optional) or not required.issubset(raw):
            raise ValueError("deployment configuration contains missing or unknown fields")
        base = path.resolve().parent

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
            security_audit_file=absolute(raw["security_audit_file"], "security_audit_file"),
            oidc_ca_bundle=None if ca is None else absolute(ca, "oidc_ca_bundle"),
        )

    def validate_files(self) -> None:
        if not self.repository_root.is_dir():
            raise ValueError("repository_root is unavailable")
        for path, label in (
            (self.tls_certificate, "TLS certificate"),
            (self.tls_private_key, "TLS private key"),
            (self.protected_secret_file, "protected OIDC credential"),
        ):
            if not path.is_file():
                raise ValueError(f"{label} is unavailable")
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
    """Read one DPAPI-protected client secret. Plaintext is never stored in config or Git."""

    def __init__(self, path: Path, *, expected_client_id: str) -> None:
        self.path = path
        self.expected_client_id = expected_client_id

    def client_secret(self, client_id: str) -> str:
        if os.name != "nt" or client_id != self.expected_client_id:
            raise RuntimeError("protected credential unavailable")
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"schema_version", "client_id", "ciphertext"}:
            raise RuntimeError("protected credential unavailable")
        if payload["schema_version"] != "aidp-dpapi-secret-v1" or payload["client_id"] != client_id:
            raise RuntimeError("protected credential unavailable")
        try:
            encrypted = base64.b64decode(payload["ciphertext"], validate=True)
            plaintext = _crypt_unprotect(encrypted).decode("utf-8", "strict")
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
        "revocation",
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


def _repository_identity(root: Path) -> str:
    import hashlib

    return hashlib.sha256(str(root.resolve()).lower().encode("utf-8")).hexdigest()


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _crypt_unprotect(ciphertext: bytes) -> bytes:
    buffer = ctypes.create_string_buffer(ciphertext)
    source = _DATA_BLOB(len(ciphertext), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    destination = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination)):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)
