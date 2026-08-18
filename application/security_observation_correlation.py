from __future__ import annotations

from dataclasses import dataclass

from application.finding_asset_context import (
    FindingAssetContextResolutionStatus,
    FindingAssetContextUseCase,
)
from application.finding_threat_intelligence import (
    FindingThreatIntelligenceUseCase,
)
from core.decision.models import Evidence
from core.enterprise_context import AssetContext
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.security_observation import (
    SecurityObservationCorrelationInput,
    SecurityObservationCorrelationService,
)
from core.threat_intelligence import (
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
)


@dataclass(frozen=True, slots=True)
class SecurityObservationCorrelationResult:
    finding_id: str
    evidence: tuple[Evidence, ...]
    completeness: ExplanationCompleteness
    asset_context: AssetContext | None = None
    threat_intelligence: tuple[FindingThreatIntelligence, ...] = ()


class SecurityObservationCorrelationApplicationService:
    """Orchestrate existing source reads and the correlation domain service."""

    _INCOMPLETE_STATUS_PRECEDENCE = (
        CompletenessStatus.SOURCE_UNAVAILABLE,
        CompletenessStatus.NO_DATA,
        CompletenessStatus.NOT_EVALUATED,
        CompletenessStatus.UNKNOWN,
        CompletenessStatus.NOT_APPLICABLE,
        CompletenessStatus.NOT_PART_OF_EXECUTION,
    )

    def __init__(
        self,
        finding_threat_intelligence: FindingThreatIntelligenceUseCase,
        finding_asset_context: FindingAssetContextUseCase,
        correlation: SecurityObservationCorrelationService,
    ) -> None:
        self._finding_threat_intelligence = finding_threat_intelligence
        self._finding_asset_context = finding_asset_context
        self._correlation = correlation

    def correlate(self, finding_id: str) -> SecurityObservationCorrelationResult:
        asset_resolution = self._finding_asset_context.resolve(finding_id)
        if (
            asset_resolution.status
            is not FindingAssetContextResolutionStatus.RESOLVED
            or asset_resolution.asset_context is None
        ):
            return self._incomplete(
                finding_id,
                CompletenessStatus.NO_DATA,
                "canonical-asset-context-unresolved",
            )

        enrichment = self._finding_threat_intelligence.enrich(finding_id)
        if enrichment.finding_id != asset_resolution.finding_id:
            raise ValueError("Correlation source reads returned different findings.")

        evidence: list[Evidence] = []
        for relationship in enrichment.relationships:
            if (
                relationship.applicability
                is not FindingIntelligenceApplicability.APPLICABLE
                or relationship.vulnerability is None
            ):
                return self._incomplete(
                    finding_id,
                    CompletenessStatus.NOT_APPLICABLE,
                    "cve-threat-intelligence-not-applicable",
                    asset_context=asset_resolution.asset_context,
                    threat_intelligence=enrichment.relationships,
                )
            required_facts = (
                ("nvd", relationship.vulnerability.nvd),
                ("cvss", relationship.vulnerability.cvss),
                ("epss", relationship.vulnerability.epss),
                ("cisa_kev", relationship.vulnerability.cisa_kev),
            )
            incomplete_facts = tuple(
                (name, fact.completeness.status)
                for name, fact in required_facts
                if fact.completeness.status is not CompletenessStatus.AVAILABLE
            )
            if incomplete_facts:
                return self._incomplete(
                    finding_id,
                    self._aggregate_incomplete_status(incomplete_facts),
                    self._incomplete_source_reference(incomplete_facts),
                    asset_context=asset_resolution.asset_context,
                    threat_intelligence=enrichment.relationships,
                )
            evidence.append(
                self._correlation.correlate(
                    SecurityObservationCorrelationInput(
                        finding_id=finding_id,
                        finding_source=enrichment.finding_source,
                        asset_context=asset_resolution.asset_context,
                        threat_intelligence=relationship,
                    )
                )
            )

        return SecurityObservationCorrelationResult(
            finding_id=finding_id,
            evidence=tuple(evidence),
            completeness=self._completeness(
                CompletenessStatus.AVAILABLE,
                "correlation-derived-evidence-available",
            ),
            asset_context=asset_resolution.asset_context,
            threat_intelligence=enrichment.relationships,
        )

    @classmethod
    def _aggregate_incomplete_status(
        cls,
        incomplete_facts: tuple[tuple[str, CompletenessStatus], ...],
    ) -> CompletenessStatus:
        statuses = {status for _, status in incomplete_facts}
        for status in cls._INCOMPLETE_STATUS_PRECEDENCE:
            if status in statuses:
                return status
        raise ValueError("Unsupported threat-intelligence completeness status.")

    @staticmethod
    def _incomplete_source_reference(
        incomplete_facts: tuple[tuple[str, CompletenessStatus], ...],
    ) -> str:
        details = ",".join(
            f"{name}={status.value}" for name, status in incomplete_facts
        )
        return f"required-threat-intelligence-incomplete:{details}"

    @classmethod
    def _incomplete(
        cls,
        finding_id: str,
        status: CompletenessStatus,
        source_reference: str,
        *,
        asset_context: AssetContext | None = None,
        threat_intelligence: tuple[FindingThreatIntelligence, ...] = (),
    ) -> SecurityObservationCorrelationResult:
        return SecurityObservationCorrelationResult(
            finding_id=finding_id,
            evidence=(),
            completeness=cls._completeness(status, source_reference),
            asset_context=asset_context,
            threat_intelligence=threat_intelligence,
        )

    @staticmethod
    def _completeness(
        status: CompletenessStatus,
        source_reference: str,
    ) -> ExplanationCompleteness:
        return ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type="security_observation_correlation",
                source_reference=source_reference,
            ),
        )
