import pytest
from aidp_orchestration.stage3ra import ProductOwnerRecoveryDecisionPayloadV1, ExecutionSourceAuthorityPayloadV1, DecisionNonceReplayStore, Stage3RAVerifier
from aidp_orchestration.foundation import canonical_bytes
from copy import deepcopy

def po():
    return {"schema_version":"aidp-product-owner-recovery-decision-v1","domain":"aidp-product-owner-recovery-decision","authenticated_principal_ref":"po","permission":"RECOVER_GATE_DEPENDENCY","approval_context_ref":"ctx","approval_context_digest":"a"*64,"decision_id":"decision","nonce":"nonce","proposal_digest":"b"*64,"predecessor_authority_id":"pred","predecessor_claim_digest":"c"*64,"predecessor_execution_id":"exec","dependency_id":"dep","parent_task_id":"parent","selected_source_authority_id":"source","selected_source_digest":"d"*64,"issued_at":"2026-09-11T12:00:00.000000Z","valid_until":"2026-09-11T13:00:00.000000Z"}
def test_typed_po_and_replay(tmp_path):
    ProductOwnerRecoveryDecisionPayloadV1.parse(canonical_bytes(po()))
    s=DecisionNonceReplayStore(tmp_path); rid=s.reserve("decision","nonce"); s.consume("decision","nonce",rid)
    with pytest.raises(ValueError): s.consume("decision","nonce")

def test_po_rejects_accept():
    v=po(); v["permission"]="ACCEPT"
    with pytest.raises(ValueError): ProductOwnerRecoveryDecisionPayloadV1.parse(canonical_bytes(v))

def test_integrated_verifier_requires_all_dependencies(tmp_path):
    with pytest.raises(ValueError, match="3RA_DEPENDENCY_UNAVAILABLE"):
        Stage3RAVerifier().verify(canonical_bytes(po()), canonical_bytes({}), decision_source=None, authority_source=None, replay_store=None, trusted_now=None)

def test_po_authoritative_field_matrix(tmp_path):
    base=po()
    class Decision:
        def verify_recovery_decision(self, value): return value == base
    class Source:
        def verify_source_authority(self, value): return True
    for field in ("authenticated_principal_ref","permission","approval_context_ref","approval_context_digest","decision_id","nonce","proposal_digest","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","dependency_id","parent_task_id","selected_source_authority_id","selected_source_digest","issued_at","valid_until"):
        mutated=deepcopy(base); mutated[field] = "X" if field not in {"permission"} else "ACCEPT"
        with pytest.raises(ValueError):
            Stage3RAVerifier().verify(canonical_bytes(mutated), canonical_bytes({}), decision_source=Decision(), authority_source=Source(), replay_store=DecisionNonceReplayStore(tmp_path / field), trusted_now="2026-09-11T12:30:00.000000Z")

def test_source_lifecycle_matrix():
    value={"schema_version":"aidp-execution-source-authority-v1","domain":"aidp-execution-source-authority","authority_id":"a","authority_digest":"a"*64,"terms_digest":"b"*64,"lifecycle":"ELIGIBLE","proposal_digest":"c"*64,"po_decision_id":"d","po_decision_digest":"e"*64,"selected_source_authority_id":"a","selected_source_digest":"f"*64}
    for lifecycle in ("EXPIRED","REVOKED","TERMINAL","BLOCKED","UNKNOWN"):
        mutated={**value,"lifecycle":lifecycle}
        with pytest.raises(ValueError): ExecutionSourceAuthorityPayloadV1.parse(canonical_bytes(mutated))
