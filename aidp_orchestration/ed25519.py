"""AIDP-SIG-V1 Ed25519 foundation; no production key storage."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
from dataclasses import dataclass

from .foundation import DOMAIN_SEPARATOR, canonical_bytes, parse_canonical_utf8

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover - exercised by dependency-absent tests
    InvalidSignature = None
    Ed25519PublicKey = None

MAX_ENVELOPE_BYTES = 512
_SCHEMA = "aidp-attestation-v1"
_ENVELOPE_FIELDS = {"algorithm", "key_id", "payload_digest", "schema_version", "signature"}
_B64_SIGNATURE = re.compile(r"^[A-Za-z0-9_-]{86}==$")


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


def _parse_envelope(envelope: bytes) -> dict[str, str]:
    if len(envelope) > MAX_ENVELOPE_BYTES:
        raise ValueError("AIDP signature envelope too large")
    value = parse_canonical_utf8(envelope)
    if canonical_bytes(value) != envelope or not isinstance(value, dict) or set(value) != _ENVELOPE_FIELDS:
        raise ValueError("malformed AIDP-SIG-V1 envelope")
    if any(type(value[field]) is not str for field in _ENVELOPE_FIELDS):
        raise ValueError("malformed AIDP-SIG-V1 envelope")
    return value


def _decode_signature(value: str) -> bytes:
    if not _B64_SIGNATURE.fullmatch(value):
        raise ValueError("noncanonical signature encoding")
    try:
        decoded = base64.b64decode(value.replace("-", "+").replace("_", "/"), validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("invalid signature encoding") from None
    if len(decoded) != 64 or base64.urlsafe_b64encode(decoded).decode("ascii") != value:
        raise ValueError("invalid Ed25519 signature length")
    return decoded


def verify(payload: bytes, envelope: bytes, *, key_id: str, public_key: bytes, schema_version: str) -> None:
    _require_crypto()
    try:
        parsed_payload = parse_canonical_utf8(payload)
        if canonical_bytes(parsed_payload) != payload:
            raise ValueError("payload is not canonical")
        value = _parse_envelope(envelope)
        if value["schema_version"] != schema_version or value["algorithm"] != "Ed25519" or value["key_id"] != key_id:
            raise ValueError("AIDP signature binding mismatch")
        if value["payload_digest"] != hashlib.sha256(payload).hexdigest(): raise ValueError("payload digest mismatch")
        signature = _decode_signature(value["signature"])
        public = Ed25519PublicKey.from_public_bytes(public_key)
        public.verify(signature, _signed_bytes(payload, schema_version))
    except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        raise ValueError("invalid AIDP-SIG-V1 envelope") from None
    except InvalidSignature:
        raise ValueError("invalid Ed25519 signature") from None
