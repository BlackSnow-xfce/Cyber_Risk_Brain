import json
import pytest
from aidp_orchestration.attestations import CATEGORIES, AttestationBundleVerifier
from stage3_harness import Stage3TestTrustHarness

def _setup(tmp_path):
    h=Stage3TestTrustHarness.create(tmp_path); members=[h.build(c)[0] for c in sorted(CATEGORIES)]
    return h,members
def _verify(h,members):
    return AttestationBundleVerifier().verify(members, policies=h.policies, requests=h.requests, environment="test", audience="aidp-recovery-test", endpoint_identities={c:h.requests[c]["endpoint_identity"] for c in CATEGORIES}, trust_store={"trust_store_id":"stage3-test-store","monotonic_epoch":1}, revoked_key_ids=set(), public_keys=h.public_keys, payload_schema="payload-v1", now=h.now)
def _mutate(members, category, field, value):
    idx=sorted(CATEGORIES).index(category); obj=json.loads(members[idx]); obj[field]=value; members[idx]=json.dumps(obj,separators=(",",":"),sort_keys=True).encode()

@pytest.mark.parametrize("field,value", [("operation","ACCEPT"),("operation","REWORK"),("principal",""),("approval_context_id",""),("approval_context_digest","bad"),("decision_id",""),("nonce",""),("selected_source_digest","bad")])
def test_po_semantic_denials(tmp_path,field,value):
    h,members=_setup(tmp_path); _mutate(members,"product-owner-recovery-decision",field,value)
    with pytest.raises(ValueError): _verify(h,members)

@pytest.mark.parametrize("field,value", [("attempt_identity",""),("attempt_count","0"),("attempt_count","2"),("result_identity",""),("result_count","0"),("heartbeat_continuity","false"),("execution_outcome","UNKNOWN"),("execution_outcome","SUCCESS"),("execution_store_manifest_digest","bad"),("supervisor_ledger_identity","")])
def test_execution_semantic_denials(tmp_path,field,value):
    h,members=_setup(tmp_path); _mutate(members,"execution-evidence",field,value)
    with pytest.raises(ValueError): _verify(h,members)

@pytest.mark.parametrize("field,value", [("completeness_result","false"),("topology_snapshot_digest","bad"),("host_identity",""),("supervisor_identity",""),("launcher_identity",""),("descendants",""),("job_process_groups",""),("containers",""),("remote_executors","")])
def test_process_semantic_denials(tmp_path,field,value):
    h,members=_setup(tmp_path); _mutate(members,"process-lineage",field,value)
    with pytest.raises(ValueError): _verify(h,members)

def test_batch_b_positive_control(tmp_path):
    h,members=_setup(tmp_path)
    assert _verify(h,members)[0].categories == tuple(sorted(CATEGORIES))

@pytest.mark.parametrize("category", ["product-owner-recovery-decision", "execution-evidence", "process-lineage"])
def test_each_batch_b_category_positive(tmp_path, category):
    h,members=_setup(tmp_path)
    assert _verify(h,members)[0].categories == tuple(sorted(CATEGORIES))

@pytest.mark.parametrize("category", ["product-owner-recovery-decision", "execution-evidence", "process-lineage"])
@pytest.mark.parametrize("field", ["dependency_id","parent_task_id","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","proposal_digest"])
def test_cross_member_binding_mutation_denies(tmp_path, category, field):
    h,members=_setup(tmp_path); idx=sorted(CATEGORIES).index(category); obj=json.loads(members[idx]); obj[field]="cross-member-mismatch"; members[idx]=json.dumps(obj,separators=(",",":"),sort_keys=True).encode()
    with pytest.raises(ValueError): _verify(h,members)
