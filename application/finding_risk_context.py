from __future__ import annotations

from dataclasses import dataclass

from application.finding_asset_context import (
    FindingAssetContextResolution,
    FindingAssetContextUseCase,
)
from application.finding_explanation_use_case import (
    FindingNotFoundError,
    FindingSelectionError,
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
    priority: None = None
    business_impact: None = None
    decision: None = None
    recommendations: tuple[None, ...] = ()


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
    ) -> None:
        self._findings = findings
        self._asset_context = asset_context
        self._threat_intelligence = threat_intelligence
        self._correlation = correlation
        self._risk_readiness = risk_readiness
        self._evidence_readiness = evidence_readiness

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
