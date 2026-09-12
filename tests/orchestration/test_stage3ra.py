import pytest
from aidp_orchestration.stage3ra import ProductOwnerRecoveryDecisionPayloadV1, ExecutionSourceAuthorityPayloadV1, DecisionNonceReplayStore
from aidp_orchestration.foundation import canonical_bytes

def po():
    return {"schema_version":"aidp-product-owner-recovery-decision-v1","domain":"aidp-product-owner-recovery-decision","authenticated_principal_ref":"po","permission":"RECOVER_GATE_DEPENDENCY","approval_context_ref":"ctx","approval_context_digest":"a"*64,"decision_id":"decision","nonce":"nonce","proposal_digest":"b"*64,"predecessor_authority_id":"pred","predecessor_claim_digest":"c"*64,"predecessor_execution_id":"exec","dependency_id":"dep","parent_task_id":"parent","selected_source_authority_id":"source","selected_source_digest":"d"*64,"issued_at":"2026-09-11T12:00:00.000000Z","valid_until":"2026-09-11T13:00:00.000000Z"}
def test_typed_po_and_replay(tmp_path):
    ProductOwnerRecoveryDecisionPayloadV1.parse(canonical_bytes(po()))
    s=DecisionNonceReplayStore(tmp_path); s.consume("decision","nonce")
    with pytest.raises(ValueError): s.consume("decision","nonce")

def test_po_rejects_accept():
    v=po(); v["permission"]="ACCEPT"
    with pytest.raises(ValueError): ProductOwnerRecoveryDecisionPayloadV1.parse(canonical_bytes(v))
