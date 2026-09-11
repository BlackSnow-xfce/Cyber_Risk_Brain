import json
import pytest
from aidp_orchestration.attestations import CATEGORIES, AttestationBundleVerifier
from stage3_harness import Stage3TestTrustHarness

WS_FIELDS=["residual_state_assessment","workspace_identities","refs_worktrees_detached_heads","tracked_state","untracked_state","repository_workspace_manifest_digest"]
REPO_FIELDS=["repository_identity","git_common_identity","remote_identity","branch","original_head","approved_current_head","ancestry_result","repository_snapshot_digest"]
def setup(tmp_path):
    h=Stage3TestTrustHarness.create(tmp_path); return h,[h.build(c)[0] for c in sorted(CATEGORIES)]
def verify(h,m):
    return AttestationBundleVerifier().verify(m,policies=h.policies,requests=h.requests,environment="test",audience="aidp-recovery-test",endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES},trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1},revoked_key_ids=set(),public_keys=h.public_keys,payload_schema="payload-v1",now=h.now)
@pytest.mark.parametrize("field",WS_FIELDS)
def test_workspace_ref_mutations_deny(tmp_path,field):
    h,m=setup(tmp_path); i=sorted(CATEGORIES).index("workspace-ref"); v=json.loads(m[i]); v[field]="mutated"; m[i]=json.dumps(v,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): verify(h,m)
@pytest.mark.parametrize("field",REPO_FIELDS)
def test_repository_mutations_deny(tmp_path,field):
    h,m=setup(tmp_path); i=sorted(CATEGORIES).index("repository-advancement"); v=json.loads(m[i]); v[field]="false" if field=="ancestry_result" else "mutated"; m[i]=json.dumps(v,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): verify(h,m)
def test_c1_positive_control(tmp_path):
    h,m=setup(tmp_path); assert verify(h,m)[0].categories==tuple(sorted(CATEGORIES))
