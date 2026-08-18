from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from threading import RLock
from types import MappingProxyType
from typing import Mapping
from urllib.parse import quote

import requests

from application import (
    ThreatIntelligenceConfigurationError,
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
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)


@dataclass(frozen=True, slots=True)
class _CisaKevCatalog:
    entries: Mapping[CveIdentifier, CisaKevInformation]
    source_reference: str
    retrieved_at: datetime


class CisaKevThreatIntelligenceReader:
    """Read authoritative CVE membership from the official CISA KEV catalog."""

    _CATALOG_URL = (
        "https://www.cisa.gov/sites/default/files/feeds/"
        "known_exploited_vulnerabilities.json"
    )
    _cache_lock = RLock()
    _cached_catalog: _CisaKevCatalog | None = None

    def __init__(
        self,
        timeout_seconds: float,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
        cache_ttl_seconds: float = 900,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._cache_ttl_seconds = cache_ttl_seconds

    @classmethod
    def from_settings(cls) -> CisaKevThreatIntelligenceReader:
        import settings

        try:
            timeout = float(settings.CISA_KEV_TIMEOUT_SECONDS)
            cache_ttl = float(settings.CISA_KEV_CACHE_TTL_SECONDS)
        except (TypeError, ValueError):
            timeout = 0.0
            cache_ttl = 0.0
        return cls(timeout, cache_ttl_seconds=cache_ttl)

    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence:
        if self._timeout_seconds <= 0 or self._cache_ttl_seconds <= 0:
            raise ThreatIntelligenceConfigurationError(
                "CISA KEV timeout or cache TTL is invalid."
            )

        catalog = self._catalog()
        return self._map_catalog(catalog, cve_identifier)

    def _catalog(self) -> _CisaKevCatalog:
        requested_at = self._now()
        with self._cache_lock:
            cached = type(self)._cached_catalog
            if (
                cached is not None
                and requested_at - cached.retrieved_at
                < timedelta(seconds=self._cache_ttl_seconds)
            ):
                return cached

            catalog = self._download_catalog(requested_at)
            type(self)._cached_catalog = catalog
            return catalog

    def _download_catalog(self, retrieved_at: datetime) -> _CisaKevCatalog:

        try:
            response = self._session.get(
                self._CATALOG_URL,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "PredatorAI/3.0",
                },
                timeout=self._timeout_seconds,
            )
        except requests.Timeout:
            raise ThreatIntelligenceTimeoutError(
                "CISA KEV request timed out."
            ) from None
        except requests.RequestException:
            raise ThreatIntelligenceSourceUnavailableError(
                "CISA KEV source is unavailable."
            ) from None

        if not 200 <= response.status_code < 300:
            raise ThreatIntelligenceSourceUnavailableError(
                "CISA KEV source returned an error."
            )

        try:
            document = response.json()
        except ValueError:
            raise ThreatIntelligenceInvalidResponseError(
                "CISA KEV response is not valid JSON."
            ) from None

        return self._parse_catalog(document, retrieved_at)

    def _parse_catalog(
        self,
        document: object,
        retrieved_at: datetime,
    ) -> _CisaKevCatalog:
        catalog = self._record(document, "CISA KEV catalog")
        catalog_version = self._required_string(catalog, "catalogVersion")
        date_released = self._required_string(catalog, "dateReleased")
        count = catalog.get("count")
        vulnerabilities = catalog.get("vulnerabilities")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            self._invalid("CISA KEV catalog count is invalid.")
        if not isinstance(vulnerabilities, list) or count != len(vulnerabilities):
            self._invalid("CISA KEV catalog entries do not match its count.")

        entries: dict[CveIdentifier, CisaKevInformation] = {}
        for raw_entry in vulnerabilities:
            entry = self._record(raw_entry, "CISA KEV entry")
            cve_value = self._required_string(entry, "cveID")
            try:
                cve_identifier = CveIdentifier(cve_value)
            except ValueError:
                self._invalid("CISA KEV catalog contains an invalid CVE.")
            if cve_identifier in entries:
                self._invalid("CISA KEV catalog contains a duplicate CVE.")
            entries[cve_identifier] = CisaKevInformation(
                known_exploited=True,
                date_added=self._date(entry, "dateAdded"),
                required_action=self._required_string(
                    entry,
                    "requiredAction",
                ),
                due_date=self._date(entry, "dueDate"),
            )

        source_reference = (
            f"{self._CATALOG_URL}"
            f"#catalog-version={quote(catalog_version, safe='')}"
            f"&date-released={quote(date_released, safe='')}"
        )
        return _CisaKevCatalog(
            entries=MappingProxyType(entries),
            source_reference=source_reference,
            retrieved_at=retrieved_at,
        )

    def _map_catalog(
        self,
        catalog: _CisaKevCatalog,
        requested_cve: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence:
        kev_value = catalog.entries.get(
            requested_cve,
            CisaKevInformation(known_exploited=False),
        )
        kev_fact = self._available(
            kev_value,
            self._provenance("cisa_kev", catalog.source_reference),
            catalog.retrieved_at,
        )

        return VulnerabilityThreatIntelligence(
            cve_identifier=requested_cve,
            nvd=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance("nvd", "nvd:not_evaluated_by_cisa_kev"),
            ),
            cvss=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance(
                    "nvd",
                    "nvd:cvss_not_evaluated_by_cisa_kev",
                ),
            ),
            epss=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance("epss", "epss:not_evaluated_by_cisa_kev"),
            ),
            cisa_kev=kev_fact,
            exploitation_evidence=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance(
                    "cisa_kev",
                    f"{catalog.source_reference}"
                    "&exploitation-evidence=not-evaluated",
                ),
            ),
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.utcoffset() is None:
            raise ThreatIntelligenceConfigurationError(
                "CISA KEV adapter clock must include a timezone."
            )
        return value

    @classmethod
    def _date(cls, entry: dict[str, object], key: str) -> date:
        value = cls._required_string(entry, key)
        try:
            return date.fromisoformat(value)
        except ValueError:
            cls._invalid(f"CISA KEV {key} is invalid.")

    @staticmethod
    def _available(value, provenance, observed_at):
        return IntelligenceFact(
            value=value,
            completeness=ExplanationCompleteness(
                status=CompletenessStatus.AVAILABLE,
                provenance=provenance,
            ),
            observed_at=observed_at,
        )

    @staticmethod
    def _missing(status, provenance):
        return IntelligenceFact(
            value=None,
            completeness=ExplanationCompleteness(
                status=status,
                provenance=provenance,
            ),
        )

    @staticmethod
    def _provenance(
        source_type: str,
        source_reference: str,
    ) -> ExplanationProvenance:
        return ExplanationProvenance(
            source_type=source_type,
            source_reference=source_reference,
        )

    @classmethod
    def _record(cls, value: object, label: str) -> dict[str, object]:
        if not isinstance(value, dict):
            cls._invalid(f"{label} must be an object.")
        return value

    @classmethod
    def _required_string(cls, record: dict[str, object], key: str) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            cls._invalid(f"CISA KEV {key} must be a non-empty string.")
        return value.strip()

    @staticmethod
    def _invalid(message: str):
        raise ThreatIntelligenceInvalidResponseError(message)
