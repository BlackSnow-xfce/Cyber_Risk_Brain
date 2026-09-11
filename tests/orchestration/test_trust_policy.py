import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from aidp_orchestration.ed25519 import AIDPSignatureV1, _signed_bytes
from aidp_orchestration.foundation import canonical_bytes, foundation_status
from aidp_orchestration.trust_policy import (
    CHECKPOINT_SCHEMA, POLICY_SCHEMA, SourceAuthorizationPolicyV1,
    TrustStoreCheckpointStore, TrustStoreCheckpointV1,
)

NOW = "2026-09-11T12:00:00.000000Z"


def _signed(payload, key, key_id):
    sig = key.sign(_signed_bytes(canonical_bytes(payload), "aidp-attestation-v1"))
    return AIDPSignatureV1("aidp-attestation-v1", "Ed25519", key_id,
        hashlib.sha256(canonical_bytes(payload)).hexdigest(),
        __import__("base64").urlsafe_b64encode(sig).decode()).encoded()


def _checkpoint(key):
    payload = {"schema_version": CHECKPOINT_SCHEMA, "domain": "aidp-trust-store", "environment": "test",
        "trust_store_id": "ts", "version": 1, "monotonic_epoch": 1, "previous_checkpoint_digest": "",
        "issued_at": NOW, "valid_until": "2026-09-11T13:00:00.000000Z", "revocation_epoch": 1,
        "authorized_category_key_mappings": [], "checkpoint_signer": "ops", "signer_key_id": "k"}
    return canonical_bytes({**payload, "signature": json.loads(_signed(payload, key, "k"))})


def test_trust_checkpoint_cas_and_rollback(tmp_path):
    key = Ed25519PrivateKey.generate(); raw = key.public_key().public_bytes_raw()
    checkpoint = TrustStoreCheckpointV1.parse(_checkpoint(key))
    store = TrustStoreCheckpointStore(tmp_path / "trust.json")
    store.accept(checkpoint, environment="test", trust_store_id="ts", public_key=raw, now=NOW, previous_digest=None)
    with pytest.raises(ValueError): store.accept(checkpoint, environment="test", trust_store_id="ts", public_key=raw, now=NOW, previous_digest=None)


def test_policy_exact_tuple_and_readiness():
    assert foundation_status()["TRUST_STORE_READY"] == "UNCONFIGURED"
    assert foundation_status()["SOURCE_AUTHORIZATION_READY"] == "UNCONFIGURED"
