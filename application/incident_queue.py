from __future__ import annotations

from dataclasses import dataclass

from core.incident_response import (
    CanonicalAssetReference,
    EvidenceReference,
    FindingReference,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)

from application.incident_repository import IncidentContextRepository


@dataclass(frozen=True, slots=True)
class IncidentQueueItem:
    """Stable read-only projection for the Incident Queue API."""

    incident: SecurityIncidentContext
    participant_count: int
    finding_count: int
    asset_count: int
    threat_intelligence_count: int
    evidence_count: int


class IncidentQueueQueryService:
    """List canonical Incident Contexts without adding a mutation boundary."""

    def __init__(self, repository: IncidentContextRepository) -> None:
        self._repository = repository

    def list(self) -> tuple[IncidentQueueItem, ...]:
        return tuple(self._project(context) for context in self._repository.list())

    @staticmethod
    def _project(context: SecurityIncidentContext) -> IncidentQueueItem:
        return IncidentQueueItem(
            incident=context,
            participant_count=len(context.participants),
            finding_count=sum(
                isinstance(relationship.target, FindingReference)
                for relationship in context.relationships
            ),
            asset_count=sum(
                isinstance(relationship.target, CanonicalAssetReference)
                for relationship in context.relationships
            ),
            threat_intelligence_count=sum(
                isinstance(relationship.target, ThreatIntelligenceReference)
                for relationship in context.relationships
            ),
            evidence_count=sum(
                isinstance(relationship.target, EvidenceReference)
                for relationship in context.relationships
            ),
        )
