from datetime import datetime, timezone

import pytest
import requests

from application import (
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.explainability import CompletenessStatus
from core.threat_intelligence import CveIdentifier
from infrastructure import EpssThreatIntelligenceReader

OBSERVED_AT = datetime(2026, 8, 17, 12, 0, tzinfo=timezone.utc)
CVE = CveIdentifier("CVE-2021-44228")


class ControlledResponse:
    def __init__(
        self,
        document: object | None = None,
        status_code: int = 200,
        json_error: ValueError | None = None,
    ) -> None:
        self.document = document
        self.status_code = status_code
        self.json_error = json_error

    def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.document


class RecordingSession:
    def __init__(
        self,
        response: ControlledResponse | None = None,
        error: requests.RequestException | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, object]] = []

    def get(self, url, params, headers, timeout):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def epss_document(
    epss: str = "0.943580000",
    percentile: str = "0.999540000",
) -> dict[str, object]:
    return {
        "status": "OK",
        "status-code": 200,
        "version": "1.0",
        "total": 1,
        "data": [
            {
                "cve": CVE.value,
                "epss": epss,
                "percentile": percentile,
                "date": "2026-08-17",
            }
        ],
    }


def reader(session: RecordingSession) -> EpssThreatIntelligenceReader:
    return EpssThreatIntelligenceReader(
        timeout_seconds=12,
        session=session,
        clock=lambda: OBSERVED_AT,
    )


def test_known_cve_maps_epss_score_percentile_and_provenance() -> None:
    session = RecordingSession(ControlledResponse(epss_document()))

    intelligence = reader(session).get_by_cve(CVE)

    assert intelligence.cve_identifier == CVE
    assert intelligence.contract_version == "1.0"
    assert intelligence.epss.value.probability == 0.94358
    assert intelligence.epss.value.percentile == 0.99954
    assert intelligence.epss.observed_at == OBSERVED_AT
    assert intelligence.epss.provenance.source_type == "epss"
    assert intelligence.epss.provenance.source_reference == (
        "https://api.first.org/data/v1/epss?cve=CVE-2021-44228"
        "#data-date=2026-08-17"
    )
    assert session.calls == [
        {
            "url": "https://api.first.org/data/v1/epss",
            "params": {"cve": "CVE-2021-44228"},
            "headers": {
                "Accept": "application/json",
                "User-Agent": "PredatorAI/3.0",
            },
            "timeout": 12,
        }
    ]


def test_provider_zero_is_preserved_as_a_real_epss_value() -> None:
    intelligence = reader(
        RecordingSession(ControlledResponse(epss_document("0", "0")))
    ).get_by_cve(CVE)

    assert intelligence.epss.value.probability == 0
    assert intelligence.epss.value.percentile == 0


def test_epss_does_not_author_other_source_facts() -> None:
    intelligence = reader(
        RecordingSession(ControlledResponse(epss_document()))
    ).get_by_cve(CVE)

    for fact in (intelligence.nvd, intelligence.cvss):
        assert fact.completeness.status == CompletenessStatus.NOT_EVALUATED
        assert fact.value is None
        assert fact.provenance.source_type == "nvd"
    assert (
        intelligence.cisa_kev.completeness.status
        == CompletenessStatus.NOT_EVALUATED
    )
    assert intelligence.cisa_kev.value is None
    assert (
        intelligence.exploitation_evidence.completeness.status
        == CompletenessStatus.NOT_EVALUATED
    )
    assert intelligence.exploitation_evidence.value is None


def test_cve_without_epss_data_is_explicit_no_data() -> None:
    document = {
        "status": "OK",
        "status-code": 200,
        "version": "1.0",
        "total": 0,
        "data": [],
    }

    intelligence = reader(
        RecordingSession(ControlledResponse(document))
    ).get_by_cve(CVE)

    assert intelligence.epss.completeness.status == CompletenessStatus.NO_DATA
    assert intelligence.epss.value is None
    assert intelligence.epss.observed_at == OBSERVED_AT


def test_invalid_cve_identifier_is_rejected_before_provider_use() -> None:
    session = RecordingSession(ControlledResponse(epss_document()))

    with pytest.raises(ValueError):
        CveIdentifier("not-a-cve")

    assert session.calls == []


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (requests.Timeout(), ThreatIntelligenceTimeoutError),
        (requests.ConnectionError(), ThreatIntelligenceSourceUnavailableError),
    ],
)
def test_transport_failures_remain_controlled(error, expected) -> None:
    with pytest.raises(expected):
        reader(RecordingSession(error=error)).get_by_cve(CVE)


def test_provider_http_error_is_not_mapped_to_no_data() -> None:
    with pytest.raises(ThreatIntelligenceSourceUnavailableError):
        reader(
            RecordingSession(ControlledResponse(status_code=503))
        ).get_by_cve(CVE)


@pytest.mark.parametrize(
    "document",
    [
        {"status": "ERROR", "status-code": 200, "total": 0, "data": []},
        {"status": "OK", "status-code": 200, "total": 1, "data": []},
        {
            "status": "OK",
            "status-code": 200,
            "total": 1,
            "data": [
                {
                    "cve": "CVE-2021-99999",
                    "epss": "0.5",
                    "percentile": "0.6",
                    "date": "2026-08-17",
                }
            ],
        },
    ],
)
def test_unexpected_provider_response_is_rejected(document) -> None:
    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(ControlledResponse(document))
        ).get_by_cve(CVE)


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(
                ControlledResponse(json_error=ValueError("invalid json"))
            )
        ).get_by_cve(CVE)


@pytest.mark.parametrize(
    ("epss", "percentile"),
    [
        ("-0.01", "0.5"),
        ("1.01", "0.5"),
        ("NaN", "0.5"),
        ("not-a-number", "0.5"),
        ("0.5", "-0.01"),
        ("0.5", "1.01"),
        ("0.5", "Infinity"),
    ],
)
def test_invalid_numeric_values_are_rejected(epss, percentile) -> None:
    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(
                ControlledResponse(epss_document(epss, percentile))
            )
        ).get_by_cve(CVE)


@pytest.mark.parametrize("data_date", [None, "", "17-08-2026"])
def test_invalid_data_date_is_rejected(data_date) -> None:
    document = epss_document()
    document["data"][0]["date"] = data_date

    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(ControlledResponse(document))
        ).get_by_cve(CVE)
