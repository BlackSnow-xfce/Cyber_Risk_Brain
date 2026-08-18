from application import FindingThreatIntelligenceEnrichment
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.threat_intelligence import (
    CveIdentifier,
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)

import api_app


class StubUseCase:
    def __init__(self, enrichment: FindingThreatIntelligenceEnrichment) -> None:
        self.enrichment = enrichment
        self.calls: list[str] = []

    def enrich(self, finding_id: str) -> FindingThreatIntelligenceEnrichment:
        self.calls.append(finding_id)
        return self.enrichment


def test_endpoint_projects_finding_cve_and_existing_contract() -> None:
    intelligence = unavailable_intelligence(CveIdentifier("CVE-2021-44228"))
    use_case = StubUseCase(
        FindingThreatIntelligenceEnrichment(
            finding_id="finding/id",
            finding_source="greenbone",
            finding_title="Controlled finding",
            relationships=(
                FindingThreatIntelligence(
                    finding_id="finding/id",
                    applicability=FindingIntelligenceApplicability.APPLICABLE,
                    vulnerability=intelligence,
                ),
            ),
        )
    )

    response = api_app.finding_threat_intelligence("finding/id", use_case)
    payload = response.model_dump(mode="json")

    assert use_case.calls == ["finding/id"]
    assert payload["finding_id"] == "finding/id"
    assert payload["finding_source"] == "greenbone"
    relationship = payload["relationships"][0]
    assert relationship["applicability"] == "applicable"
    assert relationship["cve_identifier"] == "CVE-2021-44228"
    assert relationship["intelligence"]["contract_version"] == "1.0"
    assert relationship["intelligence"]["epss"]["status"] == (
        "source_unavailable"
    )


def test_endpoint_projects_no_cve_as_not_applicable() -> None:
    use_case = StubUseCase(
        FindingThreatIntelligenceEnrichment(
            finding_id="finding-001",
            finding_source="greenbone",
            finding_title="Configuration finding",
            relationships=(
                FindingThreatIntelligence(
                    finding_id="finding-001",
                    applicability=(
                        FindingIntelligenceApplicability.NOT_APPLICABLE
                    ),
                ),
            ),
        )
    )

    payload = api_app.finding_threat_intelligence(
        "finding-001",
        use_case,
    ).model_dump(mode="json")

    relationship = payload["relationships"][0]
    assert relationship == {
        "applicability": "not_applicable",
        "cve_identifier": None,
        "intelligence": None,
    }


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
