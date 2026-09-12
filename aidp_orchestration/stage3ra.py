"""Stage 3R-A typed decision/source bindings and replay state."""
from __future__ import annotations
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from .foundation import DurableCAS, canonical_bytes, parse_canonical_utf8, validate_timestamp
from datetime import datetime

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
    def __init__(self, root: Path): self.store=DurableCAS(root/"decision-nonce-reservation.cas")
    def reserve(self, decision_id: str, nonce: str, *, environment="test", proposal_digest="", predecessor_lineage_digest="", selected_source_authority_id="", created_at="") -> str:
        current=self.store.read()
        if current is not None:
            p=current["payload"]
            if p.get("decision_id")==decision_id and p.get("nonce")==nonce and p.get("state")=="RESERVED": raise ValueError("replay reservation already exists")
            if p.get("decision_id")==decision_id or p.get("nonce")==nonce: raise ValueError("replay detected")
        reservation_id=uuid.uuid4().hex
        self.store.compare_and_swap(expected_version=None if current is None else current["version"],expected_digest=None if current is None else current["digest"],payload={"environment":environment,"decision_id":decision_id,"nonce":nonce,"proposal_digest":proposal_digest,"predecessor_lineage_digest":predecessor_lineage_digest,"selected_source_authority_id":selected_source_authority_id,"reservation_id":reservation_id,"state":"RESERVED","created_at":created_at,"updated_at":created_at})
        return reservation_id
    def consume(self, decision_id: str, nonce: str, reservation_id: str|None=None) -> None:
        current=self.store.read()
        if current is None or current["payload"].get("state")!="RESERVED" or current["payload"].get("decision_id")!=decision_id or current["payload"].get("nonce")!=nonce or (reservation_id is not None and current["payload"].get("reservation_id")!=reservation_id): raise ValueError("replay reservation unavailable")
        payload=dict(current["payload"]); payload["state"]="CONSUMED"
        self.store.compare_and_swap(expected_version=current["version"],expected_digest=current["digest"],payload=payload)

@dataclass(frozen=True, slots=True)
class AuthoritativeDecisionRecord:
    value: dict[str,Any]
@dataclass(frozen=True, slots=True)
class AuthoritativeSourceRecord:
    value: dict[str,Any]

class Stage3RAVerifier:
    def verify(self, po_raw: bytes, source_raw: bytes, *, decision_source: AuthoritativeDecisionSource|None, authority_source: AuthoritativeSourceStore|None, replay_store: DecisionNonceReplayStore|None, trusted_now: str|None) -> dict[str,Any]:
        if not all((decision_source, authority_source, replay_store, trusted_now)): raise ValueError("3RA_DEPENDENCY_UNAVAILABLE")
        po=ProductOwnerRecoveryDecisionPayloadV1.parse(po_raw).value; source=ExecutionSourceAuthorityPayloadV1.parse(source_raw).value
        _ = decision_source.verify_recovery_decision(po); _ = authority_source.verify_source_authority(source)
        if not _ or not decision_source.verify_recovery_decision(po) or not authority_source.verify_source_authority(source): raise ValueError("authoritative evidence denied")
        if source["po_decision_id"]!=po["decision_id"] or source["proposal_digest"]!=po["proposal_digest"] or source["selected_source_authority_id"]!=po["selected_source_authority_id"] or source["selected_source_digest"]!=po["selected_source_digest"]: raise ValueError("cross-binding denied")
        validate_timestamp(trusted_now); now=datetime.strptime(trusted_now,"%Y-%m-%dT%H:%M:%S.%fZ"); issued=datetime.strptime(po["issued_at"],"%Y-%m-%dT%H:%M:%S.%fZ"); valid=datetime.strptime(po["valid_until"],"%Y-%m-%dT%H:%M:%S.%fZ")
        if not issued<=now<=valid: raise ValueError("3RA freshness denied")
        reservation_id=replay_store.reserve(po["decision_id"],po["nonce"], proposal_digest=po["proposal_digest"], created_at=trusted_now)
        replay_store.consume(po["decision_id"],po["nonce"], reservation_id)
        return {"status":"VERIFIED_3RA","decision_id":po["decision_id"],"source_authority_id":source["authority_id"]}

def verify_cross_binding(po: dict[str,Any], source: dict[str,Any], decision_source: AuthoritativeDecisionSource, authority_source: AuthoritativeSourceStore) -> None:
    if not decision_source.verify_recovery_decision(po) or not authority_source.verify_source_authority(source): raise ValueError("authoritative evidence unavailable or denied")
    if source["po_decision_id"]!=po["decision_id"] or source["proposal_digest"]!=po["proposal_digest"] or source["selected_source_authority_id"]!=po["selected_source_authority_id"] or source["selected_source_digest"]!=po["selected_source_digest"]: raise ValueError("PO/source binding mismatch")
