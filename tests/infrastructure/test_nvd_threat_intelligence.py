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
from infrastructure import NvdThreatIntelligenceReader

OBSERVED_AT = datetime(2026, 8, 17, 10, 0, tzinfo=timezone.utc)
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


def nvd_document() -> dict[str, object]:
    return {
        "resultsPerPage": 1,
        "startIndex": 0,
        "totalResults": 1,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2026-08-17T10:00:00.000",
        "vulnerabilities": [
            {
                "cve": {
                    "id": CVE.value,
                    "published": "2021-12-10T10:15:09.143",
                    "lastModified": "2025-10-27T14:42:07.050",
                    "descriptions": [
                        {"lang": "es", "value": "Descripción controlada."},
                        {"lang": "en", "value": "Controlled NVD description."},
                    ],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "source": "nvd@nist.gov",
                                "type": "Primary",
                                "cvssData": {
                                    "version": "3.1",
                                    "vectorString": (
                                        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
                                    ),
                                    "baseScore": 10.0,
                                    "baseSeverity": "CRITICAL",
                                },
                            }
                        ]
                    },
                }
            }
        ],
    }


def reader(session: RecordingSession) -> NvdThreatIntelligenceReader:
    return NvdThreatIntelligenceReader(
        api_key=None,
        timeout_seconds=12,
        session=session,
        clock=lambda: OBSERVED_AT,
    )


def test_known_cve_maps_nvd_and_cvss_with_real_source_provenance() -> None:
    session = RecordingSession(ControlledResponse(nvd_document()))

    intelligence = reader(session).get_by_cve(CVE)

    assert intelligence is not None
    assert intelligence.cve_identifier == CVE
    assert intelligence.nvd.value.summary == "Controlled NVD description."
    assert intelligence.nvd.value.published_at == datetime(
        2021,
        12,
        10,
        10,
        15,
        9,
        143000,
        tzinfo=timezone.utc,
    )
    assert intelligence.nvd.observed_at == OBSERVED_AT
    assert intelligence.nvd.provenance.source_type == "nvd"
    assert intelligence.nvd.provenance.source_reference.endswith(
        "?cveId=CVE-2021-44228"
    )
    assert "cveIds" not in intelligence.nvd.provenance.source_reference
    assert intelligence.cvss.value.version == "3.1"
    assert intelligence.cvss.value.base_score == 10.0
    assert intelligence.cvss.value.severity == "CRITICAL"
    assert intelligence.cvss.provenance.source_type == "nvd"
    assert session.calls == [
        {
            "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
            "params": {"cveId": "CVE-2021-44228"},
            "headers": {
                "Accept": "application/json",
                "User-Agent": "PredatorAI/3.0",
            },
            "timeout": 12,
        }
    ]


def test_nvd_does_not_author_epss_kev_or_exploitation_evidence() -> None:
    intelligence = reader(
        RecordingSession(ControlledResponse(nvd_document()))
    ).get_by_cve(CVE)

    assert intelligence is not None
    assert intelligence.epss.completeness.status == CompletenessStatus.NOT_EVALUATED
    assert intelligence.epss.value is None
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


def test_valid_unknown_cve_returns_no_record() -> None:
    document = {"totalResults": 0, "vulnerabilities": []}

    assert reader(
        RecordingSession(ControlledResponse(document))
    ).get_by_cve(CVE) is None


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
    "response",
    [
        ControlledResponse(json_error=ValueError("invalid json")),
        ControlledResponse({"totalResults": 1, "vulnerabilities": []}),
        ControlledResponse(
            {
                "totalResults": 1,
                "vulnerabilities": [{"cve": {"id": "CVE-2021-99999"}}],
            }
        ),
    ],
)
def test_invalid_provider_response_is_rejected(response) -> None:
    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(RecordingSession(response)).get_by_cve(CVE)
