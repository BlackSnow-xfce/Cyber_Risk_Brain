from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

import api_app
from application import ThreatIntelligenceQueryService
from application import (
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
    CveIdentifier,
    EpssInformation,
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)


def fact(value, status: CompletenessStatus, source: str):
    return IntelligenceFact(
        value=value,
        completeness=ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type=source,
                source_reference=f"{source}:CVE-2026-12345",
            ),
        ),
        observed_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
    )


class StubReader:
    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence:
        return VulnerabilityThreatIntelligence(
            cve_identifier=cve_identifier,
            nvd=fact(None, CompletenessStatus.NO_DATA, "nvd"),
            cvss=fact(None, CompletenessStatus.NOT_EVALUATED, "nvd"),
            epss=fact(
                EpssInformation(probability=0.42, percentile=0.73),
                CompletenessStatus.AVAILABLE,
                "epss",
            ),
            cisa_kev=fact(
                None,
                CompletenessStatus.SOURCE_UNAVAILABLE,
                "cisa_kev",
            ),
            exploitation_evidence=fact(
                None,
                CompletenessStatus.NO_DATA,
                "cisa_kev",
            ),
        )


def test_endpoint_projects_availability_and_provenance_without_sentinels() -> None:
    response = api_app.vulnerability_threat_intelligence(
        "CVE-2026-12345",
        ThreatIntelligenceQueryService(StubReader()),
    )
    payload = response.model_dump(mode="json")

    assert payload["contract_version"] == "1.0"
    assert payload["cve_identifier"] == "CVE-2026-12345"
    assert payload["nvd"]["status"] == "no_data"
    assert payload["nvd"]["value"] is None
    assert payload["epss"]["value"]["probability"] == 0.42
    assert payload["epss"]["provenance"] == {
        "source_type": "epss",
        "source_reference": "epss:CVE-2026-12345",
    }
    assert payload["cisa_kev"]["status"] == "source_unavailable"
    assert payload["cisa_kev"]["value"] is None


def test_endpoint_is_controlled_when_no_reader_is_configured() -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.vulnerability_threat_intelligence(
            "CVE-2026-12345",
            ThreatIntelligenceQueryService(None),
        )

    assert captured.value.status_code == 503
    assert captured.value.detail == "Threat intelligence source is not configured."


class ErrorService:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def get_by_cve(self, cve_identifier: str):
        raise self.error


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (ThreatIntelligenceTimeoutError("timeout"), 504),
        (ThreatIntelligenceSourceUnavailableError("unavailable"), 503),
        (ThreatIntelligenceInvalidResponseError("invalid"), 502),
        (ValueError("invalid CVE"), 422),
    ],
)
def test_endpoint_maps_nvd_failures_without_fallback(error, status_code) -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.vulnerability_threat_intelligence(
            "CVE-2021-44228",
            ErrorService(error),
        )

    assert captured.value.status_code == status_code


def test_productive_dependency_uses_composite_reader(monkeypatch) -> None:
    controlled_reader = StubReader()
    source_readers = {
        "nvd_reader": object(),
        "epss_reader": object(),
        "cisa_kev_reader": object(),
    }
    captured = {}

    monkeypatch.setattr(
        api_app.NvdThreatIntelligenceReader,
        "from_settings",
        lambda: source_readers["nvd_reader"],
    )
    monkeypatch.setattr(
        api_app.EpssThreatIntelligenceReader,
        "from_settings",
        lambda: source_readers["epss_reader"],
    )
    monkeypatch.setattr(
        api_app.CisaKevThreatIntelligenceReader,
        "from_settings",
        lambda: source_readers["cisa_kev_reader"],
    )

    def composite_factory(**readers):
        captured.update(readers)
        return controlled_reader

    monkeypatch.setattr(
        api_app,
        "CompositeThreatIntelligenceReader",
        composite_factory,
    )

    service = api_app.get_threat_intelligence_query_service()
    response = api_app.vulnerability_threat_intelligence(
        "CVE-2026-12345",
        service,
    )

    assert response.cve_identifier == "CVE-2026-12345"
    assert captured == source_readers


def test_endpoint_rejects_invalid_cve_before_calling_reader() -> None:
    class FailingReader:
        def get_by_cve(self, cve_identifier):
            raise AssertionError("Reader must not be called for an invalid CVE.")

    with pytest.raises(HTTPException) as captured:
        api_app.vulnerability_threat_intelligence(
            "not-a-cve",
            ThreatIntelligenceQueryService(FailingReader()),
        )

    assert captured.value.status_code == 422
