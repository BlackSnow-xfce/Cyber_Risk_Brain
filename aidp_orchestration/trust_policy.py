"""Non-configuring trust-store and source-policy foundations.

These objects only validate signed, canonical data.  They do not load keys,
configure production trust, or authorize recovery.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ed25519 import verify
from .foundation import DurableCAS, canonical_bytes, canonical_digest, parse_canonical_utf8, validate_timestamp

CHECKPOINT_SCHEMA = "aidp-trust-store-checkpoint-v1"
POLICY_SCHEMA = "aidp-source-authorization-policy-v1"


def _object(value: bytes, schema: str, fields: set[str]) -> dict[str, Any]:
    parsed = parse_canonical_utf8(value)
    if not isinstance(parsed, dict) or set(parsed) != fields or parsed.get("schema_version") != schema:
        raise ValueError("invalid signed trust object")
    return parsed


def _fresh(value: dict[str, Any], now: str) -> None:
    validate_timestamp(now)
    validate_timestamp(value["issued_at"]); validate_timestamp(value["valid_until"])
    if not value["issued_at"] <= now <= value["valid_until"]:
        raise ValueError("signed trust object is stale or not yet valid")


@dataclass(frozen=True, slots=True)
class TrustStoreCheckpointV1:
    payload: dict[str, Any]
    signature: bytes

    def payload_bytes(self) -> bytes:
        return canonical_bytes(self.payload)

    def encoded(self) -> bytes:
        return canonical_bytes({**self.payload, "signature": parse_canonical_utf8(self.signature)})

    @classmethod
    def parse(cls, encoded: bytes) -> "TrustStoreCheckpointV1":
        fields = {"schema_version", "domain", "environment", "trust_store_id", "version", "monotonic_epoch",
                  "previous_checkpoint_digest", "issued_at", "valid_until", "revocation_epoch",
                  "authorized_category_key_mappings", "checkpoint_signer", "signer_key_id", "signature"}
        value = _object(encoded, CHECKPOINT_SCHEMA, fields)
        signature = canonical_bytes(value.pop("signature"))
        if value["domain"] != "aidp-trust-store" or not isinstance(value["version"], int):
            raise ValueError("invalid trust-store checkpoint")
        return cls(value, signature)

    def verify(self, *, public_key: bytes, environment: str, trust_store_id: str, now: str,
               previous_digest: str | None, highest_epoch: int = -1, highest_revocation_epoch: int = -1) -> None:
        if self.payload["environment"] != environment or self.payload["trust_store_id"] != trust_store_id:
            raise ValueError("trust-store binding mismatch")
        _fresh(self.payload, now)
        if self.payload["monotonic_epoch"] <= highest_epoch or self.payload["revocation_epoch"] < highest_revocation_epoch:
            raise ValueError("trust-store rollback")
        if self.payload["previous_checkpoint_digest"] != (previous_digest or ""):
            raise ValueError("trust-store chain mismatch")
        verify(self.payload_bytes(), self.signature, key_id=self.payload["signer_key_id"], public_key=public_key,
               schema_version="aidp-attestation-v1")


class TrustStoreCheckpointStore:
    def __init__(self, path: Path):
        self._cas = DurableCAS(path)

    def highest(self) -> dict[str, Any] | None:
        return self._cas.read()

    def accept(self, checkpoint: TrustStoreCheckpointV1, *, environment: str, trust_store_id: str,
               public_key: bytes, now: str, previous_digest: str | None) -> dict[str, Any]:
        current = self._cas.read()
        checkpoint.verify(public_key=public_key, environment=environment, trust_store_id=trust_store_id, now=now,
                          previous_digest=previous_digest,
                          highest_epoch=-1 if current is None else current["payload"]["monotonic_epoch"],
                          highest_revocation_epoch=-1 if current is None else current["payload"]["revocation_epoch"])
        return self._cas.compare_and_swap(expected_version=None if current is None else current["version"],
                                          expected_digest=None if current is None else current["digest"],
                                          payload={"environment": environment, "trust_store_id": trust_store_id,
                                                   "monotonic_epoch": checkpoint.payload["monotonic_epoch"],
                                                   "revocation_epoch": checkpoint.payload["revocation_epoch"],
                                                   "checkpoint_digest": canonical_digest(checkpoint.payload)})


@dataclass(frozen=True, slots=True)
class SourceAuthorizationPolicyV1:
    payload: dict[str, Any]
    signature: bytes

    def payload_bytes(self) -> bytes:
        return canonical_bytes(self.payload)

    @classmethod
    def parse(cls, encoded: bytes) -> "SourceAuthorizationPolicyV1":
        value = parse_canonical_utf8(encoded)
        fields = {"schema_version", "domain", "environment", "policy_epoch", "previous_policy_digest", "issued_at", "valid_until", "rows", "signer_key_id", "signature"}
        if not isinstance(value, dict) or set(value) != fields or value["schema_version"] != POLICY_SCHEMA:
            raise ValueError("invalid source authorization policy")
        signature = canonical_bytes(value.pop("signature"))
        if value["domain"] != "aidp-source-authorization":
            raise ValueError("invalid source authorization policy")
        return cls(value, signature)

    def verify(self, *, public_key: bytes, environment: str, now: str, highest_epoch: int = -1,
               previous_digest: str | None = None) -> None:
        if self.payload["environment"] != environment or self.payload["policy_epoch"] <= highest_epoch:
            raise ValueError("source policy rollback or environment mismatch")
        if self.payload["previous_policy_digest"] != (previous_digest or ""):
            raise ValueError("source policy chain mismatch")
        verify(self.payload_bytes(), self.signature, key_id=self.payload["signer_key_id"], public_key=public_key,
               schema_version="aidp-attestation-v1")
        _fresh({"issued_at": self.payload["issued_at"], "valid_until": self.payload["valid_until"]}, now)

    def authorize(self, request: dict[str, Any], *, trust_store_id: str, trust_store_epoch: int,
                  revoked_key_ids: set[str] = frozenset()) -> None:
        required = ("source_identity", "category", "schema", "environment", "endpoint_identity", "audience",
                    "key_namespace", "key_id", "algorithm", "trust_store_id", "minimum_epoch", "payload_schema")
        if set(request) != set(required) or request["trust_store_id"] != trust_store_id or request["minimum_epoch"] > trust_store_epoch:
            raise ValueError("source authorization denied")
        if request["key_id"] in revoked_key_ids or not any(row == request for row in self.payload["rows"]):
            raise ValueError("source authorization denied")
