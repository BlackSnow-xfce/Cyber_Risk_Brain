from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from core.decision.models import Evidence
from core.enterprise_context import ObservedAssetIdentifier
from core.explainability import ExplanationCompleteness

WEB_INCIDENT_EVIDENCE_CONTRACT_VERSION = "1.0"


class WebTelemetryRecordType(StrEnum):
    ACCESS = "access"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ApacheAccessObservation:
    client_ip: str
    http_method: str
    request_target: str
    http_version: str
    response_status: int
    response_size: int | None
    referer: str | None
    user_agent: str | None


@dataclass(frozen=True, slots=True)
class ApacheErrorObservation:
    severity: str
    module: str
    process_id: int
    client_ip: str
    source_port: int | None
    error_code: str | None
    message: str


@dataclass(frozen=True, slots=True)
class WebIncidentSourceEvidence:
    evidence: Evidence
    record_type: WebTelemetryRecordType
    observed_at: datetime
    observed_target_asset: ObservedAssetIdentifier
    observation: ApacheAccessObservation | ApacheErrorObservation
    completeness: ExplanationCompleteness

    def __post_init__(self) -> None:
        if self.observed_at.utcoffset() is None:
            raise ValueError("Web evidence timestamp must be timezone-aware.")

