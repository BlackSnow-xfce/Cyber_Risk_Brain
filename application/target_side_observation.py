from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.security_observation_creation import (
    SecurityObservationCreationBoundary,
    SecurityObservationCreationError,
    SecurityObservationInput,
)
from core.ai_authorization import AIResourceReference, AIResourceType
from core.security_observation import (
    SecurityObservation,
    SecurityObservationType,
)


TARGET_SIDE_DISTCC_PRODUCER_ID = "target-side-tcpdump"
TARGET_SIDE_DISTCC_PROTOCOL = "TCP"
TARGET_SIDE_DISTCC_PORT = 3632


class TargetSideObservationAdapterError(ValueError):
    """Raised when a controlled target-side runtime signal is invalid."""


@dataclass(frozen=True, slots=True)
class TargetSideRuntimeSignal:
    """Minimal parsed signal; it is not a trusted observation."""

    producer_id: str
    observed_at: datetime
    target_identifier: str
    target_resource: AIResourceReference
    protocol: str
    destination_port: int
    source_reference: str
    raw_observation_reference: str | None = None

    def __post_init__(self) -> None:
        self._required(self.producer_id, "producer_id")
        if not isinstance(self.observed_at, datetime):
            raise TargetSideObservationAdapterError(
                "observed_at must be a datetime."
            )
        if self.observed_at.utcoffset() is None:
            raise TargetSideObservationAdapterError(
                "observed_at must be timezone-aware."
            )
        self._required(self.target_identifier, "target_identifier")
        if not isinstance(self.target_resource, AIResourceReference):
            raise TargetSideObservationAdapterError(
                "target_resource must be an AIResourceReference."
            )
        if not isinstance(self.protocol, str) or self.protocol.upper() != TARGET_SIDE_DISTCC_PROTOCOL:
            raise TargetSideObservationAdapterError(
                "Only TCP runtime signals are supported."
            )
        if not isinstance(self.destination_port, int) or not (
            1 <= self.destination_port <= 65535
        ):
            raise TargetSideObservationAdapterError(
                "destination_port must be a valid TCP port."
            )
        self._required(self.source_reference, "source_reference")
        if self.raw_observation_reference is not None:
            self._required(
                self.raw_observation_reference,
                "raw_observation_reference",
            )

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise TargetSideObservationAdapterError(f"{label} must not be empty.")


class TargetSideRuntimeObservationAdapter:
    """Translate one controlled signal and delegate trust assignment."""

    def __init__(
        self,
        creation_boundary: SecurityObservationCreationBoundary,
        *,
        expected_producer_id: str = TARGET_SIDE_DISTCC_PRODUCER_ID,
        expected_target_identifier: str = "172.18.0.19",
        expected_target_resource: AIResourceReference,
        expected_port: int = TARGET_SIDE_DISTCC_PORT,
    ) -> None:
        if not isinstance(creation_boundary, SecurityObservationCreationBoundary):
            raise TargetSideObservationAdapterError(
                "creation_boundary must be authoritative."
            )
        if not expected_producer_id.strip() or not expected_target_identifier.strip():
            raise TargetSideObservationAdapterError(
                "Target-side adapter binding must be explicit."
            )
        if not isinstance(expected_target_resource, AIResourceReference):
            raise TargetSideObservationAdapterError(
                "expected_target_resource must be canonical."
            )
        if expected_target_resource.resource_type is not AIResourceType.ASSET:
            raise TargetSideObservationAdapterError(
                "Target-side runtime observations require an asset resource."
            )
        if expected_port != TARGET_SIDE_DISTCC_PORT:
            raise TargetSideObservationAdapterError(
                "Only the controlled DistCC port is supported."
            )
        self._creation_boundary = creation_boundary
        self._expected_producer_id = expected_producer_id
        self._expected_target_identifier = expected_target_identifier
        self._expected_target_resource = expected_target_resource
        self._expected_port = expected_port

    def to_input(self, signal: TargetSideRuntimeSignal) -> SecurityObservationInput:
        if not isinstance(signal, TargetSideRuntimeSignal):
            raise TargetSideObservationAdapterError("Runtime signal must be typed.")
        if signal.producer_id != self._expected_producer_id:
            raise TargetSideObservationAdapterError("Unexpected target-side producer.")
        if signal.target_identifier != self._expected_target_identifier:
            raise TargetSideObservationAdapterError("Target identifier is not bound.")
        if signal.target_resource != self._expected_target_resource:
            raise TargetSideObservationAdapterError("Target resource is not bound.")
        if signal.destination_port != self._expected_port:
            raise TargetSideObservationAdapterError("Destination port is not supported.")
        return SecurityObservationInput(
            producer_id=signal.producer_id,
            observation_type=SecurityObservationType.NETWORK_TRAFFIC,
            observed_at=signal.observed_at,
            target_resource=signal.target_resource,
            source_reference=signal.source_reference,
            raw_observation_reference=signal.raw_observation_reference,
        )

    def create_observation(
        self,
        signal: TargetSideRuntimeSignal,
    ) -> SecurityObservation:
        try:
            return self._creation_boundary.create(self.to_input(signal))
        except SecurityObservationCreationError as error:
            raise TargetSideObservationAdapterError(
                "Target-side observation creation was rejected."
            ) from error
