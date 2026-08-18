from __future__ import annotations

from collections.abc import Iterable

from application.incident_investigation import IncidentInvestigationContext
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.incident_response import (
    AnalystNote,
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentActivity,
    IncidentCommandCenterProjection,
    IncidentProjectionSection,
    IncidentReferenceResolution,
    IncidentReferenceType,
    IncidentRelationshipRole,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


class IncidentCommandCenterIncidentNotFoundError(LookupError):
    """Raised when the incident owner cannot provide the requested context."""


class IncidentCommandCenterQueryService:
    """Assemble a read-only command-center projection from owner results."""

    def project(
        self,
        incident: SecurityIncidentContext | None,
        *,
        resolutions: Iterable[IncidentReferenceResolution] = (),
        notes: tuple[AnalystNote, ...] = (),
        activities: tuple[IncidentActivity, ...] = (),
        investigation_context: IncidentInvestigationContext | None = None,
    ) -> IncidentCommandCenterProjection:
        if incident is None:
            raise IncidentCommandCenterIncidentNotFoundError(
                "Security incident context was not found."
            )

        relationships = incident.relationships
        resolution_map = self._resolution_map(resolutions)
        sections: list[IncidentProjectionSection] = []
        missing_context: list[str] = []
        for reference_type, role in (
            (IncidentReferenceType.FINDING, IncidentRelationshipRole.INVESTIGATION_CANDIDATE),
            (IncidentReferenceType.CANONICAL_ASSET, IncidentRelationshipRole.AFFECTED_ASSET),
            (IncidentReferenceType.THREAT_INTELLIGENCE, IncidentRelationshipRole.THREAT_CONTEXT),
            (IncidentReferenceType.EVIDENCE, IncidentRelationshipRole.SUPPORTING_EVIDENCE),
            (IncidentReferenceType.DECISION_VERSION, IncidentRelationshipRole.RELATED_DECISION),
        ):
            targets = tuple(
                relationship.target
                for relationship in relationships
                if relationship.role is role
            )
            section, section_missing = self._section(
                reference_type,
                targets,
                resolution_map,
            )
            sections.append(section)
            missing_context.extend(section_missing)

        self._validate_incident_owned_items(incident, notes, activities)
        if not notes:
            missing_context.append("analyst-notes")
        if not activities:
            missing_context.append("incident-activity")

        statuses = tuple(section.status for section in sections)
        if any(status is CompletenessStatus.SOURCE_UNAVAILABLE for status in statuses):
            overall_status = CompletenessStatus.SOURCE_UNAVAILABLE
        elif any(status is CompletenessStatus.NO_DATA for status in statuses) or missing_context:
            overall_status = CompletenessStatus.NO_DATA
        else:
            overall_status = CompletenessStatus.AVAILABLE

        return IncidentCommandCenterProjection(
            incident=incident,
            findings=tuple(
                target
                for target in (relationship.target for relationship in relationships)
                if isinstance(target, FindingReference)
            ),
            assets=tuple(
                target
                for target in (relationship.target for relationship in relationships)
                if isinstance(target, CanonicalAssetReference)
            ),
            threat_intelligence=tuple(
                target
                for target in (relationship.target for relationship in relationships)
                if isinstance(target, ThreatIntelligenceReference)
            ),
            evidence=tuple(
                target
                for target in (relationship.target for relationship in relationships)
                if isinstance(target, EvidenceReference)
            ),
            decisions=tuple(
                target
                for target in (relationship.target for relationship in relationships)
                if isinstance(target, DecisionVersionReference)
            ),
            notes=notes,
            activities=activities,
            sections=tuple(sections),
            completeness=ExplanationCompleteness(
                status=overall_status,
                provenance=ExplanationProvenance(
                    source_type="incident_command_center_read_model",
                    source_reference=f"incident-command-center:1.0:{incident.incident_id}",
                ),
            ),
            missing_context=tuple(dict.fromkeys(missing_context)),
            investigation_context=investigation_context,
        )

    @staticmethod
    def _resolution_map(
        resolutions: Iterable[IncidentReferenceResolution],
    ) -> dict[tuple[IncidentReferenceType, object], IncidentReferenceResolution]:
        items = tuple(resolutions)
        result: dict[tuple[IncidentReferenceType, object], IncidentReferenceResolution] = {}
        for item in items:
            key = (item.reference.reference_type, item.reference)
            if key in result:
                raise ValueError("Incident reference resolutions must be unique.")
            result[key] = item
        return result

    @classmethod
    def _section(
        cls,
        reference_type: IncidentReferenceType,
        targets: tuple[object, ...],
        resolutions: dict[tuple[IncidentReferenceType, object], IncidentReferenceResolution],
    ) -> tuple[IncidentProjectionSection, tuple[str, ...]]:
        reference_ids = tuple(cls._reference_id(target) for target in targets)
        if not targets:
            return (
                IncidentProjectionSection(reference_type, CompletenessStatus.NOT_APPLICABLE, ()),
                (),
            )

        statuses: list[CompletenessStatus] = []
        missing: list[str] = []
        source_references: list[str] = []
        for target in targets:
            resolution = resolutions.get((reference_type, target))
            if resolution is None:
                statuses.append(CompletenessStatus.NO_DATA)
                missing.append(cls._reference_id(target))
            else:
                statuses.append(resolution.status)
                source_references.append(resolution.source_reference)
                if resolution.status is not CompletenessStatus.AVAILABLE:
                    missing.append(
                        f"{cls._reference_id(target)}:{resolution.status.value}"
                    )

        status = (
            CompletenessStatus.SOURCE_UNAVAILABLE
            if CompletenessStatus.SOURCE_UNAVAILABLE in statuses
            else CompletenessStatus.NO_DATA
            if any(item is not CompletenessStatus.AVAILABLE for item in statuses)
            else CompletenessStatus.AVAILABLE
        )
        return (
            IncidentProjectionSection(
                reference_type,
                status,
                reference_ids,
                tuple(dict.fromkeys(source_references)),
                tuple(missing),
            ),
            tuple(missing),
        )

    @staticmethod
    def _reference_id(target: object) -> str:
        if isinstance(target, FindingReference):
            return f"finding:{target.source}:{target.finding_id}"
        if isinstance(target, CanonicalAssetReference):
            return f"asset:{target.canonical_asset_id}"
        if isinstance(target, ThreatIntelligenceReference):
            return target.reference_id
        if isinstance(target, EvidenceReference):
            return target.evidence_id
        if isinstance(target, DecisionVersionReference):
            return f"decision:{target.decision_id}:{target.version_id}"
        raise ValueError("Unsupported incident reference.")

    @staticmethod
    def _validate_incident_owned_items(
        incident: SecurityIncidentContext,
        notes: tuple[AnalystNote, ...],
        activities: tuple[IncidentActivity, ...],
    ) -> None:
        if any(note.incident_id != incident.incident_id for note in notes):
            raise ValueError("Analyst notes must belong to the incident.")
        if any(activity.incident_id != incident.incident_id for activity in activities):
            raise ValueError("Incident activity must belong to the incident.")
