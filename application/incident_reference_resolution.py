from __future__ import annotations

from collections.abc import Iterable

from application.asset_context import (
    AssetContextConfigurationError,
    AssetContextDataError,
    AssetContextQueryService,
)
from application.findings_query import FindingsConfigurationError, FindingsQueryService
from application.threat_intelligence import (
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceDataError,
    ThreatIntelligenceNotFoundError,
    ThreatIntelligenceQueryService,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.explainability import CompletenessStatus
from core.incident_response import (
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentReferenceResolution,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


class IncidentReferenceResolutionService:
    """Resolve incident references through existing authoritative readers."""

    def __init__(
        self,
        findings: FindingsQueryService | None,
        assets: AssetContextQueryService | None,
        threat_intelligence: ThreatIntelligenceQueryService | None,
    ) -> None:
        self._findings = findings
        self._assets = assets
        self._threat_intelligence = threat_intelligence

    def resolve(
        self,
        incident: SecurityIncidentContext,
    ) -> tuple[IncidentReferenceResolution, ...]:
        resolutions: list[IncidentReferenceResolution] = []
        for relationship in incident.relationships:
            reference = relationship.target
            if isinstance(reference, FindingReference):
                resolutions.append(self._finding(reference))
            elif isinstance(reference, CanonicalAssetReference):
                resolutions.append(self._asset(reference))
            elif isinstance(reference, ThreatIntelligenceReference):
                resolutions.append(self._threat_intelligence_reference(reference))
            elif isinstance(reference, (EvidenceReference, DecisionVersionReference)):
                resolutions.append(
                    IncidentReferenceResolution(
                        reference,
                        CompletenessStatus.NO_DATA,
                        f"incident-reference-resolver:unsupported:{reference.reference_type.value}",
                    )
                )
        return tuple(resolutions)

    def _finding(self, reference: FindingReference) -> IncidentReferenceResolution:
        if self._findings is None:
            return self._missing(reference, "findings:resolver-not-configured")
        try:
            matches = tuple(
                finding
                for finding in self._findings.get_findings()
                if finding.id == reference.finding_id
                and finding.source == reference.source
            )
        except FindingsConfigurationError:
            return self._unavailable(reference, "findings")
        if len(matches) != 1:
            return self._missing(reference, "findings")
        return self._available(reference, f"finding-query:{reference.source}:{reference.finding_id}")

    def _asset(self, reference: CanonicalAssetReference) -> IncidentReferenceResolution:
        if self._assets is None:
            return self._missing(reference, "asset-context:resolver-not-configured")
        try:
            asset = self._assets.resolve_canonical_asset(reference.canonical_asset_id)
        except (AssetContextConfigurationError, AssetContextDataError):
            return self._unavailable(reference, "asset-context")
        if asset is None:
            return self._missing(reference, "asset-context")
        return self._available(reference, asset.source_reference)

    def _threat_intelligence_reference(
        self,
        reference: ThreatIntelligenceReference,
    ) -> IncidentReferenceResolution:
        if self._threat_intelligence is None:
            return self._missing(
                reference, "threat-intelligence:resolver-not-configured"
            )
        try:
            intelligence = self._threat_intelligence.get_by_cve(reference.reference_id)
        except ThreatIntelligenceNotFoundError:
            return self._missing(reference, "threat-intelligence")
        except (
            ThreatIntelligenceConfigurationError,
            ThreatIntelligenceDataError,
            ThreatIntelligenceSourceUnavailableError,
            ThreatIntelligenceTimeoutError,
            ValueError,
        ):
            return self._unavailable(reference, "threat-intelligence")
        nvd_status = intelligence.nvd.completeness.status
        if nvd_status is CompletenessStatus.SOURCE_UNAVAILABLE:
            return self._unavailable(reference, "threat-intelligence")
        if nvd_status is not CompletenessStatus.AVAILABLE:
            return self._missing(reference, "threat-intelligence")
        return self._available(
            reference,
            intelligence.nvd.completeness.provenance.source_reference,
        )

    @staticmethod
    def _available(reference: object, source_reference: str) -> IncidentReferenceResolution:
        return IncidentReferenceResolution(
            reference, CompletenessStatus.AVAILABLE, source_reference
        )

    @staticmethod
    def _missing(reference: object, source: str) -> IncidentReferenceResolution:
        return IncidentReferenceResolution(
            reference, CompletenessStatus.NO_DATA, f"{source}:not-found"
        )

    @staticmethod
    def _unavailable(reference: object, source: str) -> IncidentReferenceResolution:
        return IncidentReferenceResolution(
            reference, CompletenessStatus.SOURCE_UNAVAILABLE, f"{source}:unavailable"
        )
