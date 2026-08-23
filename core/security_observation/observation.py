from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from core.ai_authorization import AIResourceReference


SECURITY_OBSERVATION_CONTRACT_VERSION = "1.0"


class SecurityObservationType(StrEnum):
    NETWORK_TRAFFIC = "network_traffic"
    PROCESS_ACTIVITY = "process_activity"
    FILE_ACTIVITY = "file_activity"
    AUTHENTICATION_ACTIVITY = "authentication_activity"
    OTHER = "other"


class SecurityObservationCollectionMethod(StrEnum):
    PACKET_CAPTURE = "packet_capture"
    SENSOR = "sensor"
    PRODUCER_ATTESTATION = "producer_attestation"
    OTHER = "other"


class SecurityObservationIndependence(StrEnum):
    INDEPENDENT_SENSOR = "independent_sensor"
    TARGET_SIDE = "target_side"
    DIRECT_SOURCE = "direct_source"
    SELF_ATTESTED = "self_attested"


@dataclass(frozen=True, slots=True)
class SecurityObservationProvenance:
    """Immutable provenance for a signal, not a confirmation record."""

    source_type: str
    source_reference: str
    raw_observation_reference: str | None = None

    def __post_init__(self) -> None:
        self._required(self.source_type, "source_type")
        self._required(self.source_reference, "source_reference")
        if self.raw_observation_reference is not None:
            self._required(
                self.raw_observation_reference,
                "raw_observation_reference",
            )

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must not be empty.")


@dataclass(frozen=True, slots=True)
class SecurityObservation:
    """A directly collected, provenance-bound security signal."""

    observation_id: str
    observation_type: SecurityObservationType
    observed_at: datetime
    target_resource: AIResourceReference
    source_identity: str
    collection_method: SecurityObservationCollectionMethod
    independence: SecurityObservationIndependence
    provenance: SecurityObservationProvenance
    contract_version: str = SECURITY_OBSERVATION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        self._required(self.observation_id, "observation_id")
        if not isinstance(self.observation_type, SecurityObservationType):
            raise ValueError("observation_type must be canonical.")
        if not isinstance(self.observed_at, datetime):
            raise ValueError("observed_at must be a datetime.")
        if self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware.")
        if not isinstance(self.target_resource, AIResourceReference):
            raise ValueError("target_resource must be an AIResourceReference.")
        self._required(self.source_identity, "source_identity")
        if not isinstance(
            self.collection_method,
            SecurityObservationCollectionMethod,
        ):
            raise ValueError("collection_method must be canonical.")
        if not isinstance(self.independence, SecurityObservationIndependence):
            raise ValueError("independence must be canonical.")
        if not isinstance(self.provenance, SecurityObservationProvenance):
            raise ValueError("provenance must be canonical.")
        if self.contract_version != SECURITY_OBSERVATION_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be "
                f"{SECURITY_OBSERVATION_CONTRACT_VERSION}."
            )

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must not be empty.")
