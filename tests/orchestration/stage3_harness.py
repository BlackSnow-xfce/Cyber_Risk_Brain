import base64, hashlib, json
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from aidp_orchestration.attestations import ATTESTATION_SCHEMA, CATEGORIES, EXTRA, AttestationBundleVerifier
from aidp_orchestration.ed25519 import AIDPSignatureV1, _signed_bytes
from aidp_orchestration.foundation import canonical_bytes
from aidp_orchestration.foundation import DurableCAS
from aidp_orchestration.trust_policy import POLICY_SCHEMA
from aidp_orchestration.stage3ra import Stage3RAVerifier, DecisionNonceReplayStore

class _HarnessStage3RAVerifier(Stage3RAVerifier):
    def verify(self, *args, **kwargs):
        return {"status": "VERIFIED_3RA"}

class _Allow:
    def verify_recovery_decision(self, value): return True
    def verify_source_authority(self, value): return True

@dataclass
class Stage3TestTrustHarness:
    root: Path
    policies: dict
    requests: dict
    keys: dict
    public_keys: dict
    lineage: dict
    now: str = "2026-09-11T12:00:00.000000Z"

    @classmethod
    def create(cls, root: Path):
        keys={}; public={}; policies={}; requests={}
        for category in sorted(CATEGORIES):
            name=category.replace("-", "-")+"-test"; key_id=name+"-key"; key=Ed25519PrivateKey.generate()
            keys[category]=key; public[key_id]=key.public_key().public_bytes_raw()
            requests[category]={"source_identity":name,"category":category,"schema":"aidp-source-attestation-v1","environment":"test","endpoint_identity":name+"-endpoint","audience":"aidp-recovery-test","key_namespace":name+"-namespace","key_id":key_id,"algorithm":"Ed25519","trust_store_id":"stage3-test-store","minimum_epoch":1,"payload_schema":"payload-v1"}
            policies[category]=type("Policy",(),{"payload":{"schema_version":POLICY_SCHEMA,"domain":"aidp-source-authorization","environment":"test","rows":[requests[category]],"issued_at":"2026-09-11T12:00:00.000000Z","valid_until":"2026-09-11T13:00:00.000000Z"}})()
        lineage={"dependency_id":"dep-test","parent_task_id":"parent-test","predecessor_authority_id":"pred-test","predecessor_claim_digest":"claim-test","predecessor_execution_id":"exec-test","proposal_digest":"proposal-test","selected_source_authority_id":"source-test"}
        harness=cls(root,policies,requests,keys,public,lineage)
        root.mkdir(parents=True, exist_ok=True)
        trust=DurableCAS(root/"trust.cas")
        policy=DurableCAS(root/"policy.cas")
        if trust.read() is None: trust.compare_and_swap(expected_version=None, expected_digest=None, payload={"trust_store_id":"stage3-test-store","monotonic_epoch":1,"revocation_epoch":1,"checkpoint_digest":"test-checkpoint"})
        if policy.read() is None: policy.compare_and_swap(expected_version=None, expected_digest=None, payload={"policy_id":"stage3-test-policy","policy_epoch":1,"policy_digest":"test-policy"})
        return harness

    def build(self, category):
        req=self.requests[category]; payload={"schema_version":ATTESTATION_SCHEMA,"domain":"aidp-source-attestation","source_category":category,**{k:v for k,v in req.items() if k not in {"category","schema","minimum_epoch"}},"trust_store_epoch":1,"observation_sequence":1,"issued_at":self.now,"valid_until":"2026-09-11T13:00:00.000000Z",**{k:v for k,v in self.lineage.items() if k != "selected_source_authority_id"},"payload_digest":"placeholder"}
        for field in EXTRA[category]: payload[field] = "valid"
        if category == "product-owner-recovery-decision": payload.update(principal="po-test", operation="RECOVER_GATE_DEPENDENCY", approval_context_id="ctx", approval_context_digest="a"*64, decision_id="decision", nonce="nonce", selected_source_authority_id="source-test", selected_source_digest="b"*64)
        if category == "execution-evidence": payload.update(attempt_count="1", result_count="1", execution_outcome="FAILED", heartbeat_continuity="true", execution_store_manifest_digest="c"*64)
        if category == "process-lineage": payload.update(completeness_result="true", topology_snapshot_digest="d"*64)
        if category == "workspace-ref": payload.update(residual_state_assessment="clean", workspace_identities="workspace", refs_worktrees_detached_heads="refs", tracked_state="clean", untracked_state="clean", repository_workspace_manifest_digest="e"*64)
        if category == "repository-advancement": payload.update(repository_identity="repo", git_common_identity="common", remote_identity="remote", branch="branch", original_head="a"*40, approved_current_head="b"*40, ancestry_result="true", repository_snapshot_digest="f"*64)
        if category == "execution-source-authority": payload.update(selected_source_authority_id="source-test", selected_source_digest="1"*64, authority_terms_digest="2"*64, authority_lifecycle_state="ELIGIBLE")
        if category == "trusted-time": payload.update(trusted_utc_timestamp=self.now, monotonic_time_sequence="1", time_service_identity="time-test", time_validity_interval="valid")
        body=canonical_bytes(payload); payload["payload_digest"]=hashlib.sha256(body).hexdigest(); body=canonical_bytes(payload)
        key=self.keys[category]; sig=key.sign(_signed_bytes(body,"aidp-attestation-v1")); envelope=AIDPSignatureV1("aidp-attestation-v1","Ed25519",req["key_id"],hashlib.sha256(body).hexdigest(),base64.urlsafe_b64encode(sig).decode()).encoded()
        return canonical_bytes({**payload, "signature": json.loads(envelope)}), envelope

    def verify(self):
        trust=DurableCAS(self.root/"trust.cas").read()
        if trust is None: raise ValueError("test trust store unavailable")
        members=[self.build(category) for category in sorted(CATEGORIES)]
        return AttestationBundleVerifier(_HarnessStage3RAVerifier(), decision_source=_Allow(), authority_source=_Allow(), replay_store=DecisionNonceReplayStore(self.root), trusted_now=self.now).verify([body for body,_ in members], policies=self.policies, requests=self.requests, environment="test", audience="aidp-recovery-test", endpoint_identities={c:self.requests[c]["endpoint_identity"] for c in CATEGORIES}, trust_store=trust["payload"], revoked_key_ids=set(), public_keys=self.public_keys, payload_schema="payload-v1", now=self.now)
