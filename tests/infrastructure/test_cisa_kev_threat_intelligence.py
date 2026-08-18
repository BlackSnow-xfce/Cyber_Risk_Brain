from datetime import date, datetime, timedelta, timezone

import pytest
import requests

from application import (
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.explainability import CompletenessStatus
from core.threat_intelligence import CveIdentifier
from infrastructure import CisaKevThreatIntelligenceReader

OBSERVED_AT = datetime(2026, 8, 17, 13, 0, tzinfo=timezone.utc)
CVE = CveIdentifier("CVE-2021-44228")
OTHER_CVE = "CVE-2024-12345"


@pytest.fixture(autouse=True)
def clear_catalog_cache(monkeypatch):
    monkeypatch.setattr(
        CisaKevThreatIntelligenceReader,
        "_cached_catalog",
        None,
    )


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

    def get(self, url, headers, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "timeout": timeout}
        )
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def kev_entry(cve: str = CVE.value) -> dict[str, object]:
    return {
        "cveID": cve,
        "vendorProject": "Apache",
        "product": "Log4j2",
        "vulnerabilityName": "Controlled vulnerability",
        "dateAdded": "2021-12-10",
        "shortDescription": "Controlled description.",
        "requiredAction": "Apply updates per vendor instructions.",
        "dueDate": "2021-12-24",
        "knownRansomwareCampaignUse": "Known",
        "notes": "",
    }


def kev_catalog(*entries: dict[str, object]) -> dict[str, object]:
    vulnerabilities = list(entries or (kev_entry(),))
    return {
        "title": "CISA Known Exploited Vulnerabilities Catalog",
        "catalogVersion": "2026.08.17",
        "dateReleased": "2026-08-17T12:00:00.000Z",
        "count": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
    }


def reader(
    session: RecordingSession,
    *,
    clock=lambda: OBSERVED_AT,
    cache_ttl_seconds: float = 900,
) -> CisaKevThreatIntelligenceReader:
    return CisaKevThreatIntelligenceReader(
        timeout_seconds=15,
        session=session,
        clock=clock,
        cache_ttl_seconds=cache_ttl_seconds,
    )


def test_multiple_cves_share_one_catalog_download_across_readers() -> None:
    first_session = RecordingSession(
        ControlledResponse(kev_catalog(kev_entry(), kev_entry(OTHER_CVE)))
    )
    second_session = RecordingSession(
        ControlledResponse(kev_catalog(kev_entry(), kev_entry(OTHER_CVE)))
    )

    first = reader(first_session).get_by_cve(CVE)
    second = reader(second_session).get_by_cve(CveIdentifier(OTHER_CVE))

    assert first.cisa_kev.value.known_exploited is True
    assert second.cisa_kev.value.known_exploited is True
    assert len(first_session.calls) == 1
    assert second_session.calls == []


def test_expired_catalog_is_refreshed_deterministically() -> None:
    current = [OBSERVED_AT]
    first_session = RecordingSession(ControlledResponse(kev_catalog()))
    first = reader(
        first_session,
        clock=lambda: current[0],
        cache_ttl_seconds=60,
    )

    initial = first.get_by_cve(CVE)
    current[0] = OBSERVED_AT + timedelta(seconds=60)
    refresh_session = RecordingSession(
        ControlledResponse(kev_catalog(kev_entry(OTHER_CVE)))
    )
    refreshed = reader(
        refresh_session,
        clock=lambda: current[0],
        cache_ttl_seconds=60,
    ).get_by_cve(CVE)

    assert initial.cisa_kev.value.known_exploited is True
    assert refreshed.cisa_kev.value.known_exploited is False
    assert len(first_session.calls) == 1
    assert len(refresh_session.calls) == 1
    assert refreshed.cisa_kev.observed_at == current[0]


def test_catalog_membership_maps_authoritative_true_with_metadata() -> None:
    session = RecordingSession(ControlledResponse(kev_catalog()))

    intelligence = reader(session).get_by_cve(CVE)

    assert intelligence.cve_identifier == CVE
    assert intelligence.contract_version == "1.0"
    assert intelligence.cisa_kev.completeness.status == CompletenessStatus.AVAILABLE
    assert intelligence.cisa_kev.value.known_exploited is True
    assert intelligence.cisa_kev.value.date_added == date(2021, 12, 10)
    assert intelligence.cisa_kev.value.required_action == (
        "Apply updates per vendor instructions."
    )
    assert intelligence.cisa_kev.value.due_date == date(2021, 12, 24)
    assert intelligence.cisa_kev.observed_at == OBSERVED_AT
    assert session.calls == [
        {
            "url": (
                "https://www.cisa.gov/sites/default/files/feeds/"
                "known_exploited_vulnerabilities.json"
            ),
            "headers": {
                "Accept": "application/json",
                "User-Agent": "PredatorAI/3.0",
            },
            "timeout": 15,
        }
    ]


def test_valid_catalog_absence_maps_authoritative_false() -> None:
    intelligence = reader(
        RecordingSession(
            ControlledResponse(kev_catalog(kev_entry(OTHER_CVE)))
        )
    ).get_by_cve(CVE)

    assert intelligence.cisa_kev.completeness.status == CompletenessStatus.AVAILABLE
    assert intelligence.cisa_kev.value.known_exploited is False
    assert intelligence.cisa_kev.value.date_added is None
    assert intelligence.cisa_kev.value.required_action is None
    assert intelligence.cisa_kev.value.due_date is None


@pytest.mark.parametrize("member", [True, False])
def test_positive_and_negative_membership_have_cisa_provenance(member) -> None:
    entry = kev_entry() if member else kev_entry(OTHER_CVE)

    fact = reader(
        RecordingSession(ControlledResponse(kev_catalog(entry)))
    ).get_by_cve(CVE).cisa_kev

    assert fact.provenance.source_type == "cisa_kev"
    assert fact.provenance.source_reference == (
        "https://www.cisa.gov/sites/default/files/feeds/"
        "known_exploited_vulnerabilities.json"
        "#catalog-version=2026.08.17"
        "&date-released=2026-08-17T12%3A00%3A00.000Z"
    )


def test_cisa_kev_does_not_author_other_source_facts() -> None:
    intelligence = reader(
        RecordingSession(ControlledResponse(kev_catalog()))
    ).get_by_cve(CVE)

    for fact in (intelligence.nvd, intelligence.cvss, intelligence.epss):
        assert fact.completeness.status == CompletenessStatus.NOT_EVALUATED
        assert fact.value is None
    assert (
        intelligence.exploitation_evidence.completeness.status
        == CompletenessStatus.NOT_EVALUATED
    )
    assert intelligence.exploitation_evidence.value is None


def test_invalid_cve_identifier_is_rejected_before_provider_use() -> None:
    session = RecordingSession(ControlledResponse(kev_catalog()))

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
def test_transport_failure_never_becomes_negative_membership(error, expected) -> None:
    with pytest.raises(expected):
        reader(RecordingSession(error=error)).get_by_cve(CVE)


def test_http_error_never_becomes_negative_membership() -> None:
    with pytest.raises(ThreatIntelligenceSourceUnavailableError):
        reader(
            RecordingSession(ControlledResponse(status_code=503))
        ).get_by_cve(CVE)


@pytest.mark.parametrize(
    "document",
    [
        {},
        {
            "catalogVersion": "1",
            "dateReleased": "2026-08-17",
            "count": 1,
            "vulnerabilities": [],
        },
        kev_catalog(kev_entry(), kev_entry()),
        kev_catalog(kev_entry("not-a-cve")),
    ],
)
def test_invalid_dataset_never_becomes_negative_membership(document) -> None:
    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(ControlledResponse(document))
        ).get_by_cve(CVE)


@pytest.mark.parametrize("field", ["dateAdded", "dueDate"])
def test_invalid_kev_date_is_rejected(field) -> None:
    entry = kev_entry()
    entry[field] = "17-08-2026"

    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(ControlledResponse(kev_catalog(entry)))
        ).get_by_cve(CVE)


def test_invalid_json_never_becomes_negative_membership() -> None:
    with pytest.raises(ThreatIntelligenceInvalidResponseError):
        reader(
            RecordingSession(
                ControlledResponse(json_error=ValueError("invalid json"))
            )
        ).get_by_cve(CVE)
