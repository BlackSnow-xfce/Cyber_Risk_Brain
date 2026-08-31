from __future__ import annotations

from dataclasses import dataclass

from application.finding_asset_context import (
    FindingAssetContextResolution,
    FindingAssetContextUseCase,
)
from application.business_impact_readiness import (
    BusinessImpactReadiness,
    BusinessImpactReadinessService,
)
from application.finding_asset_business_context import (
    FindingAssetBusinessContextResolution,
    FindingAssetBusinessContextResolutionStatus,
    FindingAssetBusinessContextUseCase,
)
from application.finding_service_impact_profile import (
    FindingServiceImpactProfileResolution,
    FindingServiceImpactProfileResolutionStatus,
    FindingServiceImpactProfileUseCase,
)
from application.finding_technical_effect import (
    FindingTechnicalEffectProjection,
    FindingTechnicalEffectService,
)
from application.business_impact_classification_readiness import (
    BusinessImpactClassificationReadiness,
    BusinessImpactClassificationReadinessService,
)
from application.finding_explanation_use_case import (
    FindingNotFoundError,
    FindingSelectionError,
)
from application.finding_risk_priority import (
    FindingRiskPriority,
    FindingRiskPriorityService,
)
from application.finding_threat_intelligence import (
    FindingThreatIntelligenceEnrichment,
    FindingThreatIntelligenceUseCase,
)
from application.findings_query import FindingsQueryService
from application.risk_readiness import (
    RiskAssessmentInput,
    RiskAssessmentReadinessResult,
    RiskAssessmentReadinessService,
    RiskAssessmentResult,
    RiskReadinessService,
)
from application.security_observation_correlation import (
    SecurityObservationCorrelationApplicationService,
    SecurityObservationCorrelationResult,
)
from core.decision.models import Evidence
from core.models import UniversalFinding


@dataclass(frozen=True, slots=True)
class FindingSourceFact:
    name: str
    value: str
    source_reference: str


@dataclass(frozen=True, slots=True)
class FindingRiskContext:
    finding_id: str
    source_facts: tuple[FindingSourceFact, ...]
    asset_context: FindingAssetContextResolution
    threat_intelligence: FindingThreatIntelligenceEnrichment
    correlation: SecurityObservationCorrelationResult
    evidence: tuple[Evidence, ...]
    risk_inputs: RiskAssessmentInput
    assessment: RiskAssessmentResult
    evidence_readiness: RiskAssessmentReadinessResult
    refusal_reason: str | None
    priority: FindingRiskPriority
    business_context: FindingAssetBusinessContextResolution
    business_impact_readiness: BusinessImpactReadiness
    service_impact_profile: FindingServiceImpactProfileResolution
    technical_effect: FindingTechnicalEffectProjection
    business_impact_classification_readiness: BusinessImpactClassificationReadiness
    business_impact: None = None
    decision: None = None
    recommendations: tuple[None, ...] = ()


def _unavailable_business_context(
    asset_context: FindingAssetContextResolution,
) -> FindingAssetBusinessContextResolution:
    return FindingAssetBusinessContextResolution(
        finding_id=asset_context.finding_id,
        status=(
            FindingAssetBusinessContextResolutionStatus.NOT_FOUND
            if asset_context.asset_context is not None
            else FindingAssetBusinessContextResolutionStatus.MISSING_CANONICAL_ASSET
        ),
    )


class FindingRiskContextUseCase:
    """Compose authoritative finding context without creating a risk result."""

    def __init__(
        self,
        findings: FindingsQueryService,
        asset_context: FindingAssetContextUseCase,
        threat_intelligence: FindingThreatIntelligenceUseCase,
        correlation: SecurityObservationCorrelationApplicationService,
        risk_readiness: RiskReadinessService,
        evidence_readiness: RiskAssessmentReadinessService,
        risk_priority: FindingRiskPriorityService | None = None,
        business_context: FindingAssetBusinessContextUseCase | None = None,
        business_impact_readiness: BusinessImpactReadinessService | None = None,
        service_impact_profile: FindingServiceImpactProfileUseCase | None = None,
        technical_effect: FindingTechnicalEffectService | None = None,
        classification_readiness: BusinessImpactClassificationReadinessService | None = None,
    ) -> None:
        self._findings = findings
        self._asset_context = asset_context
        self._threat_intelligence = threat_intelligence
        self._correlation = correlation
        self._risk_readiness = risk_readiness
        self._evidence_readiness = evidence_readiness
        self._risk_priority = risk_priority or FindingRiskPriorityService()
        self._business_context = business_context
        self._business_impact_readiness = (
            business_impact_readiness or BusinessImpactReadinessService()
        )
        self._service_impact_profile = service_impact_profile
        self._technical_effect = technical_effect or FindingTechnicalEffectService()
        self._classification_readiness = classification_readiness or BusinessImpactClassificationReadinessService()

    def project(self, finding_id: str) -> FindingRiskContext:
        finding = self._select_finding(finding_id)
        asset_context = self._asset_context.resolve(finding_id)
        threat_intelligence = self._threat_intelligence.enrich(finding_id)
        correlation = self._correlation.correlate_snapshot(
            finding_id,
            asset_context,
            threat_intelligence,
        )
        self._require_consistent_snapshot(
            finding,
            asset_context,
            threat_intelligence,
            correlation,
        )

        risk_inputs = RiskAssessmentInput.from_universal_finding(
            finding
        ).with_asset_context(asset_context.asset_context)
        assessment = self._risk_readiness.assess(risk_inputs)
        evidence_readiness = self._evidence_readiness.evaluate(correlation)
        priority = self._risk_priority.prioritize(
            finding.id,
            assessment,
            evidence_readiness,
        )
        business_context = (
            self._business_context.resolve(asset_context)
            if self._business_context is not None
            else _unavailable_business_context(asset_context)
        )
        business_impact_readiness = self._business_impact_readiness.evaluate(
            business_context
        )
        service_impact_profile = (
            self._service_impact_profile.resolve(business_context)
            if self._service_impact_profile is not None
            else FindingServiceImpactProfileResolution(
                finding.id,
                (
                    FindingServiceImpactProfileResolutionStatus.MISSING_CANONICAL_ASSET
                    if business_context.status is FindingAssetBusinessContextResolutionStatus.MISSING_CANONICAL_ASSET
                    else FindingServiceImpactProfileResolutionStatus.NOT_FOUND
                ),
            )
        )
        technical_effect = self._technical_effect.project(threat_intelligence)
        classification_readiness = self._classification_readiness.evaluate(
            business_impact_readiness,
            service_impact_profile,
            technical_effect,
        )
        refusal_parts = [
            f"{item.name}:{item.state.value}"
            for item in assessment.missing_inputs
        ] + list(evidence_readiness.missing_requirements)

        return FindingRiskContext(
            finding_id=finding.id,
            source_facts=self._source_facts(finding),
            asset_context=asset_context,
            threat_intelligence=threat_intelligence,
            correlation=correlation,
            evidence=correlation.evidence,
            risk_inputs=risk_inputs,
            assessment=assessment,
            evidence_readiness=evidence_readiness,
            refusal_reason=(
                "Risk calculation refused because required context is missing: "
                + ", ".join(dict.fromkeys(refusal_parts))
                + "."
                if refusal_parts
                else None
            ),
            priority=priority,
            business_context=business_context,
            business_impact_readiness=business_impact_readiness,
            service_impact_profile=service_impact_profile,
            technical_effect=technical_effect,
            business_impact_classification_readiness=classification_readiness,
        )
    def _select_finding(self, finding_id: str) -> UniversalFinding:
        matches = [
            finding
            for finding in self._findings.get_findings()
            if finding.id == finding_id
        ]
        if not matches:
            raise FindingNotFoundError(finding_id)
        if len(matches) > 1:
            raise FindingSelectionError(
                "Configured finding source contains a duplicate finding ID."
            )
        return matches[0]

    @staticmethod
    def _source_facts(
        finding: UniversalFinding,
    ) -> tuple[FindingSourceFact, ...]:
        source_reference = finding.source
        return (
            FindingSourceFact("finding_id", finding.id, source_reference),
            FindingSourceFact("source", finding.source, source_reference),
            FindingSourceFact("title", finding.title, source_reference),
            FindingSourceFact(
                "vendor_severity",
                finding.vendor_severity,
                source_reference,
            ),
            FindingSourceFact("observed_asset", finding.asset, source_reference),
        )

    @staticmethod
    def _require_consistent_snapshot(
        finding: UniversalFinding,
        asset_context: FindingAssetContextResolution,
        threat_intelligence: FindingThreatIntelligenceEnrichment,
        correlation: SecurityObservationCorrelationResult,
    ) -> None:
        source_reads = (asset_context, threat_intelligence)
        if (
            any(source.finding_id != finding.id for source in source_reads)
            or correlation.finding_id != finding.id
            or any(source.finding_source != finding.source for source in source_reads)
            or any(source.finding_title != finding.title for source in source_reads)
            or any(
                relationship.finding_id != finding.id
                for relationship in (
                    *threat_intelligence.relationships,
                    *correlation.threat_intelligence,
                )
            )
        ):
            raise ValueError(
                "Finding risk-context sources returned different finding snapshots."
            )

        if (
            asset_context.asset_context is not None
            and asset_context.observed_identifier
            != asset_context.asset_context.observed_identifier
        ):
            raise ValueError(
                "Finding risk-context asset resolution is internally inconsistent."
            )

        if asset_context.asset_context != correlation.asset_context:
            raise ValueError(
                "Finding risk-context sources returned different asset context."
            )

        if threat_intelligence.relationships != correlation.threat_intelligence:
            raise ValueError(
                "Finding risk-context sources returned different threat intelligence."
            )
