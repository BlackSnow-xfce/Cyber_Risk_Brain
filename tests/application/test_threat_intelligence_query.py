import pytest

from application import (
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceDataError,
    ThreatIntelligenceNotFoundError,
    ThreatIntelligenceQueryService,
)
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.threat_intelligence import (
    CveIdentifier,
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)


def unavailable(source: str):
    return IntelligenceFact(
        value=None,
        completeness=ExplanationCompleteness(
            status=CompletenessStatus.SOURCE_UNAVAILABLE,
            provenance=ExplanationProvenance(
                source_type=source,
                source_reference=f"{source}:unconfigured",
            ),
        ),
    )


def record(cve: str) -> VulnerabilityThreatIntelligence:
    return VulnerabilityThreatIntelligence(
        cve_identifier=CveIdentifier(cve),
        nvd=unavailable("nvd"),
        cvss=unavailable("nvd"),
        epss=unavailable("epss"),
        cisa_kev=unavailable("cisa_kev"),
        exploitation_evidence=unavailable("cisa_kev"),
    )


class StubReader:
    def __init__(self, result: VulnerabilityThreatIntelligence | None) -> None:
        self.result = result
        self.calls: list[CveIdentifier] = []

    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence | None:
        self.calls.append(cve_identifier)
        return self.result


def test_query_reads_one_canonical_cve_without_evaluation() -> None:
    reader = StubReader(record("CVE-2026-12345"))
    service = ThreatIntelligenceQueryService(reader)

    result = service.get_by_cve("cve-2026-12345")

    assert result.cve_identifier.value == "CVE-2026-12345"
    assert [item.value for item in reader.calls] == ["CVE-2026-12345"]


def test_query_reports_configuration_not_found_and_reader_mismatch() -> None:
    with pytest.raises(ThreatIntelligenceConfigurationError):
        ThreatIntelligenceQueryService(None).get_by_cve("CVE-2026-12345")

    with pytest.raises(ThreatIntelligenceNotFoundError):
        ThreatIntelligenceQueryService(StubReader(None)).get_by_cve(
            "CVE-2026-12345"
        )

    with pytest.raises(ThreatIntelligenceDataError):
        ThreatIntelligenceQueryService(
            StubReader(record("CVE-2026-99999"))
        ).get_by_cve("CVE-2026-12345")

