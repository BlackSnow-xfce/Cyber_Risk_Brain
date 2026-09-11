import base64
import json
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from aidp_orchestration.ed25519 import sign_for_test, verify
from aidp_orchestration.foundation import canonical_bytes

def test_ed25519_valid_and_binding_failures():
    private = Ed25519PrivateKey.generate(); raw = private.private_bytes_raw(); public = private.public_key().public_bytes_raw()
    payload = canonical_bytes({"domain": "aidp-test", "value": 1})
    envelope = sign_for_test(payload, key_id="test-key", private_key=raw, schema_version="aidp-attestation-v1")
    verify(payload, envelope, key_id="test-key", public_key=public, schema_version="aidp-attestation-v1")
    for kwargs in ({"key_id": "wrong"}, {"schema_version": "other"}, {"public_key": Ed25519PrivateKey.generate().public_key().public_bytes_raw()}):
        args = {"key_id": "test-key", "public_key": public, "schema_version": "aidp-attestation-v1"}; args.update(kwargs)
        with pytest.raises(ValueError): verify(payload, envelope, **args)

def test_ed25519_malformed_and_replay_rejected():
    private = Ed25519PrivateKey.generate(); raw = private.private_bytes_raw(); public = private.public_key().public_bytes_raw()
    payload = canonical_bytes({"value": 1}); envelope = sign_for_test(payload, key_id="k", private_key=raw, schema_version="aidp-attestation-v1")
    for bad in (b"{}", envelope[:-2], envelope + b"x"):
        with pytest.raises(ValueError): verify(payload, bad, key_id="k", public_key=public, schema_version="aidp-attestation-v1")
    with pytest.raises(ValueError): verify(canonical_bytes({"value": 2}), envelope, key_id="k", public_key=public, schema_version="aidp-attestation-v1")
    value = json.loads(envelope); value["algorithm"] = "RSA"
    with pytest.raises(ValueError): verify(payload, json.dumps(value).encode(), key_id="k", public_key=public, schema_version="aidp-attestation-v1")
