import json
import pytest
from aidp_orchestration.attestations import CATEGORIES, AttestationBundleVerifier
from stage3_harness import Stage3TestTrustHarness

def setup(tmp_path):
    h=Stage3TestTrustHarness.create(tmp_path); return h,[h.build(c)[0] for c in sorted(CATEGORIES)]
def verify(h,m):
    return AttestationBundleVerifier().verify(m,policies=h.policies,requests=h.requests,environment="test",audience="aidp-recovery-test",endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES},trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1},revoked_key_ids=set(),public_keys=h.public_keys,payload_schema="payload-v1",now=h.now)
@pytest.mark.parametrize("field,value",[("selected_source_digest","bad"),("authority_terms_digest","bad"),("authority_lifecycle_state","EXPIRED"),("authority_lifecycle_state","REVOKED"),("authority_lifecycle_state","TERMINAL"),("authority_lifecycle_state","UNKNOWN")])
def test_source_authority_mutations_deny(tmp_path,field,value):
    h,m=setup(tmp_path); i=sorted(CATEGORIES).index("execution-source-authority"); v=json.loads(m[i]); v[field]=value; m[i]=json.dumps(v,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): verify(h,m)
@pytest.mark.parametrize("field,value",[("trusted_utc_timestamp","bad"),("time_service_identity","wrong"),("time_validity_interval","expired"),("monotonic_time_sequence","0"),("trust_store_epoch",2)])
def test_trusted_time_mutations_deny(tmp_path,field,value):
    h,m=setup(tmp_path); i=sorted(CATEGORIES).index("trusted-time"); v=json.loads(m[i]); v[field]=value; m[i]=json.dumps(v,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): verify(h,m)
def test_c2_positive_and_replay_substitution_denies(tmp_path):
    h,m=setup(tmp_path); assert verify(h,m)[0].categories==tuple(sorted(CATEGORIES))
    i=sorted(CATEGORIES).index("trusted-time"); m[i]=m[sorted(CATEGORIES).index("execution-source-authority")]
    with pytest.raises(ValueError): verify(h,m)
