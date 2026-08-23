from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from core.ai_authorization import AIResourceReference
from core.security_observation import (
    SecurityObservation,
    SecurityObservationCollectionMethod,
    SecurityObservationIndependence,
    SecurityObservationProvenance,
    SecurityObservationType,
)


class SecurityObservationCreationError(ValueError):
    """Raised when an external observation request cannot be trusted."""


@dataclass(frozen=True, slots=True)
class SecurityObservationInput:
    """Producer-controlled facts; trusted metadata is deliberately absent."""

    producer_id: str
    observation_type: SecurityObservationType
    observed_at: datetime
    target_resource: AIResourceReference
    source_reference: str
    raw_observation_reference: str | None = None

    def __post_init__(self) -> None:
        self._required(self.producer_id, "producer_id")
        if not isinstance(self.observation_type, SecurityObservationType):
            raise SecurityObservationCreationError(
                "observation_type must be canonical."
            )
        if not isinstance(self.target_resource, AIResourceReference):
            raise SecurityObservationCreationError(
                "target_resource must be an AIResourceReference."
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
            raise SecurityObservationCreationError(f"{label} must not be empty.")


@dataclass(frozen=True, slots=True)
class SecurityObservationProducerPolicy:
    """Trusted PredatorAI metadata for one explicitly registered producer."""

    producer_id: str
    source_identity: str
    collection_method: SecurityObservationCollectionMethod
    independence: SecurityObservationIndependence
    allowed_observation_types: frozenset[SecurityObservationType]

    def __post_init__(self) -> None:
        self._required(self.producer_id, "producer_id")
        self._required(self.source_identity, "source_identity")
        if not isinstance(
            self.collection_method,
            SecurityObservationCollectionMethod,
        ):
            raise SecurityObservationCreationError(
                "collection_method must be canonical."
            )
        if not isinstance(self.independence, SecurityObservationIndependence):
            raise SecurityObservationCreationError(
                "independence must be canonical."
            )
        if not isinstance(self.allowed_observation_types, frozenset):
            raise SecurityObservationCreationError(
                "allowed_observation_types must be a frozenset."
            )
        if not self.allowed_observation_types or any(
            not isinstance(item, SecurityObservationType)
            for item in self.allowed_observation_types
        ):
            raise SecurityObservationCreationError(
                "allowed_observation_types must be explicit and typed."
            )

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip() or value == "*":
            raise SecurityObservationCreationError(
                f"{label} must be explicit and non-wildcard."
            )


class SecurityObservationCreationBoundary:
    """Assign trusted observation metadata only from a positive policy."""

    def __init__(
        self,
        producer_policies: Iterable[SecurityObservationProducerPolicy],
        *,
        observation_id_factory: Callable[[], str] | None = None,
    ) -> None:
        policies = tuple(producer_policies)
        if any(not isinstance(item, SecurityObservationProducerPolicy) for item in policies):
            raise SecurityObservationCreationError("Producer policies must be typed.")
        producer_ids = tuple(item.producer_id for item in policies)
        if len(set(producer_ids)) != len(producer_ids):
            raise SecurityObservationCreationError("Producer policies must be unique.")
        self._policies = {item.producer_id: item for item in policies}
        self._observation_id_factory = observation_id_factory or (
            lambda: f"observation:{uuid4()}"
        )

    def create(self, request: SecurityObservationInput) -> SecurityObservation:
        if not isinstance(request, SecurityObservationInput):
            raise SecurityObservationCreationError("Observation input must be canonical.")
        policy = self._policies.get(request.producer_id)
        if policy is None:
            raise SecurityObservationCreationError("Producer is not authorized.")
        if request.observation_type not in policy.allowed_observation_types:
            raise SecurityObservationCreationError(
                "Observation type is not allowed for this producer."
            )
        observation_id = self._observation_id_factory()
        if not isinstance(observation_id, str) or not observation_id.strip():
            raise SecurityObservationCreationError(
                "Observation ID factory must return a non-empty ID."
            )
        try:
            return SecurityObservation(
                observation_id=observation_id,
                observation_type=request.observation_type,
                observed_at=request.observed_at,
                target_resource=request.target_resource,
                source_identity=policy.source_identity,
                collection_method=policy.collection_method,
                independence=policy.independence,
                provenance=SecurityObservationProvenance(
                    source_type=policy.source_identity,
                    source_reference=request.source_reference,
                    raw_observation_reference=request.raw_observation_reference,
                ),
            )
        except (TypeError, ValueError) as error:
            raise SecurityObservationCreationError(
                "Observation input failed authoritative validation."
            ) from error
