from __future__ import annotations

from dataclasses import dataclass

from application.incident_investigation import IncidentObservation
from core.decision.models import EvidenceKind, EvidenceType
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.security_observation import WebIncidentSourceEvidence


@dataclass(frozen=True, slots=True)
class IncidentWebEvidenceContext:
    incident_id: str
    evidence: tuple[WebIncidentSourceEvidence, ...]
    evidence_references: tuple[str, ...]
    completeness: ExplanationCompleteness
    missing_context: tuple[str, ...]


class IncidentWebEvidenceAssociationService:
    """Associate observed target telemetry without inferring causality."""

    def associate(
        self,
        incident: IncidentObservation,
        records: tuple[WebIncidentSourceEvidence, ...],
    ) -> IncidentWebEvidenceContext:
        for record in records:
            if (
                record.evidence.kind is not EvidenceKind.SOURCE
                or record.evidence.evidence_type
                is not EvidenceType.WEB_TELEMETRY
            ):
                raise ValueError(
                    "Incident web evidence must be canonical source evidence."
                )

        if incident.observed_asset_identifier is None:
            return self._context(
                incident.incident_id,
                (),
                CompletenessStatus.NO_DATA,
                ("incident-observed-asset",),
            )

        matching = tuple(
            record
            for record in records
            if record.observed_target_asset
            == incident.observed_asset_identifier
        )
        if not matching:
            return self._context(
                incident.incident_id,
                (),
                CompletenessStatus.NO_DATA,
                ("web-incident-source-evidence",),
            )
        return self._context(
            incident.incident_id,
            matching,
            CompletenessStatus.AVAILABLE,
            (),
        )

    @staticmethod
    def _context(
        incident_id: str,
        records: tuple[WebIncidentSourceEvidence, ...],
        status: CompletenessStatus,
        missing_context: tuple[str, ...],
    ) -> IncidentWebEvidenceContext:
        references = tuple(
            record.evidence.identifier
            for record in records
            if record.evidence.identifier is not None
        )
        return IncidentWebEvidenceContext(
            incident_id=incident_id,
            evidence=records,
            evidence_references=references,
            completeness=ExplanationCompleteness(
                status=status,
                provenance=ExplanationProvenance(
                    source_type="incident_web_evidence_association",
                    source_reference=(
                        f"incident-web-evidence:1.0:{incident_id}"
                    ),
                ),
            ),
            missing_context=missing_context,
        )

