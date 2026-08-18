from __future__ import annotations

from application import (
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceDataError,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceReader,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.threat_intelligence import (
    THREAT_INTELLIGENCE_CONTRACT_VERSION,
    CveIdentifier,
    IntelligenceFact,
    VulnerabilityThreatIntelligence,
)

_SOURCE_FAILURES = (
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)


class CompositeThreatIntelligenceReader:
    """Merge authoritative facts from independent source readers."""

    def __init__(
        self,
        nvd_reader: ThreatIntelligenceReader,
        epss_reader: ThreatIntelligenceReader,
        cisa_kev_reader: ThreatIntelligenceReader,
    ) -> None:
        self._nvd_reader = nvd_reader
        self._epss_reader = epss_reader
        self._cisa_kev_reader = cisa_kev_reader

    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence:
        nvd_result, nvd_failure = self._read(
            self._nvd_reader,
            cve_identifier,
        )
        epss_result, epss_failure = self._read(
            self._epss_reader,
            cve_identifier,
        )
        kev_result, kev_failure = self._read(
            self._cisa_kev_reader,
            cve_identifier,
        )

        if nvd_result is not None:
            self._validate_source_response(
                nvd_result,
                cve_identifier,
                "NVD",
                ("nvd", "cvss"),
            )
            nvd_fact = nvd_result.nvd
            cvss_fact = nvd_result.cvss
        else:
            status = (
                CompletenessStatus.SOURCE_UNAVAILABLE
                if nvd_failure is not None
                else CompletenessStatus.NO_DATA
            )
            provenance = self._failure_provenance(
                "nvd",
                nvd_failure,
            )
            nvd_fact = self._missing(status, provenance)
            cvss_fact = self._missing(status, provenance)

        if epss_result is not None:
            self._validate_source_response(
                epss_result,
                cve_identifier,
                "EPSS",
                ("epss",),
            )
            epss_fact = epss_result.epss
        else:
            status = (
                CompletenessStatus.SOURCE_UNAVAILABLE
                if epss_failure is not None
                else CompletenessStatus.NO_DATA
            )
            epss_fact = self._missing(
                status,
                self._failure_provenance("epss", epss_failure),
            )

        if kev_result is not None:
            self._validate_source_response(
                kev_result,
                cve_identifier,
                "CISA KEV",
                ("cisa_kev",),
            )
            kev_fact = kev_result.cisa_kev
            exploitation_evidence = kev_result.exploitation_evidence
        else:
            status = (
                CompletenessStatus.SOURCE_UNAVAILABLE
                if kev_failure is not None
                else CompletenessStatus.NO_DATA
            )
            provenance = self._failure_provenance(
                "cisa_kev",
                kev_failure,
            )
            kev_fact = self._missing(status, provenance)
            exploitation_evidence = self._missing(status, provenance)

        return VulnerabilityThreatIntelligence(
            cve_identifier=cve_identifier,
            nvd=nvd_fact,
            cvss=cvss_fact,
            epss=epss_fact,
            cisa_kev=kev_fact,
            exploitation_evidence=exploitation_evidence,
        )

    @staticmethod
    def _read(
        reader: ThreatIntelligenceReader,
        cve_identifier: CveIdentifier,
    ) -> tuple[VulnerabilityThreatIntelligence | None, Exception | None]:
        try:
            return reader.get_by_cve(cve_identifier), None
        except _SOURCE_FAILURES as error:
            return None, error

    @classmethod
    def _validate_source_response(
        cls,
        response: VulnerabilityThreatIntelligence,
        requested_cve: CveIdentifier,
        source_label: str,
        authoritative_fields: tuple[str, ...],
    ) -> None:
        if response.cve_identifier != requested_cve:
            raise ThreatIntelligenceDataError(
                f"{source_label} reader returned a different CVE."
            )
        if response.contract_version != THREAT_INTELLIGENCE_CONTRACT_VERSION:
            raise ThreatIntelligenceDataError(
                f"{source_label} reader returned an unsupported contract version."
            )

        source_fields = ("nvd", "cvss", "epss", "cisa_kev")
        for field in source_fields:
            if field in authoritative_fields:
                continue
            cls._require_not_evaluated(
                getattr(response, field),
                source_label,
                field,
            )
        cls._require_not_evaluated(
            response.exploitation_evidence,
            source_label,
            "exploitation_evidence",
        )

    @staticmethod
    def _require_not_evaluated(
        fact: IntelligenceFact[object],
        source_label: str,
        field: str,
    ) -> None:
        if (
            fact.value is not None
            or fact.completeness.status != CompletenessStatus.NOT_EVALUATED
        ):
            raise ThreatIntelligenceDataError(
                f"{source_label} reader exceeded source authority for {field}."
            )

    @staticmethod
    def _failure_provenance(
        source: str,
        error: Exception | None,
    ) -> ExplanationProvenance:
        reason = type(error).__name__ if error is not None else "no_data"
        return ExplanationProvenance(
            source_type=source,
            source_reference=f"{source}:source_status:{reason}",
        )

    @staticmethod
    def _missing(
        status: CompletenessStatus,
        provenance: ExplanationProvenance,
    ) -> IntelligenceFact[object]:
        return IntelligenceFact(
            value=None,
            completeness=ExplanationCompleteness(
                status=status,
                provenance=provenance,
            ),
        )
