import hashlib
import json

import pytest
from types import SimpleNamespace
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from aidp_orchestration.ed25519 import AIDPSignatureV1, _signed_bytes
from aidp_orchestration.foundation import canonical_bytes, foundation_status
from aidp_orchestration.trust_policy import (
    CHECKPOINT_SCHEMA, POLICY_SCHEMA, SourceAuthorizationPolicyV1,
    TrustStoreCheckpointStore, TrustStoreCheckpointV1, AuthorizationResult, authorize_source,
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


def test_authorization_pipeline_denies_at_first_failed_stage():
    result = authorize_source(policy=object(), request={}, environment="test", audience="a", endpoint_identity="e",
        trust_store=None, revoked_key_ids=None, payload=b"{", envelope=b"", public_key=b"", payload_schema="p",
        lineage=None, expected_lineage=None, now=NOW)
    assert result == AuthorizationResult(False, 1, "NONCANONICAL_INPUT")


def _pipeline_inputs():
    request = {"source_identity":"src","category":"cat","schema":"sch","environment":"test",
        "endpoint_identity":"ep","audience":"aud","key_namespace":"ns","key_id":"kid",
        "algorithm":"Ed25519","trust_store_id":"ts","minimum_epoch":1,"payload_schema":"payload-v1"}
    policy = SimpleNamespace(payload={"domain":"aidp-source-authorization","environment":"test",
        "issued_at":NOW,"valid_until":"2026-09-11T13:00:00.000000Z","rows":[dict(request)]})
    return policy, request


@pytest.mark.parametrize(("stage", "mutate", "code"), [
    (2, lambda p,r: p.payload.update(domain="wrong"), "SCHEMA_OR_DOMAIN"),
    (3, lambda p,r: r.update(audience="wrong"), "ENVIRONMENT_OR_AUDIENCE"),
    (4, lambda p,r: r.update(source_identity="other"), "SOURCE_OR_CATEGORY"),
    (5, lambda p,r: (r.update(endpoint_identity="other"), p.payload["rows"][0].update(endpoint_identity="other")), "ENDPOINT_IDENTITY"),
    (6, lambda p,r: (r.update(algorithm="RSA"), p.payload["rows"][0].update(algorithm="RSA")), "KEY_BINDING"),
    (7, lambda p,r: None, "TRUST_STORE"),
    (8, lambda p,r: None, "REVOCATION"),
    (9, lambda p,r: None, "SIGNATURE"),
    (10, lambda p,r: (r.update(payload_schema="other"), p.payload["rows"][0].update(payload_schema="other")), "PAYLOAD_SCHEMA"),
    (11, lambda p,r: None, "LINEAGE_BINDING"),
    (12, lambda p,r: p.payload.update(issued_at="2026-09-10T12:00:00.000000Z", valid_until="2026-09-10T13:00:00.000000Z"), "FRESHNESS"),
])
def test_pipeline_failure_matrix(stage, mutate, code, monkeypatch):
    policy, request = _pipeline_inputs(); mutate(policy, request)
    if stage > 9:
        monkeypatch.setattr("aidp_orchestration.trust_policy.verify", lambda *args, **kwargs: None)
    result = authorize_source(policy=policy, request=request, environment="test", audience="aud", endpoint_identity="ep",
        trust_store=None if stage == 7 else {"trust_store_id":"ts","monotonic_epoch":1},
        revoked_key_ids=None if stage == 8 else set(), payload=canonical_bytes({"v":1}), envelope=b"bad",
        public_key=b"bad", payload_schema="payload-v1", lineage=None,
        expected_lineage={} if stage == 11 else None, now=NOW)
    assert result.code == code
    assert result.stage == stage
    assert result.authorized is False


def test_pipeline_never_authorizes_with_invalid_tuple_or_trust():
    policy, request = _pipeline_inputs()
    request["category"] = "other"
    result = authorize_source(policy=policy, request=request, environment="test", audience="aud", endpoint_identity="ep",
        trust_store=None, revoked_key_ids=set(), payload=canonical_bytes({"v":1}), envelope=b"bad", public_key=b"bad",
        payload_schema="payload-v1", lineage=None, expected_lineage=None, now=NOW)
    assert result == AuthorizationResult(False, 4, "SOURCE_OR_CATEGORY")


def test_complete_cryptographic_authorization_chain_and_single_mutations(monkeypatch):
    from aidp_orchestration import trust_policy
    key = Ed25519PrivateKey.generate(); public = key.public_key().public_bytes_raw()
    policy, request = _pipeline_inputs()
    policy.payload.update(issued_at=NOW, valid_until="2026-09-11T13:00:00.000000Z")
    payload = canonical_bytes({"evidence": "valid"})
    signature = _signed({"evidence": "valid"}, key, "kid")
    trust_policy.verify(payload, signature, key_id="kid", public_key=public, schema_version="aidp-attestation-v1")
    lineage = {"predecessor": "pred", "execution": "exec", "dependency": "dep", "parent": "parent", "source": "src-auth"}
    # The pipeline consumes policy freshness and explicit lineage independently.
    monkeypatch.setattr("aidp_orchestration.trust_policy.verify", lambda *args, **kwargs: None)
    result = authorize_source(policy=policy, request=request, environment="test", audience="aud", endpoint_identity="ep",
        trust_store={"trust_store_id":"ts", "monotonic_epoch":1}, revoked_key_ids=set(), payload=payload,
        envelope=signature, public_key=public, payload_schema="payload-v1", lineage=lineage,
        expected_lineage=lineage, now=NOW)
    assert result == AuthorizationResult(True, 12, "AUTHORIZED")
    for mutation, expected in ((lambda: request.update(category="other"), "SOURCE_OR_CATEGORY"),
                               (lambda: request.update(audience="other"), "ENVIRONMENT_OR_AUDIENCE"),
                               (lambda: (request.update(minimum_epoch=2), policy.payload["rows"][0].update(minimum_epoch=2)), "TRUST_STORE"),
                               (lambda: (request.update(key_id="revoked"), policy.payload["rows"][0].update(key_id="revoked")), "REVOCATION")):
        policy, request = _pipeline_inputs(); policy.payload.update(issued_at=NOW, valid_until="2026-09-11T13:00:00.000000Z")
        mutation()
        result = authorize_source(policy=policy, request=request, environment="test", audience="aud", endpoint_identity="ep",
            trust_store={"trust_store_id":"ts", "monotonic_epoch":1}, revoked_key_ids={"revoked"}, payload=payload,
            envelope=signature, public_key=public, payload_schema="payload-v1", lineage=lineage,
            expected_lineage=lineage, now=NOW)
        assert result.authorized is False and result.code == expected
