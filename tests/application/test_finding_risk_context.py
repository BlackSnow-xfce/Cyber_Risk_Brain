from dataclasses import replace

import pytest

from application import (
    FindingAssetContextResolution,
    FindingAssetContextResolutionStatus,
    FindingRiskContextUseCase,
    FindingSelectionError,
    FindingThreatIntelligenceEnrichment,
    RiskAssessmentReadinessService,
    RiskAssessmentStatus,
    RiskInputState,
    RiskReadinessService,
    SecurityObservationCorrelationResult,
    ThreatIntelligenceSourceUnavailableError,
)
from core.models import UniversalFinding
from core.explainability import CompletenessStatus
from core.threat_intelligence import (
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
)
from tests.application.test_risk_assessment_readiness import complete_input

FINDING_ID = "6d3167e9-002c-4b76-a5a7-ce47f81b78b1"


class Findings:
    def __init__(self, items=None) -> None:
        self.items = [finding()] if items is None else items

    def get_findings(self):
        return self.items


class Source:
    def __init__(self, value) -> None:
        self.value = value
        self.enrich_calls = 0
        self.correlation_snapshot = None

    def resolve(self, finding_id):
        return self.value

    def enrich(self, finding_id):
        self.enrich_calls += 1
        if isinstance(self.value, Exception):
            raise self.value
        return self.value

    def correlate(self, finding_id):
        return self.value

    def correlate_snapshot(self, finding_id, asset_context, threat_intelligence):
        self.correlation_snapshot = (asset_context, threat_intelligence)
        return self.value


class ForbiddenCalculator:
    def calculate_risk_score(self, node):
        raise AssertionError("Incomplete context must not invoke a calculator.")


def finding(*, asset: str = "172.18.0.19") -> UniversalFinding:
    return UniversalFinding(
        id=FINDING_ID,
        source="greenbone",
        title="DistCC Remote Code Execution Vulnerability",
        vendor_severity="High",
        business_criticality="UNKNOWN",
        asset=asset,
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
        cve_identifiers=("CVE-2004-2687",),
    )


def sources():
    correlated = complete_input()
    resolution = FindingAssetContextResolution(
        finding_id=FINDING_ID,
        finding_source="greenbone",
        finding_title=finding().title,
        status=FindingAssetContextResolutionStatus.RESOLVED,
        observed_identifier=correlated.asset_context.observed_identifier,
        asset_context=correlated.asset_context,
    )
    enrichment = FindingThreatIntelligenceEnrichment(
        finding_id=FINDING_ID,
        finding_source="greenbone",
        finding_title=finding().title,
        relationships=correlated.threat_intelligence,
    )
    return resolution, enrichment, correlated


def project(*, resolution=None, enrichment=None, correlation=None, findings=None):
    default_resolution, default_enrichment, default_correlation = sources()
    return FindingRiskContextUseCase(
        Findings(findings),
        Source(resolution or default_resolution),
        Source(enrichment or default_enrichment),
        Source(correlation or default_correlation),
        RiskReadinessService(ForbiddenCalculator()),
        RiskAssessmentReadinessService(),
    ).project(FINDING_ID)


def test_resolved_projection_preserves_exact_provenance_and_fails_closed() -> None:
    result = project()

    assert result.asset_context.asset_context == result.correlation.asset_context
    assert result.threat_intelligence.relationships == result.correlation.threat_intelligence
    assert result.evidence == result.correlation.evidence
    assert result.evidence_readiness.status.value == "READY"
    assert result.assessment.status is RiskAssessmentStatus.INSUFFICIENT_CONTEXT
    assert result.assessment.score is None
    assert result.priority.status.value == "UNAVAILABLE"
    assert result.priority.band is result.priority.score is None
    assert result.business_impact is result.decision is None
    assert result.recommendations == ()
    assert result.risk_inputs.business_criticality.state is RiskInputState.AUTHORITATIVE
    assert result.risk_inputs.business_criticality.source == (
        "product-owner:metasploitable2-lab-classification"
    )
    assert {item.state for item in result.assessment.missing_inputs} == {
        RiskInputState.NOT_EVALUATED,
    }
    assert all(fact.source_reference == "greenbone" for fact in result.source_facts)
    evidence = result.evidence[0]
    assert evidence.identifier == f"correlation:{FINDING_ID}:CVE-2004-2687"
    assert evidence.provenance is not None
    assert any(
        reference.startswith("asset-context:")
        for reference in evidence.provenance.input_references
    )


def test_projection_reads_ti_once_and_passes_the_exact_snapshot_to_correlation() -> None:
    resolution, enrichment, correlation = sources()
    threat_intelligence = Source(enrichment)
    correlation_source = Source(correlation)

    result = FindingRiskContextUseCase(
        Findings(),
        Source(resolution),
        threat_intelligence,
        correlation_source,
        RiskReadinessService(ForbiddenCalculator()),
        RiskAssessmentReadinessService(),
    ).project(FINDING_ID)

    assert threat_intelligence.enrich_calls == 1
    assert correlation_source.correlation_snapshot == (resolution, enrichment)
    assert result.threat_intelligence is enrichment


@pytest.mark.parametrize(
    ("status", "asset"),
    [
        (FindingAssetContextResolutionStatus.NOT_FOUND, "192.0.2.1"),
        (FindingAssetContextResolutionStatus.MISSING_IDENTIFIER, ""),
    ],
)
def test_unresolved_asset_states_remain_unknown(status, asset) -> None:
    selected = finding(asset=asset)
    resolution = FindingAssetContextResolution(
        finding_id=FINDING_ID,
        finding_source=selected.source,
        finding_title=selected.title,
        status=status,
    )
    _, enrichment, _ = sources()
    enrichment = replace(enrichment, relationships=())
    correlation = SecurityObservationCorrelationResult(
        finding_id=FINDING_ID,
        evidence=(),
        completeness=complete_input().completeness,
    )

    result = project(
        resolution=resolution,
        enrichment=enrichment,
        correlation=correlation,
        findings=[selected],
    )

    assert result.risk_inputs.business_criticality.state is RiskInputState.UNKNOWN
    assert result.assessment.score is None
    assert result.priority.status.value == "UNAVAILABLE"
    assert result.priority.band is result.priority.score is None
    assert result.evidence_readiness.missing_requirements


@pytest.mark.parametrize("correlation_snapshot", ["empty", "different"])
def test_unresolved_asset_rejects_unconsumed_top_level_ti(
    correlation_snapshot,
) -> None:
    selected = finding(asset="192.0.2.1")
    resolution = FindingAssetContextResolution(
        finding_id=FINDING_ID,
        finding_source=selected.source,
        finding_title=selected.title,
        status=FindingAssetContextResolutionStatus.NOT_FOUND,
    )
    _, enrichment, _ = sources()
    correlation_relationships = (
        ()
        if correlation_snapshot == "empty"
        else (
            FindingThreatIntelligence(
                finding_id=FINDING_ID,
                applicability=(
                    FindingIntelligenceApplicability.NOT_APPLICABLE
                ),
            ),
        )
    )
    correlation = SecurityObservationCorrelationResult(
        finding_id=FINDING_ID,
        evidence=(),
        completeness=complete_input().completeness,
        threat_intelligence=correlation_relationships,
    )

    with pytest.raises(
        ValueError,
        match="different threat intelligence",
    ):
        project(
            resolution=resolution,
            enrichment=enrichment,
            correlation=correlation,
            findings=[selected],
        )


def test_unavailable_threat_intelligence_fails_closed() -> None:
    resolution, _, correlation = sources()
    with pytest.raises(ThreatIntelligenceSourceUnavailableError):
        project(
            resolution=resolution,
            enrichment=ThreatIntelligenceSourceUnavailableError("offline"),
            correlation=correlation,
        )


def test_incomplete_applicable_threat_intelligence_remains_explicit() -> None:
    resolution, enrichment, correlation = sources()
    relationship = enrichment.relationships[0]
    assert relationship.vulnerability is not None
    incomplete_fact = replace(
        relationship.vulnerability.epss,
        value=None,
        completeness=replace(
            relationship.vulnerability.epss.completeness,
            status=CompletenessStatus.NO_DATA,
        ),
    )
    incomplete_relationship = replace(
        relationship,
        vulnerability=replace(relationship.vulnerability, epss=incomplete_fact),
    )
    incomplete_enrichment = replace(
        enrichment,
        relationships=(incomplete_relationship,),
    )
    incomplete_correlation = replace(
        correlation,
        evidence=(),
        completeness=replace(
            correlation.completeness,
            status=CompletenessStatus.NO_DATA,
        ),
        threat_intelligence=incomplete_enrichment.relationships,
    )

    result = project(
        resolution=resolution,
        enrichment=incomplete_enrichment,
        correlation=incomplete_correlation,
    )

    assert result.threat_intelligence.relationships[0].vulnerability is not None
    assert (
        result.threat_intelligence.relationships[0].vulnerability.epss.completeness.status
        is CompletenessStatus.NO_DATA
    )
    assert result.evidence_readiness.status.value == "INSUFFICIENT_EVIDENCE"
    assert result.assessment.score is None
    assert result.priority.status.value == "UNAVAILABLE"


@pytest.mark.parametrize(
    "mismatch",
    [
        "source",
        "title",
        "asset",
        "observed_identifier",
        "threat_intelligence",
        "relationship_finding",
        "correlation_finding",
    ],
)
def test_cross_source_snapshot_mismatches_are_rejected(mismatch) -> None:
    resolution, enrichment, correlation = sources()
    if mismatch == "source":
        enrichment = replace(enrichment, finding_source="different-source")
    elif mismatch == "title":
        resolution = replace(resolution, finding_title="different title")
    elif mismatch == "asset":
        assert correlation.asset_context is not None
        correlation = replace(
            correlation,
            asset_context=replace(
                correlation.asset_context,
                source_reference="different-provenance",
            ),
        )
    elif mismatch == "observed_identifier":
        resolution = replace(
            resolution,
            observed_identifier=replace(
                resolution.observed_identifier,
                value="172.18.0.20",
            ),
        )
    elif mismatch == "threat_intelligence":
        correlation = replace(correlation, threat_intelligence=())
    elif mismatch == "relationship_finding":
        mismatched = replace(
            enrichment.relationships[0],
            finding_id="different-finding",
        )
        enrichment = replace(enrichment, relationships=(mismatched,))
        correlation = replace(correlation, threat_intelligence=(mismatched,))
    else:
        correlation = replace(correlation, finding_id="different-finding")

    with pytest.raises(ValueError, match="different|inconsistent"):
        project(
            resolution=resolution,
            enrichment=enrichment,
            correlation=correlation,
        )


def test_duplicate_finding_source_is_rejected_before_projection() -> None:
    with pytest.raises(FindingSelectionError, match="duplicate finding ID"):
        project(findings=[finding(), finding()])


def test_projection_does_not_invoke_legacy_or_ai_authorities(monkeypatch) -> None:
    from core.decision.business_context import BusinessContextEngine
    from core.decision.business_impact_builder import BusinessImpactBuilder
    from core.decision.recommendation_builder import RecommendationBuilder
    from core.predator_engine import PredatorEngine

    def forbidden(*args, **kwargs):
        raise AssertionError("Legacy Decision or AI authority was invoked.")

    monkeypatch.setattr(BusinessContextEngine, "analyze", forbidden)
    monkeypatch.setattr(BusinessImpactBuilder, "build", forbidden)
    monkeypatch.setattr(RecommendationBuilder, "build", forbidden)
    monkeypatch.setattr(PredatorEngine, "run", forbidden)

    result = project()

    assert result.assessment.score is None
    assert result.decision is None
    assert result.recommendations == ()
