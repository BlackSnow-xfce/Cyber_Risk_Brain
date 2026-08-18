from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, tzinfo
from hashlib import sha256
from ipaddress import ip_address
import re

from core.decision.models import (
    Evidence,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceType,
)
from core.enterprise_context import ObservedAssetIdentifier
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.security_observation import (
    WEB_INCIDENT_EVIDENCE_CONTRACT_VERSION,
    ApacheAccessObservation,
    ApacheErrorObservation,
    WebIncidentSourceEvidence,
    WebTelemetryRecordType,
)


@dataclass(frozen=True, slots=True)
class WebTelemetryParseResult:
    record: WebIncidentSourceEvidence | None
    completeness: ExplanationCompleteness


class ApacheWebTelemetryParser:
    """Parse the controlled DVWA Apache access and error log formats."""

    _ACCESS_PATTERN = re.compile(
        r'^(?P<client>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\S+) (?P<target>.*?) (?P<version>HTTP/\d(?:\.\d)?)" '
        r'(?P<status>\d{3}) (?P<size>\d+|-) '
        r'"(?P<referer>[^"]*)" "(?P<agent>[^"]*)"$'
    )
    _ERROR_PATTERN = re.compile(
        r'^\[(?P<timestamp>[^\]]+)\] '
        r'\[(?P<module>[^:\]]+):(?P<severity>[^\]]+)\] '
        r'\[pid (?P<pid>\d+)(?::[^\]]+)?\] '
        r'\[client (?P<client>[^\]]+)\] (?P<message>.+)$'
    )
    _ERROR_CODE_PATTERN = re.compile(r"\bAH\d{5}\b")

    def __init__(self, error_log_timezone: tzinfo = timezone.utc) -> None:
        self._error_log_timezone = error_log_timezone

    def parse_access(
        self,
        line: str,
        *,
        observed_target_asset: ObservedAssetIdentifier,
        source_reference: str,
    ) -> WebTelemetryParseResult:
        normalized = line.strip()
        match = self._ACCESS_PATTERN.fullmatch(normalized)
        if match is None:
            return self._unsupported(
                WebTelemetryRecordType.ACCESS,
                normalized,
                observed_target_asset,
                source_reference,
            )
        try:
            client_ip = str(ip_address(match.group("client")))
            observed_at = datetime.strptime(
                match.group("timestamp"),
                "%d/%b/%Y:%H:%M:%S %z",
            )
            observation = ApacheAccessObservation(
                client_ip=client_ip,
                http_method=match.group("method"),
                request_target=match.group("target"),
                http_version=match.group("version"),
                response_status=int(match.group("status")),
                response_size=(
                    None
                    if match.group("size") == "-"
                    else int(match.group("size"))
                ),
                referer=self._optional(match.group("referer")),
                user_agent=self._optional(match.group("agent")),
            )
        except (TypeError, ValueError):
            return self._unsupported(
                WebTelemetryRecordType.ACCESS,
                normalized,
                observed_target_asset,
                source_reference,
            )
        return self._available(
            WebTelemetryRecordType.ACCESS,
            normalized,
            observed_at,
            observed_target_asset,
            observation,
            source_reference,
        )

    def parse_error(
        self,
        line: str,
        *,
        observed_target_asset: ObservedAssetIdentifier,
        source_reference: str,
    ) -> WebTelemetryParseResult:
        normalized = line.strip()
        match = self._ERROR_PATTERN.fullmatch(normalized)
        if match is None:
            return self._unsupported(
                WebTelemetryRecordType.ERROR,
                normalized,
                observed_target_asset,
                source_reference,
            )
        try:
            client_ip, source_port = self._client_endpoint(
                match.group("client")
            )
            observed_at = datetime.strptime(
                match.group("timestamp"),
                "%a %b %d %H:%M:%S.%f %Y",
            ).replace(tzinfo=self._error_log_timezone)
            message = match.group("message")
            code = self._ERROR_CODE_PATTERN.search(message)
            observation = ApacheErrorObservation(
                severity=match.group("severity"),
                module=match.group("module"),
                process_id=int(match.group("pid")),
                client_ip=client_ip,
                source_port=source_port,
                error_code=code.group(0) if code is not None else None,
                message=message,
            )
        except (TypeError, ValueError):
            return self._unsupported(
                WebTelemetryRecordType.ERROR,
                normalized,
                observed_target_asset,
                source_reference,
            )
        return self._available(
            WebTelemetryRecordType.ERROR,
            normalized,
            observed_at,
            observed_target_asset,
            observation,
            source_reference,
        )

    @classmethod
    def _available(
        cls,
        record_type: WebTelemetryRecordType,
        line: str,
        observed_at: datetime,
        observed_target_asset: ObservedAssetIdentifier,
        observation: ApacheAccessObservation | ApacheErrorObservation,
        source_reference: str,
    ) -> WebTelemetryParseResult:
        digest = cls._digest(
            record_type,
            line,
            observed_target_asset,
            source_reference,
        )
        provenance_reference = f"{source_reference}#sha256={digest}"
        completeness = ExplanationCompleteness(
            status=CompletenessStatus.AVAILABLE,
            provenance=ExplanationProvenance(
                source_type="apache_dvwa_web_telemetry",
                source_reference=provenance_reference,
            ),
        )
        evidence = Evidence(
            evidence_type=EvidenceType.WEB_TELEMETRY,
            key=f"apache-{record_type.value}-observation",
            value=observation,
            source="apache_dvwa_web_telemetry",
            description="Observed Apache web telemetry without interpretation.",
            identifier=f"web-telemetry:{record_type.value}:{digest}",
            kind=EvidenceKind.SOURCE,
            provenance=EvidenceProvenance(
                source_type="apache_dvwa_web_telemetry",
                source_reference=provenance_reference,
            ),
            contract_version=WEB_INCIDENT_EVIDENCE_CONTRACT_VERSION,
        )
        return WebTelemetryParseResult(
            record=WebIncidentSourceEvidence(
                evidence=evidence,
                record_type=record_type,
                observed_at=observed_at,
                observed_target_asset=observed_target_asset,
                observation=observation,
                completeness=completeness,
            ),
            completeness=completeness,
        )

    @classmethod
    def _unsupported(
        cls,
        record_type: WebTelemetryRecordType,
        line: str,
        observed_target_asset: ObservedAssetIdentifier,
        source_reference: str,
    ) -> WebTelemetryParseResult:
        digest = cls._digest(
            record_type,
            line,
            observed_target_asset,
            source_reference,
        )
        return WebTelemetryParseResult(
            record=None,
            completeness=ExplanationCompleteness(
                status=CompletenessStatus.NO_DATA,
                provenance=ExplanationProvenance(
                    source_type="apache_dvwa_web_telemetry",
                    source_reference=(
                        f"{source_reference}#unsupported-sha256={digest}"
                    ),
                ),
            ),
        )

    @staticmethod
    def _client_endpoint(value: str) -> tuple[str, int | None]:
        host, separator, raw_port = value.rpartition(":")
        if not separator:
            return str(ip_address(value)), None
        client_ip = str(ip_address(host))
        port = int(raw_port)
        if not 0 < port <= 65535:
            raise ValueError("Apache client source port is invalid.")
        return client_ip, port

    @staticmethod
    def _optional(value: str) -> str | None:
        return None if value in ("", "-") else value

    @staticmethod
    def _digest(
        record_type: WebTelemetryRecordType,
        line: str,
        observed_target_asset: ObservedAssetIdentifier,
        source_reference: str,
    ) -> str:
        identity = "\n".join(
            (
                WEB_INCIDENT_EVIDENCE_CONTRACT_VERSION,
                record_type.value,
                source_reference,
                observed_target_asset.identifier_type.value,
                observed_target_asset.value,
                line,
            )
        )
        return sha256(identity.encode("utf-8")).hexdigest()

