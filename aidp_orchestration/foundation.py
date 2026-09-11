"""Non-executing protocol foundations: canonical bytes and durable CAS."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

DOMAIN_SEPARATOR = bytes.fromhex("414944502D4154544553544154494F4E2D563100")
_INT_MIN, _INT_MAX = -(2**63 - 1), 2**63 - 1
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


def foundation_status() -> dict[str, str]:
    try:
        from .ed25519 import Ed25519PublicKey
        ed25519_ready = Ed25519PublicKey is not None
    except ImportError:
        ed25519_ready = False
    return {
        "CANONICALIZATION_READY": "READY",
        "CAS_READY": "READY",
        "ED25519_READY": "READY" if ed25519_ready else "BLOCKED",
        "TRUST_STORE_READY": "UNCONFIGURED",
        "SOURCE_AUTHORIZATION_READY": "UNCONFIGURED",
        "TRUST_STORE_UNCONFIGURED": "BLOCKED",
        "SOURCE_AUTHORIZATION_UNCONFIGURED": "BLOCKED",
        "SUPERVISOR_ADMISSION_NOT_IMPLEMENTED": "BLOCKED",
        "PRODUCTION_RECOVERY_BLOCKED": "BLOCKED",
    }


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        normalized = unicodedata.normalize("NFC", value)
        if any(0xD800 <= ord(char) <= 0xDFFF for char in normalized):
            raise ValueError("lone surrogate is forbidden")
        return normalized
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    normalized: set[str] = set()
    for key, value in pairs:
        key = unicodedata.normalize("NFC", key)
        if key in normalized:
            raise ValueError("duplicate object key")
        normalized.add(key)
        result[key] = value
    return result


def _integer(value: str) -> int:
    if not re.fullmatch(r"0|-[1-9][0-9]*|[1-9][0-9]*", value):
        raise ValueError("non-canonical integer")
    number = int(value)
    if not _INT_MIN <= number <= _INT_MAX:
        raise ValueError("integer out of range")
    return number


def _reject_float(value: str) -> None:
    raise ValueError("decimal and exponent numbers are forbidden")


def parse_canonical_utf8(payload: bytes) -> Any:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    text = payload.decode("utf-8", errors="strict")
    value = json.loads(text, object_pairs_hook=_pairs, parse_int=_integer, parse_float=_reject_float,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid constant: {value}")))
    return _normalize(value)


def canonical_bytes(value: Any) -> bytes:
    value = _normalize(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_timestamp(value: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        raise ValueError("timestamp must be UTC with six fractional digits")
    if value[17:19] == "60":
        raise ValueError("leap seconds are forbidden")
    return value


class DurableCAS:
    """Small fail-closed version/digest CAS record; no silent initialization reset."""
    def __init__(self, path: Path):
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")

    def read(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        raw = self.path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict) or set(value) != {"version", "digest", "payload"}:
            raise ValueError("corrupt CAS record")
        if type(value["version"]) is not int or value["version"] < 0 or value["digest"] != canonical_digest(value["payload"]):
            raise ValueError("corrupt CAS record")
        return value

    def compare_and_swap(self, *, expected_version: int | None, expected_digest: str | None,
                         payload: Any) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError("CAS busy") from exc
        try:
            current = self.read()
            if (current is None) != (expected_version is None):
                raise RuntimeError("CAS version mismatch")
            if current is not None and (current["version"] != expected_version or current["digest"] != expected_digest):
                raise RuntimeError("CAS version mismatch")
            next_value = {"version": 0 if current is None else current["version"] + 1,
                          "payload": _normalize(payload)}
            next_value["digest"] = canonical_digest(next_value["payload"])
            encoded = json.dumps(next_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            with tempfile.NamedTemporaryFile(dir=self.path.parent, delete=False) as stream:
                temp = Path(stream.name); stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp, self.path)
            if self.read() != next_value:
                raise RuntimeError("CAS readback failed")
            return next_value
        finally:
            os.close(fd); self.lock_path.unlink(missing_ok=True)
