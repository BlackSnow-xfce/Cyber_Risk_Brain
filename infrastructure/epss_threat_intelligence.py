from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

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
    CveIdentifier,
    EpssInformation,
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)


class EpssThreatIntelligenceReader:
    """Read one CVE from FIRST EPSS without evaluating its significance."""

    _EPSS_URL = "https://api.first.org/data/v1/epss"

    def __init__(
        self,
        timeout_seconds: float,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @classmethod
    def from_settings(cls) -> EpssThreatIntelligenceReader:
        import settings

        try:
            timeout = float(settings.EPSS_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            timeout = 0.0
        return cls(timeout)

    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence:
        if self._timeout_seconds <= 0:
            raise ThreatIntelligenceConfigurationError(
                "EPSS request timeout is invalid."
            )

        try:
            response = self._session.get(
                self._EPSS_URL,
                params={"cve": cve_identifier.value},
                headers={
                    "Accept": "application/json",
                    "User-Agent": "PredatorAI/3.0",
                },
                timeout=self._timeout_seconds,
            )
        except requests.Timeout:
            raise ThreatIntelligenceTimeoutError(
                "EPSS request timed out."
            ) from None
        except requests.RequestException:
            raise ThreatIntelligenceSourceUnavailableError(
                "EPSS source is unavailable."
            ) from None

        if not 200 <= response.status_code < 300:
            raise ThreatIntelligenceSourceUnavailableError(
                "EPSS source returned an error."
            )

        try:
            document = response.json()
        except ValueError:
            raise ThreatIntelligenceInvalidResponseError(
                "EPSS response is not valid JSON."
            ) from None

        retrieved_at = self._clock()
        if retrieved_at.utcoffset() is None:
            raise ThreatIntelligenceConfigurationError(
                "EPSS adapter clock must include a timezone."
            )
        return self._map_response(document, cve_identifier, retrieved_at)

    def _map_response(
        self,
        document: object,
        requested_cve: CveIdentifier,
        retrieved_at: datetime,
    ) -> VulnerabilityThreatIntelligence:
        root = self._record(document, "EPSS response")
        if root.get("status") != "OK" or root.get("status-code") != 200:
            self._invalid("EPSS response status is invalid.")
        total = root.get("total")
        data = root.get("data")
        if isinstance(total, bool) or not isinstance(total, int):
            self._invalid("EPSS response total is invalid.")
        if not isinstance(data, list):
            self._invalid("EPSS response data must be a list.")

        source_reference = f"{self._EPSS_URL}?cve={requested_cve.value}"
        if total == 0 and data == []:
            epss_fact = self._missing(
                CompletenessStatus.NO_DATA,
                self._provenance("epss", source_reference),
                retrieved_at,
            )
        else:
            if total != 1 or len(data) != 1:
                self._invalid("EPSS response did not contain exactly one CVE.")
            item = self._record(data[0], "EPSS item")
            if item.get("cve") != requested_cve.value:
                self._invalid("EPSS response returned a different CVE.")
            data_date = self._data_date(item.get("date"))
            probability = self._unit_interval(item.get("epss"), "score")
            percentile = self._unit_interval(
                item.get("percentile"),
                "percentile",
            )
            epss_fact = self._available(
                EpssInformation(
                    probability=probability,
                    percentile=percentile,
                ),
                self._provenance(
                    "epss",
                    f"{source_reference}#data-date={data_date.isoformat()}",
                ),
                retrieved_at,
            )

        return VulnerabilityThreatIntelligence(
            cve_identifier=requested_cve,
            nvd=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance("nvd", "nvd:not_evaluated_by_epss"),
            ),
            cvss=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance("nvd", "nvd:cvss_not_evaluated_by_epss"),
            ),
            epss=epss_fact,
            cisa_kev=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance(
                    "cisa_kev",
                    "cisa_kev:not_evaluated_by_epss",
                ),
            ),
            exploitation_evidence=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance(
                    "epss",
                    f"{source_reference}#exploitation-not-evaluated",
                ),
            ),
        )

    @classmethod
    def _unit_interval(cls, value: object, label: str) -> float:
        if not isinstance(value, str) or not value.strip():
            cls._invalid(f"EPSS {label} is missing.")
        try:
            parsed = Decimal(value)
        except InvalidOperation:
            cls._invalid(f"EPSS {label} is invalid.")
        if not parsed.is_finite() or not Decimal("0") <= parsed <= Decimal("1"):
            cls._invalid(f"EPSS {label} must be between 0 and 1.")
        return float(parsed)

    @classmethod
    def _data_date(cls, value: object) -> date:
        if not isinstance(value, str) or not value.strip():
            cls._invalid("EPSS data date is missing.")
        try:
            return date.fromisoformat(value)
        except ValueError:
            cls._invalid("EPSS data date is invalid.")

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
    def _missing(status, provenance, observed_at=None):
        return IntelligenceFact(
            value=None,
            completeness=ExplanationCompleteness(
                status=status,
                provenance=provenance,
            ),
            observed_at=observed_at,
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

    @staticmethod
    def _invalid(message: str):
        raise ThreatIntelligenceInvalidResponseError(message)
