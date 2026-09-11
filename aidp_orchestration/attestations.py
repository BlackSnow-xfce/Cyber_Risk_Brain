"""Closed source-attestation schemas and non-configuring bundle verifier."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .foundation import canonical_bytes, canonical_digest, parse_canonical_utf8
from .trust_policy import authorize_source, AuthorizationResult
import re

ATTESTATION_SCHEMA = "aidp-source-attestation-v1"
CATEGORIES = frozenset({"product-owner-recovery-decision", "execution-evidence", "process-lineage", "workspace-ref", "repository-advancement", "execution-source-authority", "trusted-time"})
COMMON = {"schema_version","domain","source_category","source_identity","environment","endpoint_identity","audience","key_namespace","key_id","algorithm","trust_store_id","trust_store_epoch","observation_sequence","issued_at","valid_until","dependency_id","parent_task_id","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","proposal_digest","payload_schema","payload_digest","signature"}

EXTRA = {
 "product-owner-recovery-decision": {"principal","operation","approval_context_id","approval_context_digest","decision_id","nonce","selected_source_digest","selected_source_authority_id"},
 "execution-evidence": {"execution_store_manifest_digest","attempt_identity","attempt_count","result_identity","result_count","heartbeat_range","heartbeat_continuity","execution_outcome","supervisor_ledger_identity"},
 "process-lineage": {"topology_snapshot_digest","host_identity","supervisor_identity","launcher_identity","descendants","job_process_groups","detached_orphan_state","containers","remote_executors","completeness_result"},
 "workspace-ref": {"repository_workspace_manifest_digest","workspace_identities","refs_worktrees_detached_heads","tracked_state","untracked_state","residual_state_assessment"},
 "repository-advancement": {"repository_identity","git_common_identity","remote_identity","branch","original_head","approved_current_head","ancestry_result","repository_snapshot_digest"},
 "execution-source-authority": {"selected_source_authority_id","selected_source_digest","authority_terms_digest","authority_lifecycle_state"},
 "trusted-time": {"trusted_utc_timestamp","monotonic_time_sequence","time_validity_interval","time_service_identity"},
}

@dataclass(frozen=True, slots=True)
class SourceAttestation:
    category: str
    payload: dict[str, Any]
    signature: bytes

    @classmethod
    def parse(cls, raw: bytes) -> "SourceAttestation":
        value = parse_canonical_utf8(raw)
        if canonical_bytes(value) != raw or not isinstance(value, dict): raise ValueError("noncanonical attestation")
        category = value.get("source_category")
        if value.get("schema_version") != ATTESTATION_SCHEMA or category not in CATEGORIES or value.get("domain") != "aidp-source-attestation": raise ValueError("invalid attestation schema")
        fields = COMMON | EXTRA[category]
        if set(value) != fields: raise ValueError("closed attestation schema mismatch")
        signature = canonical_bytes(value.pop("signature"))
        return cls(category, value, signature)

@dataclass(frozen=True, slots=True)
class AttestationBundleManifestV1:
    categories: tuple[str, ...]
    attestation_digests: dict[str, str]
    common_lineage_digest: str
    proposal_digest: str
    trust_store_epoch: int
    policy_epoch: int
    issued_at: str
    valid_until: str

    def encoded(self) -> bytes:
        return canonical_bytes({"schema_version":"aidp-attestation-bundle-manifest-v1","categories":list(self.categories),"attestation_digests":self.attestation_digests,"common_lineage_digest":self.common_lineage_digest,"proposal_digest":self.proposal_digest,"trust_store_epoch":self.trust_store_epoch,"policy_epoch":self.policy_epoch,"issued_at":self.issued_at,"valid_until":self.valid_until})
    @property
    def digest(self) -> str: return canonical_digest(parse_canonical_utf8(self.encoded()))

class AttestationBundleVerifier:
    def verify(self, attestations: list[bytes], *, policies: dict[str, Any], requests: dict[str, dict[str, Any]], environment: str, audience: str, endpoint_identities: dict[str, str], trust_store: dict[str, Any], revoked_key_ids: set[str], public_keys: dict[str, bytes], payload_schema: str, now: str, manifest: AttestationBundleManifestV1 | None = None) -> tuple[AttestationBundleManifestV1, tuple[SourceAttestation, ...]]:
        parsed = [SourceAttestation.parse(raw) for raw in attestations]
        categories = [item.category for item in parsed]
        if len(categories) != len(set(categories)) or set(categories) != CATEGORIES: raise ValueError("incomplete or duplicate attestation bundle")
        common = {k: parsed[0].payload[k] for k in ("environment","dependency_id","parent_task_id","predecessor_authority_id","predecessor_claim_digest","predecessor_execution_id","proposal_digest","selected_source_authority_id") if k in parsed[0].payload}
        for item in parsed:
            if any(item.payload[k] != v for k,v in common.items()): raise ValueError("attestation lineage mismatch")
            result: AuthorizationResult = authorize_source(policy=policies[item.category], request=requests[item.category], environment=environment, audience=audience, endpoint_identity=endpoint_identities[item.category], trust_store=trust_store, revoked_key_ids=revoked_key_ids, payload=canonical_bytes(item.payload), envelope=item.signature, public_key=public_keys[item.payload["key_id"]], payload_schema=payload_schema, lineage=common, expected_lineage=common, now=now)
            if not result.authorized: raise ValueError(f"attestation denied: {result.code}")
            self._validate_semantics(item.payload, common)
        ordered = tuple(sorted(categories)); digests = {item.category: canonical_digest(item.payload) for item in parsed}
        computed = AttestationBundleManifestV1(ordered, digests, canonical_digest(common), common["proposal_digest"], trust_store["monotonic_epoch"], 0, min(item.payload["issued_at"] for item in parsed), max(item.payload["valid_until"] for item in parsed))
        if manifest is not None:
            if manifest != computed:
                raise ValueError("attestation manifest mismatch")
        return computed, tuple(parsed)

    @staticmethod
    def _validate_semantics(payload: dict[str, Any], common: dict[str, Any]) -> None:
        category = payload["source_category"]
        digest = lambda v: isinstance(v, str) and bool(re.fullmatch(r"[0-9a-f]{64}", v))
        if category == "product-owner-recovery-decision":
            if payload.get("operation") != "RECOVER_GATE_DEPENDENCY" or not payload.get("principal") or not payload.get("approval_context_id") or not digest(payload.get("approval_context_digest")) or not payload.get("decision_id") or not payload.get("nonce"): raise ValueError("invalid recovery decision semantics")
            if not digest(payload.get("selected_source_digest")): raise ValueError("invalid recovery decision semantics")
        elif category == "execution-evidence":
            if payload.get("execution_outcome") not in {"FAILED", "BLOCKED"} or not payload.get("attempt_identity") or payload.get("attempt_count") != "1" or not payload.get("result_identity") or payload.get("result_count") != "1" or not payload.get("heartbeat_continuity") or not payload.get("supervisor_ledger_identity") or not digest(payload.get("execution_store_manifest_digest")): raise ValueError("invalid execution evidence semantics")
        elif category == "process-lineage":
            required=("topology_snapshot_digest","host_identity","supervisor_identity","launcher_identity","descendants","job_process_groups","detached_orphan_state","containers","remote_executors")
            if payload.get("completeness_result") != "true" or any(not payload.get(k) for k in required): raise ValueError("invalid process lineage semantics")
        elif category == "workspace-ref":
            if payload.get("residual_state_assessment") != "clean" or not payload.get("workspace_identities") or not payload.get("refs_worktrees_detached_heads") or payload.get("tracked_state") != "clean" or payload.get("untracked_state") != "clean" or not digest(payload.get("repository_workspace_manifest_digest")): raise ValueError("invalid workspace semantics")
        elif category == "repository-advancement":
            if not all(payload.get(k) for k in ("repository_identity","git_common_identity","remote_identity","branch","original_head","approved_current_head","repository_snapshot_digest")) or payload.get("ancestry_result") != "true" or not digest(payload.get("repository_snapshot_digest")): raise ValueError("invalid repository semantics")
        elif category == "execution-source-authority":
            if not payload.get("selected_source_authority_id") or not digest(payload.get("selected_source_digest")) or not digest(payload.get("authority_terms_digest")) or payload.get("authority_lifecycle_state") != "ELIGIBLE": raise ValueError("invalid source authority semantics")
        elif category == "trusted-time":
            if not payload.get("trusted_utc_timestamp") or not payload.get("monotonic_time_sequence") or not payload.get("time_service_identity") or payload.get("time_validity_interval") != "valid": raise ValueError("invalid trusted time semantics")
