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


TARGET_SIDE_PROCESS_PRODUCER_ID = "target-side-process-audit"


class TargetSideProcessObservationAdapterError(ValueError):
    """Raised when a target-side process signal is invalid or rejected."""


@dataclass(frozen=True, slots=True)
class TargetSideProcessRuntimeSignal:
    """Structured process signal; it is not a trusted observation."""

    producer_id: str
    observed_at: datetime
    target_resource: AIResourceReference
    process_identifier: str
    process_name: str
    source_reference: str
    raw_observation_reference: str | None = None

    def __post_init__(self) -> None:
        self._required(self.producer_id, "producer_id")
        if not isinstance(self.observed_at, datetime):
            raise TargetSideProcessObservationAdapterError(
                "observed_at must be a datetime."
            )
        if self.observed_at.utcoffset() is None:
            raise TargetSideProcessObservationAdapterError(
                "observed_at must be timezone-aware."
            )
        if not isinstance(self.target_resource, AIResourceReference):
            raise TargetSideProcessObservationAdapterError(
                "target_resource must be an AIResourceReference."
            )
        if self.target_resource.resource_type is not AIResourceType.ASSET:
            raise TargetSideProcessObservationAdapterError(
                "Process observations require an asset resource."
            )
        self._required(self.process_identifier, "process_identifier")
        self._required(self.process_name, "process_name")
        self._required(self.source_reference, "source_reference")
        if self.raw_observation_reference is not None:
            self._required(
                self.raw_observation_reference,
                "raw_observation_reference",
            )

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise TargetSideProcessObservationAdapterError(
                f"{label} must not be empty."
            )


class TargetSideProcessObservationAdapter:
    """Translate structured process activity and delegate trusted creation."""

    def __init__(
        self,
        creation_boundary: SecurityObservationCreationBoundary,
        *,
        expected_producer_id: str = TARGET_SIDE_PROCESS_PRODUCER_ID,
        expected_target_resource: AIResourceReference,
    ) -> None:
        if not isinstance(creation_boundary, SecurityObservationCreationBoundary):
            raise TargetSideProcessObservationAdapterError(
                "creation_boundary must be authoritative."
            )
        if not expected_producer_id.strip():
            raise TargetSideProcessObservationAdapterError(
                "Process producer binding must be explicit."
            )
        if not isinstance(expected_target_resource, AIResourceReference):
            raise TargetSideProcessObservationAdapterError(
                "expected_target_resource must be canonical."
            )
        if expected_target_resource.resource_type is not AIResourceType.ASSET:
            raise TargetSideProcessObservationAdapterError(
                "Process observations require an asset resource."
            )
        self._creation_boundary = creation_boundary
        self._expected_producer_id = expected_producer_id
        self._expected_target_resource = expected_target_resource

    def to_input(
        self,
        signal: TargetSideProcessRuntimeSignal,
    ) -> SecurityObservationInput:
        if not isinstance(signal, TargetSideProcessRuntimeSignal):
            raise TargetSideProcessObservationAdapterError(
                "Process runtime signal must be typed."
            )
        if signal.producer_id != self._expected_producer_id:
            raise TargetSideProcessObservationAdapterError(
                "Unexpected process producer."
            )
        if signal.target_resource != self._expected_target_resource:
            raise TargetSideProcessObservationAdapterError(
                "Process target resource is not bound."
            )
        return SecurityObservationInput(
            producer_id=signal.producer_id,
            observation_type=SecurityObservationType.PROCESS_ACTIVITY,
            observed_at=signal.observed_at,
            target_resource=signal.target_resource,
            source_reference=signal.source_reference,
            raw_observation_reference=signal.raw_observation_reference,
        )

    def create_observation(
        self,
        signal: TargetSideProcessRuntimeSignal,
    ) -> SecurityObservation:
        try:
            return self._creation_boundary.create(self.to_input(signal))
        except SecurityObservationCreationError as error:
            raise TargetSideProcessObservationAdapterError(
                "Target-side process observation creation was rejected."
            ) from error
