import pytest
from aidp_orchestration.attestations import ATTESTATION_SCHEMA, CATEGORIES, EXTRA, SourceAttestation, AttestationBundleVerifier
from aidp_orchestration.foundation import canonical_bytes, foundation_status
from aidp_orchestration.stage3ra import Stage3RAVerifier

COMMON = {"schema_version": ATTESTATION_SCHEMA, "domain":"aidp-source-attestation", "source_identity":"src", "environment":"test", "endpoint_identity":"ep", "audience":"aud", "key_namespace":"ns", "key_id":"kid", "algorithm":"Ed25519", "trust_store_id":"ts", "trust_store_epoch":1, "observation_sequence":1, "issued_at":"2026-09-11T12:00:00.000000Z", "valid_until":"2026-09-11T13:00:00.000000Z", "dependency_id":"dep", "parent_task_id":"parent", "predecessor_authority_id":"pred", "predecessor_claim_digest":"claim", "predecessor_execution_id":"exec", "proposal_digest":"proposal", "payload_schema":"payload-v1", "payload_digest":"digest"}

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

def test_bundle_po_source_requires_stage3ra_verifier(tmp_path):
    from stage3_harness import Stage3TestTrustHarness
    h=Stage3TestTrustHarness.create(tmp_path)
    members=[h.build(c)[0] for c in sorted(CATEGORIES)]
    with pytest.raises(ValueError, match="STAGE3RA_VERIFIER_UNAVAILABLE"):
        AttestationBundleVerifier().verify(members, policies=h.policies, requests=h.requests, environment="test", audience="aidp-recovery-test", endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES}, trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1}, revoked_key_ids=set(), public_keys=h.public_keys, payload_schema="payload-v1", now=h.now)

def test_bundle_verifier_accepts_stage3ra_dependency_slot():
    sentinel=object()
    assert AttestationBundleVerifier(stage3ra_verifier=sentinel)._stage3ra_verifier is sentinel

def _integrated_args(h, members):
    from stage3_harness import _Allow
    from aidp_orchestration.stage3ra import DecisionNonceReplayStore
    return dict(attestations=members, policies=h.policies, requests=h.requests,
        environment="test", audience="aidp-recovery-test",
        endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES},
        trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1},
        revoked_key_ids=set(), public_keys=h.public_keys, payload_schema="payload-v1",
        now=h.now, decision_source=_Allow(), authority_source=_Allow(),
        replay_store=DecisionNonceReplayStore(h.root), trusted_now=h.now)

class _DenyDecision:
    def verify_recovery_decision(self, value): return False
class _DenyAuthority:
    def verify_source_authority(self, value): return False
class _DenyVerifier:
    def verify(self, *args, **kwargs): raise ValueError("3RA_DENIED")

def _run(verifier, args):
    deps={k:args[k] for k in ("decision_source","authority_source","replay_store","trusted_now")}
    call={k:args[k] for k in ("attestations","policies","requests","environment","audience","endpoint_identities","trust_store","revoked_key_ids","public_keys","payload_schema","now")}
    return AttestationBundleVerifier(verifier, **deps).verify(**call)

def test_step1b_missing_mandatory_dependencies_deny(tmp_path):
    from stage3_harness import Stage3TestTrustHarness
    h=Stage3TestTrustHarness.create(tmp_path); members=[h.build(c)[0] for c in sorted(CATEGORIES)]
    for name in ("decision_source", "authority_source", "replay_store", "trusted_now"):
        args=_integrated_args(h, members); args[name]=None
        with pytest.raises(ValueError, match="3RA_DEPENDENCY_UNAVAILABLE"):
            _run(_DenyVerifier(), args)

def test_step1b_authoritative_lookup_and_verifier_denials(tmp_path):
    from stage3_harness import Stage3TestTrustHarness
    h=Stage3TestTrustHarness.create(tmp_path); members=[h.build(c)[0] for c in sorted(CATEGORIES)]
    args=_integrated_args(h, members); args["decision_source"]=_DenyDecision()
    with pytest.raises(ValueError): _run(Stage3RAVerifier(), args)
    args=_integrated_args(h, members); args["authority_source"]=_DenyAuthority()
    with pytest.raises(ValueError): _run(Stage3RAVerifier(), args)
    args=_integrated_args(h, members)
    with pytest.raises(ValueError, match="3RA_DENIED"): _run(_DenyVerifier(), args)
