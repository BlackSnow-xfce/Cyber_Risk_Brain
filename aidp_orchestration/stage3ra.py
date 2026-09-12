"""Stage 3R-A typed decision/source bindings and replay state."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from .foundation import DurableCAS, canonical_bytes, parse_canonical_utf8, validate_timestamp

_DIGEST=re.compile(r"^[0-9a-f]{64}$")
PO_FIELDS={"schema_version","domain","authenticated_principal_ref","permission","approval_context_ref","approval_context_digest","decision_id","nonce","proposal_digest","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","dependency_id","parent_task_id","selected_source_authority_id","selected_source_digest","issued_at","valid_until"}
SOURCE_FIELDS={"schema_version","domain","authority_id","authority_digest","terms_digest","lifecycle","proposal_digest","po_decision_id","po_decision_digest","selected_source_authority_id","selected_source_digest"}

def _digest(v):
    if not isinstance(v,str) or not _DIGEST.fullmatch(v): raise ValueError("invalid digest")
def _text(v):
    if not isinstance(v,str) or not v: raise ValueError("empty identity")

@dataclass(frozen=True, slots=True)
class ProductOwnerRecoveryDecisionPayloadV1:
    value: dict[str,Any]
    @classmethod
    def parse(cls, raw: bytes):
        v=parse_canonical_utf8(raw)
        if canonical_bytes(v)!=raw or not isinstance(v,dict) or set(v)!=PO_FIELDS or v.get("schema_version")!="aidp-product-owner-recovery-decision-v1" or v.get("domain")!="aidp-product-owner-recovery-decision": raise ValueError("invalid PO recovery payload")
        for k in ("authenticated_principal_ref","approval_context_ref","decision_id","nonce","predecessor_authority_id","predecessor_execution_id","dependency_id","parent_task_id","selected_source_authority_id"): _text(v[k])
        if v["permission"]!="RECOVER_GATE_DEPENDENCY": raise ValueError("invalid recovery permission")
        for k in ("approval_context_digest","proposal_digest","predecessor_claim_digest","selected_source_digest"): _digest(v[k])
        validate_timestamp(v["issued_at"]); validate_timestamp(v["valid_until"])
        if v["issued_at"]>=v["valid_until"]: raise ValueError("invalid recovery interval")
        return cls(v)

@dataclass(frozen=True, slots=True)
class ExecutionSourceAuthorityPayloadV1:
    value: dict[str,Any]
    @classmethod
    def parse(cls, raw: bytes):
        v=parse_canonical_utf8(raw)
        if canonical_bytes(v)!=raw or not isinstance(v,dict) or set(v)!=SOURCE_FIELDS or v.get("schema_version")!="aidp-execution-source-authority-v1" or v.get("domain")!="aidp-execution-source-authority": raise ValueError("invalid source payload")
        for k in ("authority_id","po_decision_id","selected_source_authority_id"): _text(v[k])
        for k in ("authority_digest","terms_digest","proposal_digest","po_decision_digest","selected_source_digest"): _digest(v[k])
        if v["lifecycle"]!="ELIGIBLE": raise ValueError("source authority is not eligible")
        return cls(v)

class AuthoritativeDecisionSource(Protocol):
    def verify_recovery_decision(self, value: dict[str,Any]) -> bool: ...
class AuthoritativeSourceStore(Protocol):
    def verify_source_authority(self, value: dict[str,Any]) -> bool: ...

class DecisionNonceReplayStore:
    def __init__(self, root: Path): self.decision=DurableCAS(root/"decision.cas"); self.nonce=DurableCAS(root/"nonce.cas")
    def consume(self, decision_id: str, nonce: str) -> None:
        for store,key in ((self.decision,decision_id),(self.nonce,nonce)):
            current=store.read()
            if current is not None and current["payload"].get("value")==key: raise ValueError("replay detected")
            store.compare_and_swap(expected_version=None if current is None else current["version"],expected_digest=None if current is None else current["digest"],payload={"value":key})

def verify_cross_binding(po: dict[str,Any], source: dict[str,Any], decision_source: AuthoritativeDecisionSource, authority_source: AuthoritativeSourceStore) -> None:
    if not decision_source.verify_recovery_decision(po) or not authority_source.verify_source_authority(source): raise ValueError("authoritative evidence unavailable or denied")
    if source["po_decision_id"]!=po["decision_id"] or source["proposal_digest"]!=po["proposal_digest"] or source["selected_source_authority_id"]!=po["selected_source_authority_id"] or source["selected_source_digest"]!=po["selected_source_digest"]: raise ValueError("PO/source binding mismatch")
