from datetime import date, datetime, timezone

import pytest

from application import (
    ThreatIntelligenceDataError,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
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
    IntelligenceFact,
    NvdIntelligence,
    VulnerabilityThreatIntelligence,
)
from infrastructure import CompositeThreatIntelligenceReader

CVE = CveIdentifier("CVE-2021-44228")
OTHER_CVE = CveIdentifier("CVE-2024-12345")
OBSERVED_AT = datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc)


def fact(value, status: CompletenessStatus, source: str, reference: str):
    return IntelligenceFact(
        value=value,
        completeness=ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type=source,
                source_reference=reference,
            ),
        ),
        observed_at=OBSERVED_AT if status == CompletenessStatus.AVAILABLE else None,
    )


def not_evaluated(source: str, field: str):
    return fact(
        None,
        CompletenessStatus.NOT_EVALUATED,
        source,
        f"{source}:{field}:not_evaluated",
    )


def nvd_response(cve: CveIdentifier = CVE):
    return VulnerabilityThreatIntelligence(
        cve_identifier=cve,
        nvd=fact(
            NvdIntelligence(summary="Controlled NVD fact."),
            CompletenessStatus.AVAILABLE,
            "nvd",
            "nvd:fact",
        ),
        cvss=fact(
            CvssInformation(
                version="3.1",
                base_score=10.0,
                vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                severity="CRITICAL",
            ),
            CompletenessStatus.AVAILABLE,
            "nvd",
            "nvd:cvss",
        ),
        epss=not_evaluated("epss", "by_nvd"),
        cisa_kev=not_evaluated("cisa_kev", "by_nvd"),
        exploitation_evidence=not_evaluated("nvd", "evidence_by_nvd"),
    )


def epss_response(status: CompletenessStatus = CompletenessStatus.AVAILABLE):
    value = (
        EpssInformation(probability=0.94, percentile=0.99)
        if status == CompletenessStatus.AVAILABLE
        else None
    )
    return VulnerabilityThreatIntelligence(
        cve_identifier=CVE,
        nvd=not_evaluated("nvd", "by_epss"),
        cvss=not_evaluated("nvd", "cvss_by_epss"),
        epss=fact(value, status, "epss", "epss:fact"),
        cisa_kev=not_evaluated("cisa_kev", "by_epss"),
        exploitation_evidence=not_evaluated("epss", "evidence_by_epss"),
    )


def kev_response(member: bool = True):
    value = (
        CisaKevInformation(
            known_exploited=True,
            date_added=date(2021, 12, 10),
            required_action="Apply vendor updates.",
            due_date=date(2021, 12, 24),
        )
        if member
        else CisaKevInformation(known_exploited=False)
    )
    return VulnerabilityThreatIntelligence(
        cve_identifier=CVE,
        nvd=not_evaluated("nvd", "by_kev"),
        cvss=not_evaluated("nvd", "cvss_by_kev"),
        epss=not_evaluated("epss", "by_kev"),
        cisa_kev=fact(
            value,
            CompletenessStatus.AVAILABLE,
            "cisa_kev",
            "cisa_kev:fact",
        ),
        exploitation_evidence=not_evaluated(
            "cisa_kev",
            "evidence_by_kev",
        ),
    )


class ControlledReader:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[CveIdentifier] = []

    def get_by_cve(self, cve_identifier: CveIdentifier):
        self.calls.append(cve_identifier)
        if self.error is not None:
            raise self.error
        return self.result


def composite(nvd=None, epss=None, kev=None):
    readers = (
        ControlledReader(nvd if nvd is not None else nvd_response()),
        ControlledReader(epss if epss is not None else epss_response()),
        ControlledReader(kev if kev is not None else kev_response()),
    )
    return CompositeThreatIntelligenceReader(*readers), readers


def test_all_sources_available_merge_only_authoritative_facts() -> None:
    reader, readers = composite()

    result = reader.get_by_cve(CVE)

    assert result.nvd.value.summary == "Controlled NVD fact."
    assert result.cvss.value.base_score == 10.0
    assert result.epss.value.probability == 0.94
    assert result.cisa_kev.value.known_exploited is True
    assert [source.calls for source in readers] == [[CVE], [CVE], [CVE]]


@pytest.mark.parametrize(
    ("failed_source", "fields"),
    [
        ("nvd", ("nvd", "cvss")),
        ("epss", ("epss",)),
        ("kev", ("cisa_kev", "exploitation_evidence")),
    ],
)
def test_one_source_failure_preserves_other_available_facts(
    failed_source,
    fields,
) -> None:
    readers = {
        "nvd": ControlledReader(nvd_response()),
        "epss": ControlledReader(epss_response()),
        "kev": ControlledReader(kev_response()),
    }
    readers[failed_source] = ControlledReader(
        error=ThreatIntelligenceSourceUnavailableError("unavailable")
    )
    composite_reader = CompositeThreatIntelligenceReader(
        readers["nvd"],
        readers["epss"],
        readers["kev"],
    )

    result = composite_reader.get_by_cve(CVE)

    for field in fields:
        failed_fact = getattr(result, field)
        assert failed_fact.completeness.status == CompletenessStatus.SOURCE_UNAVAILABLE
        assert failed_fact.value is None
    if failed_source != "nvd":
        assert result.nvd.value is not None
        assert result.cvss.value is not None
    if failed_source != "epss":
        assert result.epss.value is not None
    if failed_source != "kev":
        assert result.cisa_kev.value is not None


def test_kev_catalog_absence_preserves_authoritative_false() -> None:
    reader, _ = composite(kev=kev_response(member=False))

    result = reader.get_by_cve(CVE)

    assert result.cisa_kev.completeness.status == CompletenessStatus.AVAILABLE
    assert result.cisa_kev.value.known_exploited is False


def test_epss_no_data_remains_distinct_from_provider_failure() -> None:
    no_data_reader, _ = composite(
        epss=epss_response(CompletenessStatus.NO_DATA)
    )
    failed_epss = ControlledReader(error=ThreatIntelligenceTimeoutError("timeout"))
    failed_reader = CompositeThreatIntelligenceReader(
        ControlledReader(nvd_response()),
        failed_epss,
        ControlledReader(kev_response()),
    )

    no_data = no_data_reader.get_by_cve(CVE)
    unavailable = failed_reader.get_by_cve(CVE)

    assert no_data.epss.completeness.status == CompletenessStatus.NO_DATA
    assert no_data.epss.value is None
    assert unavailable.epss.completeness.status == CompletenessStatus.SOURCE_UNAVAILABLE
    assert unavailable.epss.value is None


def test_source_provenance_and_observation_timestamps_are_preserved() -> None:
    nvd = nvd_response()
    epss = epss_response()
    kev = kev_response()
    reader, _ = composite(nvd=nvd, epss=epss, kev=kev)

    result = reader.get_by_cve(CVE)

    assert result.nvd is nvd.nvd
    assert result.cvss is nvd.cvss
    assert result.epss is epss.epss
    assert result.cisa_kev is kev.cisa_kev


def test_source_response_with_different_cve_fails_closed() -> None:
    reader, _ = composite(nvd=nvd_response(OTHER_CVE))

    with pytest.raises(ThreatIntelligenceDataError):
        reader.get_by_cve(CVE)


def test_non_authoritative_available_fact_fails_closed() -> None:
    nvd = nvd_response()
    invalid_nvd = VulnerabilityThreatIntelligence(
        cve_identifier=CVE,
        nvd=nvd.nvd,
        cvss=nvd.cvss,
        epss=epss_response().epss,
        cisa_kev=nvd.cisa_kev,
        exploitation_evidence=nvd.exploitation_evidence,
    )
    reader, _ = composite(nvd=invalid_nvd)

    with pytest.raises(ThreatIntelligenceDataError):
        reader.get_by_cve(CVE)


def test_invalid_provider_response_becomes_unavailable_without_false() -> None:
    kev_reader = ControlledReader(
        error=ThreatIntelligenceInvalidResponseError("invalid catalog")
    )
    reader = CompositeThreatIntelligenceReader(
        ControlledReader(nvd_response()),
        ControlledReader(epss_response()),
        kev_reader,
    )

    result = reader.get_by_cve(CVE)

    assert result.cisa_kev.completeness.status == CompletenessStatus.SOURCE_UNAVAILABLE
    assert result.cisa_kev.value is None


def test_contract_version_mismatch_fails_closed() -> None:
    nvd = nvd_response()
    object.__setattr__(nvd, "contract_version", "2.0")
    reader, _ = composite(nvd=nvd)

    with pytest.raises(ThreatIntelligenceDataError):
        reader.get_by_cve(CVE)


def test_composite_contract_contains_no_risk_priority_or_decision_fields() -> None:
    reader, _ = composite()

    result = reader.get_by_cve(CVE)

    assert not hasattr(result, "risk")
    assert not hasattr(result, "priority")
    assert not hasattr(result, "decision")
