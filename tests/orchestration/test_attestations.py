import pytest
from aidp_orchestration.attestations import ATTESTATION_SCHEMA, CATEGORIES, EXTRA, SourceAttestation, AttestationBundleVerifier
from aidp_orchestration.foundation import canonical_bytes, foundation_status

COMMON = {"schema_version": ATTESTATION_SCHEMA, "domain":"aidp-source-attestation", "source_identity":"src", "environment":"test", "endpoint_identity":"ep", "audience":"aud", "key_namespace":"ns", "key_id":"kid", "trust_store_id":"ts", "trust_store_epoch":1, "observation_sequence":1, "issued_at":"2026-09-11T12:00:00.000000Z", "valid_until":"2026-09-11T13:00:00.000000Z", "dependency_id":"dep", "parent_task_id":"parent", "predecessor_authority_id":"pred", "predecessor_claim_digest":"claim", "predecessor_execution_id":"exec", "proposal_digest":"proposal", "payload_schema":"payload-v1", "payload_digest":"digest"}

def _raw(category):
    value = {**COMMON, "source_category":category}
    for field in EXTRA[category]: value[field] = "value"
    value["signature"] = {"algorithm":"Ed25519","key_id":"kid","payload_digest":"0"*64,"schema_version":"aidp-attestation-v1","signature":"A"*88}
    return canonical_bytes(value)

@pytest.mark.parametrize("category", sorted(CATEGORIES))
def test_all_closed_attestation_categories_parse(category):
    assert SourceAttestation.parse(_raw(category)).category == category

@pytest.mark.parametrize("category", sorted(CATEGORIES))
def test_category_schema_rejects_wrong_category(category):
    value = _raw(category).replace(category.encode(), b"unknown-category", 1)
    with pytest.raises(ValueError):
        SourceAttestation.parse(value)

def test_attestation_rejects_noncanonical_and_unknown_fields():
    with pytest.raises(ValueError): SourceAttestation.parse(_raw("trusted-time") + b"\n")

def test_bundle_requires_exact_category_set_and_readiness_stays_blocked():
    verifier = AttestationBundleVerifier()
    with pytest.raises(ValueError):
        verifier.verify([_raw("trusted-time")], policies={}, requests={}, environment="test", audience="aud", endpoint_identities={}, trust_store={}, revoked_key_ids=set(), public_keys={}, payload_schema="payload-v1", now="2026-09-11T12:00:00.000000Z")
    status = foundation_status()
    assert status["SOURCE_ATTESTATION_SCHEMAS_READY"] == "READY"
    assert status["ATTESTATION_BUNDLE_VERIFIER_READY"] == "READY"
    assert status["SOURCE_ATTESTATION_PROVIDERS_UNCONFIGURED"] == "BLOCKED"
    assert status["PRODUCTION_RECOVERY_BLOCKED"] == "BLOCKED"
