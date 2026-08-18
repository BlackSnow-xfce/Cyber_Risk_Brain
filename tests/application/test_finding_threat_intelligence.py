from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.models import UniversalFinding
from core.threat_intelligence import (
    CveIdentifier,
    FindingIntelligenceApplicability,
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)
from application import FindingThreatIntelligenceUseCase


class StubFindings:
    def __init__(self, finding: UniversalFinding) -> None:
        self.finding = finding

    def get_findings(self) -> list[UniversalFinding]:
        return [self.finding]


class RecordingReader:
    def __init__(self) -> None:
        self.calls: list[CveIdentifier] = []

    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence:
        self.calls.append(cve_identifier)
        return unavailable_intelligence(cve_identifier)


def test_finding_with_multiple_cves_uses_existing_ti_contract_per_cve() -> None:
    reader = RecordingReader()
    use_case = FindingThreatIntelligenceUseCase(
        StubFindings(
            finding(
                "CVE-2021-44228",
                "cve-2024-12345",
                "CVE-2021-44228",
            )
        ),
        reader,
    )

    result = use_case.enrich("finding-001")

    assert result.finding_id == "finding-001"
    assert result.finding_source == "greenbone"
    assert [call.value for call in reader.calls] == [
        "CVE-2021-44228",
        "CVE-2024-12345",
    ]
    assert [
        relationship.applicability
        for relationship in result.relationships
    ] == [
        FindingIntelligenceApplicability.APPLICABLE,
        FindingIntelligenceApplicability.APPLICABLE,
    ]
    assert [
        relationship.vulnerability.contract_version
        for relationship in result.relationships
        if relationship.vulnerability is not None
    ] == ["1.0", "1.0"]


def test_finding_without_cve_is_not_applicable_and_skips_ti_reader() -> None:
    reader = RecordingReader()
    use_case = FindingThreatIntelligenceUseCase(
        StubFindings(finding()),
        reader,
    )

    result = use_case.enrich("finding-001")

    assert reader.calls == []
    assert len(result.relationships) == 1
    relationship = result.relationships[0]
    assert (
        relationship.applicability
        == FindingIntelligenceApplicability.NOT_APPLICABLE
    )
    assert relationship.vulnerability is None


def test_unavailable_ti_remains_contract_status_without_interpretation() -> None:
    reader = RecordingReader()
    use_case = FindingThreatIntelligenceUseCase(
        StubFindings(finding("CVE-2021-44228")),
        reader,
    )

    relationship = use_case.enrich("finding-001").relationships[0]

    intelligence = relationship.vulnerability
    assert intelligence is not None
    assert intelligence.contract_version == "1.0"
    for fact in (
        intelligence.nvd,
        intelligence.cvss,
        intelligence.epss,
        intelligence.cisa_kev,
        intelligence.exploitation_evidence,
    ):
        assert fact.completeness.status == CompletenessStatus.SOURCE_UNAVAILABLE
        assert fact.value is None
    assert not hasattr(relationship, "risk")
    assert not hasattr(relationship, "priority")
    assert not hasattr(relationship, "decision")


def finding(*cves: str) -> UniversalFinding:
    return UniversalFinding(
        id="finding-001",
        source="greenbone",
        title="Controlled finding",
        vendor_severity="High",
        business_criticality="UNKNOWN",
        asset="192.0.2.10",
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
        cve_identifiers=tuple(cves),
    )


def unavailable_intelligence(
    cve_identifier: CveIdentifier,
) -> VulnerabilityThreatIntelligence:
    return VulnerabilityThreatIntelligence(
        cve_identifier=cve_identifier,
        nvd=unavailable("nvd"),
        cvss=unavailable("nvd"),
        epss=unavailable("epss"),
        cisa_kev=unavailable("cisa_kev"),
        exploitation_evidence=unavailable("cisa_kev"),
    )


def unavailable(source: str):
    return IntelligenceFact(
        value=None,
        completeness=ExplanationCompleteness(
            status=CompletenessStatus.SOURCE_UNAVAILABLE,
            provenance=ExplanationProvenance(
                source_type=source,
                source_reference=f"{source}:unavailable",
            ),
        ),
    )
