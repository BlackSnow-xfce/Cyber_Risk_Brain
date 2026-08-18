from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

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
    CvssInformation,
    IntelligenceFact,
    NvdIntelligence,
    VulnerabilityThreatIntelligence,
)


class NvdThreatIntelligenceReader:
    _CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    _NVD_CVSS_SOURCE = "nvd@nist.gov"
    _CVSS_METRIC_KEYS = (
        "cvssMetricV40",
        "cvssMetricV31",
        "cvssMetricV30",
        "cvssMetricV2",
    )

    def __init__(
        self,
        api_key: str | None,
        timeout_seconds: float,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._api_key = api_key.strip() if api_key and api_key.strip() else None
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @classmethod
    def from_settings(cls) -> NvdThreatIntelligenceReader:
        import settings

        try:
            timeout = float(settings.NVD_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            timeout = 0.0
        return cls(settings.NVD_API_KEY, timeout)

    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence | None:
        if self._timeout_seconds <= 0:
            raise ThreatIntelligenceConfigurationError(
                "NVD request timeout is invalid."
            )

        headers = {
            "Accept": "application/json",
            "User-Agent": "PredatorAI/3.0",
        }
        if self._api_key is not None:
            headers["apiKey"] = self._api_key

        try:
            response = self._session.get(
                self._CVE_URL,
                params={"cveId": cve_identifier.value},
                headers=headers,
                timeout=self._timeout_seconds,
            )
        except requests.Timeout:
            raise ThreatIntelligenceTimeoutError(
                "NVD request timed out."
            ) from None
        except requests.RequestException:
            raise ThreatIntelligenceSourceUnavailableError(
                "NVD source is unavailable."
            ) from None

        if not 200 <= response.status_code < 300:
            raise ThreatIntelligenceSourceUnavailableError(
                "NVD source returned an error."
            )

        try:
            document = response.json()
        except ValueError:
            raise ThreatIntelligenceInvalidResponseError(
                "NVD response is not valid JSON."
            ) from None

        observed_at = self._clock()
        if observed_at.utcoffset() is None:
            raise ThreatIntelligenceConfigurationError(
                "NVD adapter clock must include a timezone."
            )
        return self._map_response(document, cve_identifier, observed_at)

    def _map_response(
        self,
        document: object,
        requested_cve: CveIdentifier,
        observed_at: datetime,
    ) -> VulnerabilityThreatIntelligence | None:
        root = self._record(document, "NVD response")
        total_results = root.get("totalResults")
        vulnerabilities = root.get("vulnerabilities")
        if not isinstance(total_results, int) or not isinstance(
            vulnerabilities,
            list,
        ):
            self._invalid("NVD response has an invalid result envelope.")
        if total_results == 0 and vulnerabilities == []:
            return None
        if total_results != 1 or len(vulnerabilities) != 1:
            self._invalid("NVD response did not contain exactly one CVE.")

        vulnerability = self._record(
            vulnerabilities[0],
            "NVD vulnerability",
        )
        cve = self._record(vulnerability.get("cve"), "NVD CVE")
        returned_cve = cve.get("id")
        if returned_cve != requested_cve.value:
            self._invalid("NVD response returned a different CVE.")

        source_reference = (
            f"{self._CVE_URL}?cveId={requested_cve.value}"
        )
        nvd_provenance = self._provenance("nvd", source_reference)
        published_at = self._timestamp(cve.get("published"), "published")
        last_modified_at = self._timestamp(
            cve.get("lastModified"),
            "lastModified",
        )
        nvd_fact = self._available(
            NvdIntelligence(
                summary=self._english_description(cve),
                published_at=published_at,
                last_modified_at=last_modified_at,
            ),
            nvd_provenance,
            observed_at,
        )

        cvss = self._nvd_cvss(cve)
        cvss_fact = (
            self._available(
                cvss,
                self._provenance(
                    "nvd",
                    f"{source_reference}#cvss-{cvss.version}",
                ),
                observed_at,
            )
            if cvss is not None
            else self._missing(
                CompletenessStatus.NO_DATA,
                nvd_provenance,
                observed_at,
            )
        )

        return VulnerabilityThreatIntelligence(
            cve_identifier=requested_cve,
            nvd=nvd_fact,
            cvss=cvss_fact,
            epss=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance("epss", "epss:not_evaluated_by_nvd"),
            ),
            cisa_kev=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance(
                    "cisa_kev",
                    "cisa_kev:not_evaluated_by_nvd",
                ),
            ),
            exploitation_evidence=self._missing(
                CompletenessStatus.NOT_EVALUATED,
                self._provenance(
                    "nvd",
                    f"{source_reference}#exploitation-not-evaluated",
                ),
            ),
        )

    def _nvd_cvss(self, cve: dict[str, object]) -> CvssInformation | None:
        metrics = cve.get("metrics")
        if metrics is None:
            return None
        metrics_record = self._record(metrics, "NVD metrics")

        for metric_key in self._CVSS_METRIC_KEYS:
            metric_items = metrics_record.get(metric_key)
            if metric_items is None:
                continue
            if not isinstance(metric_items, list):
                self._invalid("NVD CVSS metrics must be a list.")
            for metric_item in metric_items:
                metric = self._record(metric_item, "NVD CVSS metric")
                if metric.get("source") != self._NVD_CVSS_SOURCE:
                    continue
                cvss_data = self._record(
                    metric.get("cvssData"),
                    "NVD CVSS data",
                )
                version = self._required_string(cvss_data, "version")
                vector = self._required_string(cvss_data, "vectorString")
                base_score = cvss_data.get("baseScore")
                if not isinstance(base_score, (int, float)):
                    self._invalid("NVD CVSS base score is invalid.")
                severity = cvss_data.get("baseSeverity")
                if severity is None:
                    severity = metric.get("baseSeverity")
                if severity is not None and not isinstance(severity, str):
                    self._invalid("NVD CVSS severity is invalid.")
                return CvssInformation(
                    version=version,
                    base_score=float(base_score),
                    vector=vector,
                    severity=severity,
                )
        return None

    def _english_description(self, cve: dict[str, object]) -> str | None:
        descriptions = cve.get("descriptions")
        if descriptions is None:
            return None
        if not isinstance(descriptions, list):
            self._invalid("NVD descriptions must be a list.")
        for item in descriptions:
            description = self._record(item, "NVD description")
            if description.get("lang") == "en":
                return self._required_string(description, "value")
        return None

    def _timestamp(self, value: object, field: str) -> datetime:
        if not isinstance(value, str) or not value.strip():
            self._invalid(f"NVD {field} timestamp is missing.")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            self._invalid(f"NVD {field} timestamp is invalid.")
        if parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

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

    @classmethod
    def _required_string(cls, record: dict[str, object], key: str) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            cls._invalid(f"NVD {key} must be a non-empty string.")
        return value.strip()

    @staticmethod
    def _invalid(message: str):
        raise ThreatIntelligenceInvalidResponseError(message)
