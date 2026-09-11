"""AIDP-SIG-V1 Ed25519 foundation; no production key storage."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass

from .foundation import DOMAIN_SEPARATOR, canonical_bytes, canonical_digest

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError:  # pragma: no cover - exercised by dependency-absent tests
    InvalidSignature = None
    Ed25519PrivateKey = Ed25519PublicKey = None


@dataclass(frozen=True, slots=True)
class AIDPSignatureV1:
    schema_version: str
    algorithm: str
    key_id: str
    payload_digest: str
    signature: str

    def encoded(self) -> bytes:
        return canonical_bytes({"algorithm": self.algorithm, "key_id": self.key_id,
                                "payload_digest": self.payload_digest,
                                "schema_version": self.schema_version, "signature": self.signature})


def _require_crypto() -> None:
    if Ed25519PublicKey is None:
        raise RuntimeError("Ed25519 dependency unavailable")


def _signed_bytes(payload: bytes, schema_version: str) -> bytes:
    return DOMAIN_SEPARATOR + schema_version.encode("utf-8") + b"\x00" + payload


def sign_for_test(payload: bytes, *, key_id: str, private_key: bytes, schema_version: str) -> bytes:
    _require_crypto()
    if schema_version != "aidp-attestation-v1" or not key_id:
        raise ValueError("invalid AIDP signature binding")
    try: key = Ed25519PrivateKey.from_private_bytes(private_key)
    except (ValueError, TypeError): raise ValueError("malformed Ed25519 private key") from None
    signature = key.sign(_signed_bytes(payload, schema_version))
    digest = hashlib.sha256(payload).hexdigest()
    return AIDPSignatureV1(schema_version, "Ed25519", key_id, digest,
                           base64.urlsafe_b64encode(signature).decode("ascii")).encoded()


def verify(payload: bytes, envelope: bytes, *, key_id: str, public_key: bytes, schema_version: str) -> None:
    _require_crypto()
    try:
        value = json.loads(envelope.decode("utf-8"))
        if not isinstance(value, dict) or set(value) != {"algorithm", "key_id", "payload_digest", "schema_version", "signature"}:
            raise ValueError("malformed AIDP-SIG-V1 envelope")
        if value["schema_version"] != schema_version or value["algorithm"] != "Ed25519" or value["key_id"] != key_id:
            raise ValueError("AIDP signature binding mismatch")
        if value["payload_digest"] != hashlib.sha256(payload).hexdigest(): raise ValueError("payload digest mismatch")
        signature = base64.urlsafe_b64decode(value["signature"].encode("ascii"))
        if len(signature) != 64: raise ValueError("invalid Ed25519 signature length")
        public = Ed25519PublicKey.from_public_bytes(public_key)
        public.verify(signature, _signed_bytes(payload, schema_version))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        raise ValueError("invalid AIDP-SIG-V1 envelope") from None
    except InvalidSignature:
        raise ValueError("invalid Ed25519 signature") from None
