from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Iterable

from application.finding_asset_context import (
    FindingAssetContextResolution,
    FindingAssetContextResolutionStatus,
)
from application.security_observation_correlation import (
    SecurityObservationCorrelationResult,
)
from core.decision.models import Evidence, EvidenceKind, EvidenceType
from core.enterprise_context import AssetContext, ObservedAssetIdentifier
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.models import UniversalFinding

INCIDENT_INVESTIGATION_CONTRACT_VERSION = "1.0"


class IncidentInvestigationCandidateStatus(StrEnum):
    CANDIDATE = "candidate"


@dataclass(frozen=True, slots=True)
class IncidentObservation:
    incident_id: str
    source: str
    observed_at: datetime | None
    observed_asset_identifier: ObservedAssetIdentifier | None

    def __post_init__(self) -> None:
        incident_id = self.incident_id.strip()
        source = self.source.strip()
        if not incident_id:
            raise ValueError("Incident ID must not be empty.")
        if not source:
            raise ValueError("Incident source must not be empty.")
        if (
            self.observed_at is not None
            and self.observed_at.utcoffset() is None
        ):
            raise ValueError("Incident observed timestamp must be timezone-aware.")
        object.__setattr__(self, "incident_id", incident_id)
        object.__setattr__(self, "source", source)


@dataclass(frozen=True, slots=True)
class IncidentInvestigationFindingInput:
    finding: UniversalFinding
    asset_resolution: FindingAssetContextResolution
    correlation: SecurityObservationCorrelationResult | None = None

    def __post_init__(self) -> None:
        if self.asset_resolution.finding_id != self.finding.id:
            raise ValueError(
                "Finding and asset resolution must reference the same finding."
            )
        if (
            self.correlation is not None
            and self.correlation.finding_id != self.finding.id
        ):
            raise ValueError(
                "Finding and correlation must reference the same finding."
            )


@dataclass(frozen=True, slots=True)
class IncidentInvestigationCandidate:
    finding: UniversalFinding
    status: IncidentInvestigationCandidateStatus
    correlation_evidence: tuple[Evidence, ...]
    threat_intelligence_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    completeness: ExplanationCompleteness


@dataclass(frozen=True, slots=True)
class IncidentInvestigationContext:
    incident_id: str
    incident_source: str
    observed_at: datetime | None
    observed_asset_identifier: ObservedAssetIdentifier | None
    asset_resolution_status: FindingAssetContextResolutionStatus
    asset_context: AssetContext | None
    candidates: tuple[IncidentInvestigationCandidate, ...]
    evidence_references: tuple[str, ...]
    completeness: ExplanationCompleteness
    missing_context: tuple[str, ...]
    contract_version: str = INCIDENT_INVESTIGATION_CONTRACT_VERSION


class IncidentInvestigationService:
    """Build investigation context from existing evidence without causality."""

    def investigate(
        self,
        observation: IncidentObservation,
        asset_context: AssetContext | None,
        finding_inputs: tuple[IncidentInvestigationFindingInput, ...],
    ) -> IncidentInvestigationContext:
        finding_ids = tuple(item.finding.id for item in finding_inputs)
        if len(set(finding_ids)) != len(finding_ids):
            raise ValueError("Investigation finding inputs must be unique.")
        resolution_status = self._resolution_status(observation, asset_context)
        if resolution_status is not FindingAssetContextResolutionStatus.RESOLVED:
            missing = (
                "observed-asset-identifier"
                if resolution_status
                is FindingAssetContextResolutionStatus.MISSING_IDENTIFIER
                else "canonical-asset-context"
            )
            return self._context(
                observation,
                resolution_status,
                asset_context=None,
                candidates=(),
                status=CompletenessStatus.NO_DATA,
                missing_context=(missing,),
            )

        assert asset_context is not None
        candidates = tuple(
            self._candidate(item, asset_context)
            for item in sorted(finding_inputs, key=lambda item: item.finding.id)
            if self._same_canonical_asset(item, asset_context)
        )
        if not candidates:
            return self._context(
                observation,
                resolution_status,
                asset_context=asset_context,
                candidates=(),
                status=CompletenessStatus.NO_DATA,
                missing_context=("finding-candidates",),
            )

        missing_context = tuple(
            (
                f"correlation-evidence:{candidate.finding.id}:"
                f"{candidate.completeness.status.value}"
            )
            for candidate in candidates
            if candidate.completeness.status is not CompletenessStatus.AVAILABLE
        )
        if observation.observed_at is None:
            missing_context = (*missing_context, "incident-observed-timestamp")
        if not missing_context:
            status = CompletenessStatus.AVAILABLE
        elif any(
            candidate.completeness.status
            is CompletenessStatus.SOURCE_UNAVAILABLE
            for candidate in candidates
        ):
            status = CompletenessStatus.SOURCE_UNAVAILABLE
        else:
            status = CompletenessStatus.NO_DATA

        return self._context(
            observation,
            resolution_status,
            asset_context=asset_context,
            candidates=candidates,
            status=status,
            missing_context=missing_context,
        )

    @classmethod
    def _candidate(
        cls,
        item: IncidentInvestigationFindingInput,
        asset_context: AssetContext,
    ) -> IncidentInvestigationCandidate:
        correlation = item.correlation
        finding_reference = f"finding:{item.finding.source}:{item.finding.id}"
        asset_reference = cls._asset_reference(asset_context)
        if correlation is None:
            return cls._incomplete_candidate(
                item.finding,
                CompletenessStatus.NO_DATA,
                "correlation-derived-evidence-missing",
                (finding_reference, asset_reference),
            )
        if correlation.completeness.status is not CompletenessStatus.AVAILABLE:
            return cls._incomplete_candidate(
                item.finding,
                correlation.completeness.status,
                correlation.completeness.provenance.source_reference,
                (finding_reference, asset_reference),
            )

        evidence = tuple(
            evidence
            for evidence in correlation.evidence
            if cls._valid_correlation_evidence(
                evidence,
                finding_reference,
                asset_reference,
            )
        )
        if not evidence or len(evidence) != len(correlation.evidence):
            return cls._incomplete_candidate(
                item.finding,
                CompletenessStatus.NO_DATA,
                "correlation-derived-evidence-provenance-insufficient",
                (finding_reference, asset_reference),
            )

        intelligence_references = cls._unique(
            reference
            for evidence_item in evidence
            for reference in evidence_item.provenance.input_references
            if reference.startswith("threat-intelligence:")
        )
        if not intelligence_references:
            return cls._incomplete_candidate(
                item.finding,
                CompletenessStatus.NO_DATA,
                "threat-intelligence-evidence-references-missing",
                (finding_reference, asset_reference),
            )
        evidence_references = cls._unique(
            reference
            for evidence_item in evidence
            for reference in (
                finding_reference,
                asset_reference,
                evidence_item.identifier,
                evidence_item.provenance.source_reference,
                *evidence_item.provenance.input_references,
            )
        )
        return IncidentInvestigationCandidate(
            finding=item.finding,
            status=IncidentInvestigationCandidateStatus.CANDIDATE,
            correlation_evidence=evidence,
            threat_intelligence_references=intelligence_references,
            evidence_references=evidence_references,
            completeness=cls._completeness(
                CompletenessStatus.AVAILABLE,
                f"investigation-candidate:{item.finding.id}",
            ),
        )

    @classmethod
    def _incomplete_candidate(
        cls,
        finding: UniversalFinding,
        status: CompletenessStatus,
        source_reference: str,
        evidence_references: tuple[str, ...],
    ) -> IncidentInvestigationCandidate:
        return IncidentInvestigationCandidate(
            finding=finding,
            status=IncidentInvestigationCandidateStatus.CANDIDATE,
            correlation_evidence=(),
            threat_intelligence_references=(),
            evidence_references=evidence_references,
            completeness=cls._completeness(status, source_reference),
        )

    @staticmethod
    def _valid_correlation_evidence(
        evidence: Evidence,
        finding_reference: str,
        asset_reference: str,
    ) -> bool:
        return (
            evidence.evidence_type is EvidenceType.CORRELATION
            and evidence.kind is EvidenceKind.DERIVED
            and evidence.identifier is not None
            and evidence.provenance is not None
            and finding_reference in evidence.provenance.input_references
            and asset_reference in evidence.provenance.input_references
        )

    @staticmethod
    def _same_canonical_asset(
        item: IncidentInvestigationFindingInput,
        incident_asset: AssetContext,
    ) -> bool:
        return (
            item.asset_resolution.status
            is FindingAssetContextResolutionStatus.RESOLVED
            and item.asset_resolution.asset_context is not None
            and item.asset_resolution.asset_context.canonical_asset_id
            == incident_asset.canonical_asset_id
        )

    @staticmethod
    def _resolution_status(
        observation: IncidentObservation,
        asset_context: AssetContext | None,
    ) -> FindingAssetContextResolutionStatus:
        if observation.observed_asset_identifier is None:
            if asset_context is not None:
                raise ValueError(
                    "Resolved asset context requires an observed identifier."
                )
            return FindingAssetContextResolutionStatus.MISSING_IDENTIFIER
        if asset_context is None:
            return FindingAssetContextResolutionStatus.NOT_FOUND
        if asset_context.observed_identifier != observation.observed_asset_identifier:
            raise ValueError(
                "Incident observation and asset context identifiers differ."
            )
        return FindingAssetContextResolutionStatus.RESOLVED

    @classmethod
    def _context(
        cls,
        observation: IncidentObservation,
        resolution_status: FindingAssetContextResolutionStatus,
        *,
        asset_context: AssetContext | None,
        candidates: tuple[IncidentInvestigationCandidate, ...],
        status: CompletenessStatus,
        missing_context: tuple[str, ...],
    ) -> IncidentInvestigationContext:
        references = cls._unique(
            reference
            for candidate in candidates
            for reference in candidate.evidence_references
        )
        return IncidentInvestigationContext(
            incident_id=observation.incident_id,
            incident_source=observation.source,
            observed_at=observation.observed_at,
            observed_asset_identifier=observation.observed_asset_identifier,
            asset_resolution_status=resolution_status,
            asset_context=asset_context,
            candidates=candidates,
            evidence_references=references,
            completeness=cls._completeness(
                status,
                f"incident-investigation:1.0:{observation.incident_id}",
            ),
            missing_context=missing_context,
        )

    @staticmethod
    def _asset_reference(asset_context: AssetContext) -> str:
        return (
            f"asset-context:{asset_context.canonical_asset_id}:"
            f"{asset_context.source_reference}"
        )

    @staticmethod
    def _completeness(
        status: CompletenessStatus,
        source_reference: str,
    ) -> ExplanationCompleteness:
        return ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type="incident_investigation",
                source_reference=source_reference,
            ),
        )

    @staticmethod
    def _unique(references: Iterable[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(references))
