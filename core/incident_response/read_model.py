from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from core.explainability import CompletenessStatus, ExplanationCompleteness

from core.incident_response.activity import IncidentActivity
from core.incident_response.analyst_note import AnalystNote
from core.incident_response.context import (
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentReferenceType,
    IncidentTargetReference,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)

if TYPE_CHECKING:
    from application.incident_investigation import IncidentInvestigationContext


INCIDENT_COMMAND_CENTER_READ_MODEL_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class IncidentReferenceResolution:
    """Read-only owner-boundary result for one incident relationship."""

    reference: IncidentTargetReference
    status: CompletenessStatus
    source_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.reference, (
            FindingReference,
            CanonicalAssetReference,
            ThreatIntelligenceReference,
            EvidenceReference,
            DecisionVersionReference,
        )):
            raise ValueError("Incident reference must be a canonical typed reference.")
        if not isinstance(self.status, CompletenessStatus):
            raise ValueError("Reference resolution status must be canonical.")
        normalized = self.source_reference.strip()
        if not normalized:
            raise ValueError("Reference resolution source must not be empty.")
        object.__setattr__(self, "source_reference", normalized)


@dataclass(frozen=True, slots=True)
class IncidentProjectionSection:
    section: IncidentReferenceType
    status: CompletenessStatus
    reference_ids: tuple[str, ...]
    source_references: tuple[str, ...] = ()
    missing_context: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.section, IncidentReferenceType):
            raise ValueError("Projection section must be canonical.")
        if not isinstance(self.status, CompletenessStatus):
            raise ValueError("Projection section status must be canonical.")
        if len(set(self.reference_ids)) != len(self.reference_ids):
            raise ValueError("Projection reference IDs must be unique.")
        if any(not value.strip() for value in self.reference_ids):
            raise ValueError("Projection reference IDs must not be empty.")
        if any(not value.strip() for value in self.source_references):
            raise ValueError("Projection source references must not be empty.")
        if any(not value.strip() for value in self.missing_context):
            raise ValueError("Projection missing context must not be empty.")


IncidentReferenceTuple: TypeAlias = tuple[IncidentTargetReference, ...]


@dataclass(frozen=True, slots=True)
class IncidentCommandCenterProjection:
    """Read-only projection; it is not an aggregate or source of truth."""

    incident: SecurityIncidentContext
    findings: tuple[FindingReference, ...]
    assets: tuple[CanonicalAssetReference, ...]
    threat_intelligence: tuple[ThreatIntelligenceReference, ...]
    evidence: tuple[EvidenceReference, ...]
    decisions: tuple[DecisionVersionReference, ...]
    notes: tuple[AnalystNote, ...]
    activities: tuple[IncidentActivity, ...]
    sections: tuple[IncidentProjectionSection, ...]
    completeness: ExplanationCompleteness
    missing_context: tuple[str, ...]
    investigation_context: IncidentInvestigationContext | None = None
    contract_version: str = INCIDENT_COMMAND_CENTER_READ_MODEL_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.incident, SecurityIncidentContext):
            raise ValueError("Projection requires a security incident context.")
        if any(note.incident_id != self.incident.incident_id for note in self.notes):
            raise ValueError("Analyst notes must belong to the projected incident.")
        if any(
            activity.incident_id != self.incident.incident_id
            for activity in self.activities
        ):
            raise ValueError("Incident activities must belong to the projected incident.")
        if not isinstance(self.completeness, ExplanationCompleteness):
            raise ValueError("Projection completeness must be canonical.")
        if any(not value.strip() for value in self.missing_context):
            raise ValueError("Projection missing context must not be empty.")
        if not self.contract_version.strip():
            raise ValueError("Projection contract version must not be empty.")
