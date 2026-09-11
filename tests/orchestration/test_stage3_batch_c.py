import json
import pytest
from aidp_orchestration.attestations import CATEGORIES, AttestationBundleVerifier
from stage3_harness import Stage3TestTrustHarness

CAT=["workspace-ref","repository-advancement","execution-source-authority","trusted-time"]
def setup_bundle(tmp_path):
    h=Stage3TestTrustHarness.create(tmp_path); return h,[h.build(c)[0] for c in sorted(CATEGORIES)]
def verify(h,members):
    return AttestationBundleVerifier().verify(members, policies=h.policies, requests=h.requests, environment="test", audience="aidp-recovery-test", endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES}, trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1}, revoked_key_ids=set(), public_keys=h.public_keys, payload_schema="payload-v1", now=h.now)
@pytest.mark.parametrize("category",CAT)
def test_batch_c_positive_categories_remain_in_bundle(tmp_path,category):
    h,m=setup_bundle(tmp_path); assert verify(h,m)[0].categories==tuple(sorted(CATEGORIES))
@pytest.mark.parametrize("category",CAT)
@pytest.mark.parametrize("field",["dependency_id","parent_task_id","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","proposal_digest"])
def test_batch_c_common_binding_mutation_denies(tmp_path,category,field):
    h,m=setup_bundle(tmp_path); i=sorted(CATEGORIES).index(category); v=json.loads(m[i]); v[field]="changed"; m[i]=json.dumps(v,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): verify(h,m)
@pytest.mark.parametrize("category",CAT)
def test_batch_c_independent_member_mutation_denies(tmp_path,category):
    h,m=setup_bundle(tmp_path); i=sorted(CATEGORIES).index(category); v=json.loads(m[i]); v["source_identity"]="wrong"; m[i]=json.dumps(v,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): verify(h,m)
