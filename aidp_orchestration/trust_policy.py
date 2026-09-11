"""Strict, non-configuring trust-store and source-policy foundations."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from .ed25519 import verify
from .foundation import DurableCAS, canonical_bytes, canonical_digest, parse_canonical_utf8, validate_timestamp

CHECKPOINT_SCHEMA = "aidp-trust-store-checkpoint-v1"
POLICY_SCHEMA = "aidp-source-authorization-policy-v1"
_SIG={"algorithm","key_id","payload_digest","schema_version","signature"}
_CP={"schema_version","domain","environment","trust_store_id","version","monotonic_epoch","previous_checkpoint_digest","issued_at","valid_until","revocation_epoch","authorized_category_key_mappings","checkpoint_signer","signer_key_id","signature"}
_PP={"schema_version","domain","environment","policy_id","policy_epoch","previous_policy_digest","issued_at","valid_until","rows","signer_key_id","signature"}
_ROW={"source_identity","category","schema","environment","endpoint_identity","audience","key_namespace","key_id","algorithm","trust_store_id","minimum_epoch","payload_schema"}

def _strict(raw: bytes, fields: set[str], schema: str) -> dict[str,Any]:
    value=parse_canonical_utf8(raw)
    if canonical_bytes(value)!=raw or not isinstance(value,dict) or set(value)!=fields or value.get("schema_version")!=schema: raise ValueError("noncanonical or invalid trust object")
    return value
def _text(v: Any):
    if type(v) is not str or not v or v in {"*","any"}: raise ValueError("invalid trust identity")
def _fresh(p: dict[str,Any], now: str):
    validate_timestamp(now); validate_timestamp(p["issued_at"]); validate_timestamp(p["valid_until"])
    a=datetime.strptime(p["issued_at"],"%Y-%m-%dT%H:%M:%S.%fZ"); b=datetime.strptime(p["valid_until"],"%Y-%m-%dT%H:%M:%S.%fZ"); n=datetime.strptime(now,"%Y-%m-%dT%H:%M:%S.%fZ")
    if a>=b or not a<=n<=b: raise ValueError("trust object is stale or invalid")
def _sig(v: Any)->bytes:
    if not isinstance(v,dict) or set(v)!=_SIG: raise ValueError("invalid signature envelope")
    return canonical_bytes(v)

@dataclass(frozen=True,slots=True)
class TrustStoreCheckpointV1:
    payload: dict[str,Any]; signature: bytes
    @classmethod
    def parse(cls,raw:bytes):
        v=_strict(raw,_CP,CHECKPOINT_SCHEMA)
        for k in ("environment","trust_store_id","issued_at","valid_until","checkpoint_signer","signer_key_id"): _text(v[k])
        if type(v["previous_checkpoint_digest"]) is not str: raise ValueError("invalid checkpoint digest")
        for k in ("version","monotonic_epoch","revocation_epoch"):
            if type(v[k]) is not int or v[k]<0: raise ValueError("invalid checkpoint integer")
        if v["domain"]!="aidp-trust-store" or not isinstance(v["authorized_category_key_mappings"],list): raise ValueError("invalid checkpoint schema")
        seen=set()
        for r in v["authorized_category_key_mappings"]:
            if not isinstance(r,dict) or set(r)!={"category","key_namespace","key_id","algorithm"}: raise ValueError("invalid checkpoint mapping")
            for x in r.values(): _text(x)
            ident=tuple(r[x] for x in ("category","key_namespace","key_id"))
            if ident in seen: raise ValueError("duplicate checkpoint mapping")
            seen.add(ident)
        return cls({k:x for k,x in v.items() if k!="signature"},_sig(v["signature"]))
    def verify(self,*,public_key:bytes,environment:str,trust_store_id:str,now:str,previous_digest:str|None,highest_epoch:int,highest_revocation_epoch:int):
        if self.payload["environment"]!=environment or self.payload["trust_store_id"]!=trust_store_id: raise ValueError("checkpoint binding mismatch")
        _fresh(self.payload,now)
        if self.payload["monotonic_epoch"]<=highest_epoch or self.payload["revocation_epoch"]<highest_revocation_epoch: raise ValueError("checkpoint rollback")
        if self.payload["previous_checkpoint_digest"]!=(previous_digest or ""): raise ValueError("checkpoint chain mismatch")
        verify(canonical_bytes(self.payload),self.signature,key_id=self.payload["signer_key_id"],public_key=public_key,schema_version="aidp-attestation-v1")

class TrustStoreCheckpointStore:
    def __init__(self,path:Path): self._cas=DurableCAS(path)
    def highest(self): return self._cas.read()
    def accept(self,checkpoint:TrustStoreCheckpointV1,*,environment:str,trust_store_id:str,public_key:bytes,now:str,previous_digest: str | None = None):
        c=self._cas.read(); p=None if c is None else c["payload"]
        checkpoint.verify(public_key=public_key,environment=environment,trust_store_id=trust_store_id,now=now,previous_digest=None if p is None else p["checkpoint_digest"],highest_epoch=-1 if p is None else p["monotonic_epoch"],highest_revocation_epoch=-1 if p is None else p["revocation_epoch"])
        return self._cas.compare_and_swap(expected_version=None if c is None else c["version"],expected_digest=None if c is None else c["digest"],payload={"environment":environment,"trust_store_id":trust_store_id,"monotonic_epoch":checkpoint.payload["monotonic_epoch"],"revocation_epoch":checkpoint.payload["revocation_epoch"],"checkpoint_digest":canonical_digest(checkpoint.payload)})

@dataclass(frozen=True,slots=True)
class SourceAuthorizationPolicyV1:
    payload: dict[str,Any]; signature: bytes
    @classmethod
    def parse(cls,raw:bytes):
        v=_strict(raw,_PP,POLICY_SCHEMA)
        for k in ("environment","policy_id","previous_policy_digest","issued_at","valid_until","signer_key_id"): _text(v[k])
        if v["domain"]!="aidp-source-authorization" or type(v["policy_epoch"]) is not int or v["policy_epoch"]<0 or not isinstance(v["rows"],list): raise ValueError("invalid policy schema")
        seen=set()
        for r in v["rows"]:
            if not isinstance(r,dict) or set(r)!=_ROW: raise ValueError("invalid policy row")
            for k,x in r.items():
                if k=="minimum_epoch":
                    if type(x) is not int or x<0: raise ValueError("invalid policy epoch")
                else: _text(x)
            if r["algorithm"]!="Ed25519": raise ValueError("invalid policy algorithm")
            ident=tuple(r[k] for k in sorted(_ROW))
            if ident in seen: raise ValueError("duplicate policy tuple")
            seen.add(ident)
        return cls({k:x for k,x in v.items() if k!="signature"},_sig(v["signature"]))
    def verify(self,*,public_key:bytes,environment:str,now:str,highest_epoch:int,previous_digest:str|None):
        if self.payload["environment"]!=environment or self.payload["policy_epoch"]<=highest_epoch or self.payload["previous_policy_digest"]!=(previous_digest or ""): raise ValueError("policy rollback or chain mismatch")
        _fresh(self.payload,now); verify(canonical_bytes(self.payload),self.signature,key_id=self.payload["signer_key_id"],public_key=public_key,schema_version="aidp-attestation-v1")
    def authorize(self,request:dict[str,Any],*,trust_store_id:str,trust_store_epoch:int,revoked_key_ids:set[str]|None=None):
        if set(request)!=_ROW or request["trust_store_id"]!=trust_store_id or request["minimum_epoch"]>trust_store_epoch or request["key_id"] in (revoked_key_ids or set()): raise ValueError("source authorization denied")
        if not any(r==request for r in self.payload["rows"]): raise ValueError("source authorization denied")

class SourceAuthorizationPolicyStore:
    def __init__(self,path:Path): self._cas=DurableCAS(path)
    def accept(self,policy:SourceAuthorizationPolicyV1,*,public_key:bytes,environment:str,now:str):
        c=self._cas.read(); p=None if c is None else c["payload"]
        policy.verify(public_key=public_key,environment=environment,now=now,highest_epoch=-1 if p is None else p["policy_epoch"],previous_digest=None if p is None else p["policy_digest"])
        return self._cas.compare_and_swap(expected_version=None if c is None else c["version"],expected_digest=None if c is None else c["digest"],payload={"environment":environment,"policy_id":policy.payload["policy_id"],"policy_epoch":policy.payload["policy_epoch"],"policy_digest":canonical_digest(policy.payload)})
