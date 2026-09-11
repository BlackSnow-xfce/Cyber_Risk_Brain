import json
import pytest
from aidp_orchestration.attestations import CATEGORIES, AttestationBundleVerifier
from aidp_orchestration.foundation import canonical_bytes
from stage3_harness import Stage3TestTrustHarness

def _bundle(tmp_path):
    h=Stage3TestTrustHarness.create(tmp_path); members=[h.build(c)[0] for c in sorted(CATEGORIES)]
    return h,members

def _verify(h,members):
    return AttestationBundleVerifier().verify(members, policies=h.policies, requests=h.requests, environment="test", audience="aidp-recovery-test", endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES}, trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1}, revoked_key_ids=set(), public_keys=h.public_keys, payload_schema="payload-v1", now=h.now)

@pytest.mark.parametrize("field", ["dependency_id","parent_task_id","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","proposal_digest"])
def test_lineage_mutation_denies(tmp_path,field):
    h,members=_bundle(tmp_path); value=json.loads(members[0]); value[field]="mutated"; members[0]=canonical_bytes(value)
    with pytest.raises(ValueError): _verify(h,members)
    assert _verify(h,[h.build(c)[0] for c in sorted(CATEGORIES)])[0].proposal_digest=="proposal-test"

def test_bundle_attack_matrix(tmp_path):
    h,members=_bundle(tmp_path); assert _verify(h,members)[0].categories==tuple(sorted(CATEGORIES))
    for i in range(len(members)):
        with pytest.raises(ValueError): _verify(h,members[:i]+members[i+1:])
        with pytest.raises(ValueError): _verify(h,members[:i]+[members[i],members[i]]+members[i+1:])
    with pytest.raises(ValueError): _verify(h,members+[members[0]])
    assert _verify(h,list(reversed(members)))[0].categories==tuple(sorted(CATEGORIES))
    fabricated=canonical_bytes({"source_category":"unknown"})
    with pytest.raises(ValueError): _verify(h,members+[fabricated])

def test_manifest_mutations_change_identity(tmp_path):
    h,members=_bundle(tmp_path); manifest,_=_verify(h,members); original=manifest.digest
    mutations=[manifest.__class__(tuple(reversed(manifest.categories)),manifest.attestation_digests,manifest.common_lineage_digest,manifest.proposal_digest,manifest.trust_store_epoch,manifest.policy_epoch,manifest.issued_at,manifest.valid_until),
      manifest.__class__(manifest.categories,{**manifest.attestation_digests,"trusted-time":"0"*64},manifest.common_lineage_digest,manifest.proposal_digest,manifest.trust_store_epoch,manifest.policy_epoch,manifest.issued_at,manifest.valid_until),
      manifest.__class__(manifest.categories,manifest.attestation_digests,"other",manifest.proposal_digest,manifest.trust_store_epoch,manifest.policy_epoch,manifest.issued_at,manifest.valid_until)]
    assert all(item.digest!=original for item in mutations)
