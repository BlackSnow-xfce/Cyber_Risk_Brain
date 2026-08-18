from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import ClassVar, TypeAlias

from core.incident_response._validation import required, timezone_aware


SECURITY_INCIDENT_CONTEXT_CONTRACT_VERSION = "1.0"


class IncidentLifecycleStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentPrincipalType(StrEnum):
    USER = "user"
    TEAM = "team"
    SYSTEM = "system"


class IncidentParticipantRole(StrEnum):
    ANALYST = "analyst"
    RESPONDER = "responder"
    OBSERVER = "observer"


class IncidentReferenceType(StrEnum):
    FINDING = "finding"
    CANONICAL_ASSET = "canonical_asset"
    THREAT_INTELLIGENCE = "threat_intelligence"
    EVIDENCE = "evidence"
    DECISION_VERSION = "decision_version"


class IncidentRelationshipRole(StrEnum):
    INVESTIGATION_CANDIDATE = "investigation_candidate"
    AFFECTED_ASSET = "affected_asset"
    THREAT_CONTEXT = "threat_context"
    SUPPORTING_EVIDENCE = "supporting_evidence"
    RELATED_DECISION = "related_decision"


@dataclass(frozen=True, slots=True)
class IncidentPrincipalReference:
    principal_type: IncidentPrincipalType
    principal_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.principal_type, IncidentPrincipalType):
            raise ValueError("Incident principal type must be canonical.")
        object.__setattr__(
            self,
            "principal_id",
            required(self.principal_id, "Incident principal ID"),
        )


@dataclass(frozen=True, slots=True)
class IncidentParticipant:
    principal: IncidentPrincipalReference
    role: IncidentParticipantRole

    def __post_init__(self) -> None:
        if not isinstance(self.principal, IncidentPrincipalReference):
            raise ValueError("Incident participant must reference a principal.")
        if not isinstance(self.role, IncidentParticipantRole):
            raise ValueError("Incident participant role must be canonical.")


@dataclass(frozen=True, slots=True)
class FindingReference:
    reference_type: ClassVar[IncidentReferenceType] = IncidentReferenceType.FINDING

    finding_id: str
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", required(self.finding_id, "Finding ID"))
        object.__setattr__(self, "source", required(self.source, "Finding source"))


@dataclass(frozen=True, slots=True)
class CanonicalAssetReference:
    reference_type: ClassVar[IncidentReferenceType] = (
        IncidentReferenceType.CANONICAL_ASSET
    )

    canonical_asset_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_asset_id",
            required(self.canonical_asset_id, "Canonical asset ID"),
        )


@dataclass(frozen=True, slots=True)
class ThreatIntelligenceReference:
    reference_type: ClassVar[IncidentReferenceType] = (
        IncidentReferenceType.THREAT_INTELLIGENCE
    )

    reference_id: str
    contract_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_id",
            required(self.reference_id, "Threat intelligence reference ID"),
        )
        object.__setattr__(
            self,
            "contract_version",
            required(self.contract_version, "Threat intelligence contract version"),
        )


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    reference_type: ClassVar[IncidentReferenceType] = IncidentReferenceType.EVIDENCE

    evidence_id: str
    contract_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            required(self.evidence_id, "Evidence ID"),
        )
        object.__setattr__(
            self,
            "contract_version",
            required(self.contract_version, "Evidence contract version"),
        )


@dataclass(frozen=True, slots=True)
class DecisionVersionReference:
    reference_type: ClassVar[IncidentReferenceType] = (
        IncidentReferenceType.DECISION_VERSION
    )

    decision_id: str
    version_id: str
    evidence_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "decision_id",
            required(self.decision_id, "Decision ID"),
        )
        object.__setattr__(
            self,
            "version_id",
            required(self.version_id, "Decision version ID"),
        )
        if self.evidence_snapshot_id is not None:
            object.__setattr__(
                self,
                "evidence_snapshot_id",
                required(self.evidence_snapshot_id, "Evidence snapshot ID"),
            )


IncidentTargetReference: TypeAlias = (
    FindingReference
    | CanonicalAssetReference
    | ThreatIntelligenceReference
    | EvidenceReference
    | DecisionVersionReference
)

_REFERENCE_TYPES = (
    FindingReference,
    CanonicalAssetReference,
    ThreatIntelligenceReference,
    EvidenceReference,
    DecisionVersionReference,
)

_ROLE_TARGET_TYPES: dict[IncidentRelationshipRole, type[object]] = {
    IncidentRelationshipRole.INVESTIGATION_CANDIDATE: FindingReference,
    IncidentRelationshipRole.AFFECTED_ASSET: CanonicalAssetReference,
    IncidentRelationshipRole.THREAT_CONTEXT: ThreatIntelligenceReference,
    IncidentRelationshipRole.SUPPORTING_EVIDENCE: EvidenceReference,
    IncidentRelationshipRole.RELATED_DECISION: DecisionVersionReference,
}


@dataclass(frozen=True, slots=True)
class IncidentRelationship:
    relationship_id: str
    role: IncidentRelationshipRole
    target: IncidentTargetReference

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relationship_id",
            required(self.relationship_id, "Incident relationship ID"),
        )
        if not isinstance(self.role, IncidentRelationshipRole):
            raise ValueError("Incident relationship role must be canonical.")
        if not isinstance(self.target, _REFERENCE_TYPES):
            raise ValueError("Incident relationships require a typed reference.")
        expected_target = _ROLE_TARGET_TYPES[self.role]
        if not isinstance(self.target, expected_target):
            raise ValueError(
                "Incident relationship role and target type are incompatible."
            )


@dataclass(frozen=True, slots=True)
class SecurityIncidentContext:
    incident_id: str
    lifecycle_status: IncidentLifecycleStatus
    source: str
    source_reference: str
    title: str
    created_at: datetime
    updated_at: datetime
    owner: IncidentPrincipalReference | None = None
    participants: tuple[IncidentParticipant, ...] = ()
    description: str | None = None
    relationships: tuple[IncidentRelationship, ...] = ()
    contract_version: str = SECURITY_INCIDENT_CONTEXT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "incident_id", required(self.incident_id, "Incident ID"))
        if not isinstance(self.lifecycle_status, IncidentLifecycleStatus):
            raise ValueError("Incident lifecycle status must be canonical.")
        object.__setattr__(self, "source", required(self.source, "Incident source"))
        object.__setattr__(
            self,
            "source_reference",
            required(self.source_reference, "Incident source reference"),
        )
        object.__setattr__(self, "title", required(self.title, "Incident title"))
        timezone_aware(self.created_at, "Incident created timestamp")
        timezone_aware(self.updated_at, "Incident updated timestamp")
        if self.updated_at < self.created_at:
            raise ValueError("Incident updated timestamp must not precede creation.")
        if self.owner is not None and not isinstance(
            self.owner, IncidentPrincipalReference
        ):
            raise ValueError("Incident owner must be a principal reference.")
        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                required(self.description, "Incident description"),
            )
        object.__setattr__(
            self,
            "contract_version",
            required(self.contract_version, "Incident contract version"),
        )
        if any(not isinstance(item, IncidentParticipant) for item in self.participants):
            raise ValueError("Incident participants must be typed references.")
        if len(set(self.participants)) != len(self.participants):
            raise ValueError("Incident participants must be unique.")
        if any(
            not isinstance(item, IncidentRelationship)
            for item in self.relationships
        ):
            raise ValueError("Incident relationships must be typed references.")
        relationship_ids = tuple(
            relationship.relationship_id for relationship in self.relationships
        )
        if len(set(relationship_ids)) != len(relationship_ids):
            raise ValueError("Incident relationship IDs must be unique.")
        relationship_keys = tuple(
            (relationship.role, relationship.target)
            for relationship in self.relationships
        )
        if len(set(relationship_keys)) != len(relationship_keys):
            raise ValueError("Incident relationships must be unique.")
