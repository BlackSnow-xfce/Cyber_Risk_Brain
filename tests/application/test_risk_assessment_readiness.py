from dataclasses import replace

from application import (
    RiskAssessmentReadinessService,
    RiskAssessmentReadinessStatus,
    SecurityObservationCorrelationResult,
)
from core.decision.models import (
    Evidence,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceType,
)
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.threat_intelligence import (
    CisaKevInformation,
    CveIdentifier,
    CvssInformation,
    EpssInformation,
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
    IntelligenceFact,
    NvdIntelligence,
    VulnerabilityThreatIntelligence,
)

FINDING_ID = "6d3167e9-002c-4b76-a5a7-ce47f81b78b1"
CVE = "CVE-2004-2687"


def test_complete_correlation_evidence_is_ready_without_risk_result() -> None:
    result = RiskAssessmentReadinessService().evaluate(complete_input())

    assert result.status is RiskAssessmentReadinessStatus.READY
    assert result.completeness.status is CompletenessStatus.AVAILABLE
    assert result.considered_evidence_ids == (
        f"correlation:{FINDING_ID}:{CVE}",
    )
    assert result.missing_requirements == ()
    assert "available and consistent" in result.reason
    assert not hasattr(result, "score")
    assert not hasattr(result, "risk")
    assert not hasattr(result, "priority")
    assert not hasattr(result, "decision")


def test_identical_inputs_produce_deterministic_readiness() -> None:
    service = RiskAssessmentReadinessService()
    correlation = complete_input()

    assert service.evaluate(correlation) == service.evaluate(correlation)


def test_unresolved_asset_context_is_insufficient_without_default() -> None:
    correlation = replace(
        complete_input(),
        evidence=(),
        asset_context=None,
        threat_intelligence=(),
        completeness=completeness(CompletenessStatus.NO_DATA),
    )

    result = RiskAssessmentReadinessService().evaluate(correlation)

    assert result.status is (
        RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE
    )
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert "canonical_asset_context" in result.missing_requirements
    assert result.considered_evidence_ids == ()


def test_missing_correlation_derived_evidence_is_insufficient() -> None:
    result = RiskAssessmentReadinessService().evaluate(
        replace(complete_input(), evidence=())
    )

    assert result.status is (
        RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE
    )
    assert "correlation_derived_evidence" in result.missing_requirements
    assert f"correlation_derived_evidence:{CVE}" in (
        result.missing_requirements
    )


def test_incomplete_correlation_status_is_preserved() -> None:
    result = RiskAssessmentReadinessService().evaluate(
        replace(
            complete_input(),
            completeness=completeness(
                CompletenessStatus.SOURCE_UNAVAILABLE
            ),
        )
    )

    assert result.status is (
        RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE
    )
    assert result.completeness.status is (
        CompletenessStatus.SOURCE_UNAVAILABLE
    )
    assert "correlation_completeness:source_unavailable" in (
        result.missing_requirements
    )


def test_no_data_correlation_status_is_preserved() -> None:
    correlation = replace(
        complete_input(),
        evidence=(),
        completeness=completeness(CompletenessStatus.NO_DATA),
    )

    result = RiskAssessmentReadinessService().evaluate(correlation)

    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert "correlation_completeness:no_data" in result.missing_requirements


def test_unavailable_required_ti_is_not_interpreted_as_ready() -> None:
    unavailable_epss = fact(
        None,
        "epss",
        "epss:source-unavailable",
        status=CompletenessStatus.SOURCE_UNAVAILABLE,
    )
    relationship = threat_intelligence()
    vulnerability = relationship.vulnerability
    assert vulnerability is not None
    relationship = replace(
        relationship,
        vulnerability=replace(vulnerability, epss=unavailable_epss),
    )

    result = RiskAssessmentReadinessService().evaluate(
        replace(complete_input(), threat_intelligence=(relationship,))
    )

    assert result.status is (
        RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE
    )
    assert "threat_intelligence.epss:source_unavailable" in (
        result.missing_requirements
    )
    assert not hasattr(result, "score")


def test_non_derived_correlation_evidence_is_rejected() -> None:
    source_evidence = replace(
        correlation_evidence(),
        kind=EvidenceKind.SOURCE,
    )

    result = RiskAssessmentReadinessService().evaluate(
        replace(complete_input(), evidence=(source_evidence,))
    )

    assert result.status is (
        RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE
    )
    assert "correlation_evidence_kind:derived" in (
        result.missing_requirements
    )


def test_missing_provenance_reference_is_insufficient() -> None:
    evidence = correlation_evidence()
    assert evidence.provenance is not None
    incomplete_evidence = replace(
        evidence,
        provenance=replace(
            evidence.provenance,
            input_references=tuple(
                reference
                for reference in evidence.provenance.input_references
                if ":epss:" not in reference
            ),
        ),
    )

    result = RiskAssessmentReadinessService().evaluate(
        replace(complete_input(), evidence=(incomplete_evidence,))
    )

    assert "threat_intelligence_evidence_reference:CVE-2004-2687:epss" in (
        result.missing_requirements
    )


def complete_input() -> SecurityObservationCorrelationResult:
    return SecurityObservationCorrelationResult(
        finding_id=FINDING_ID,
        evidence=(correlation_evidence(),),
        completeness=completeness(CompletenessStatus.AVAILABLE),
        asset_context=asset_context(),
        threat_intelligence=(threat_intelligence(),),
    )


def correlation_evidence() -> Evidence:
    vulnerability = threat_intelligence().vulnerability
    assert vulnerability is not None
    references = (
        f"finding:greenbone:{FINDING_ID}",
        (
            "asset-context:asset-lab-metasploitable2-001:"
            "product-owner:metasploitable2-lab-classification"
        ),
        *tuple(
            f"threat-intelligence:{CVE}:{name}:"
            f"{fact_value.provenance.source_reference}"
            for name, fact_value in (
                ("nvd", vulnerability.nvd),
                ("cvss", vulnerability.cvss),
                ("epss", vulnerability.epss),
                ("cisa-kev", vulnerability.cisa_kev),
            )
        ),
    )
    return Evidence(
        evidence_type=EvidenceType.CORRELATION,
        key="finding-cve-canonical-asset-correlation",
        value="Canonical inputs are correlated without a risk statement.",
        identifier=f"correlation:{FINDING_ID}:{CVE}",
        kind=EvidenceKind.DERIVED,
        provenance=EvidenceProvenance(
            source_type="security_observation_correlation",
            source_reference=(
                f"security-observation-correlation:1.0:{FINDING_ID}:{CVE}"
            ),
            input_references=references,
        ),
        contract_version="1.0",
    )


def asset_context() -> AssetContext:
    return AssetContext(
        observed_identifier=ObservedAssetIdentifier(
            AssetIdentifierType.IP_ADDRESS,
            "172.18.0.19",
        ),
        canonical_asset_id="asset-lab-metasploitable2-001",
        criticality=AssetCriticality.LOW,
        source_reference=(
            "product-owner:metasploitable2-lab-classification"
        ),
    )


def threat_intelligence() -> FindingThreatIntelligence:
    return FindingThreatIntelligence(
        finding_id=FINDING_ID,
        applicability=FindingIntelligenceApplicability.APPLICABLE,
        vulnerability=VulnerabilityThreatIntelligence(
            cve_identifier=CveIdentifier(CVE),
            nvd=fact(
                NvdIntelligence(summary="Validated NVD summary."),
                "nvd",
                "nvd:CVE-2004-2687",
            ),
            cvss=fact(
                CvssInformation(
                    version="2.0",
                    base_score=9.3,
                    severity="HIGH",
                    vector="AV:N/AC:M/Au:N/C:C/I:C/A:C",
                ),
                "nvd",
                "nvd:CVE-2004-2687#cvss-2.0",
            ),
            epss=fact(
                EpssInformation(
                    probability=0.88195,
                    percentile=0.99754,
                ),
                "epss",
                "epss:CVE-2004-2687#data-date=2026-08-17",
            ),
            cisa_kev=fact(
                CisaKevInformation(known_exploited=False),
                "cisa_kev",
                "cisa-kev:CVE-2004-2687#catalog=2026.08.17",
            ),
            exploitation_evidence=fact(
                None,
                "cisa_kev",
                "cisa-kev:CVE-2004-2687#not-evaluated",
                status=CompletenessStatus.NOT_EVALUATED,
            ),
        ),
    )


def completeness(status: CompletenessStatus) -> ExplanationCompleteness:
    return ExplanationCompleteness(
        status=status,
        provenance=ExplanationProvenance(
            source_type="security_observation_correlation",
            source_reference=f"correlation:{status.value}",
        ),
    )


def fact(
    value: object | None,
    source_type: str,
    source_reference: str,
    *,
    status: CompletenessStatus = CompletenessStatus.AVAILABLE,
) -> IntelligenceFact[object]:
    return IntelligenceFact(
        value=value,
        completeness=ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type=source_type,
                source_reference=source_reference,
            ),
        ),
    )
