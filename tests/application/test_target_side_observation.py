from datetime import datetime, timezone

import pytest

from application import (
    SecurityObservationCreationBoundary,
    SecurityObservationProducerPolicy,
    TargetSideObservationAdapterError,
    TargetSideRuntimeObservationAdapter,
    TargetSideRuntimeSignal,
)
from core.ai_authorization import AIResourceReference, AIResourceType
from core.security_observation import (
    SecurityObservationCollectionMethod,
    SecurityObservationIndependence,
    SecurityObservationType,
)


TARGET = AIResourceReference(AIResourceType.ASSET, "asset-lab-metasploitable2-001")
OBSERVED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _boundary():
    return SecurityObservationCreationBoundary(
        (
            SecurityObservationProducerPolicy(
                producer_id="target-side-tcpdump",
                source_identity="sensor:target-side-tcpdump",
                collection_method=SecurityObservationCollectionMethod.PACKET_CAPTURE,
                independence=SecurityObservationIndependence.TARGET_SIDE,
                allowed_observation_types=frozenset(
                    {SecurityObservationType.NETWORK_TRAFFIC}
                ),
            ),
        ),
        observation_id_factory=lambda: "observation:distcc:runtime:001",
    )


def _signal(**overrides):
    values = {
        "producer_id": "target-side-tcpdump",
        "observed_at": OBSERVED_AT,
        "target_identifier": "172.18.0.19",
        "target_resource": TARGET,
        "protocol": "TCP",
        "destination_port": 3632,
        "source_reference": "tcpdump:distcc:runtime:001",
        "raw_observation_reference": "capture:distcc:runtime:001",
    }
    values.update(overrides)
    return TargetSideRuntimeSignal(**values)


def _adapter():
    return TargetSideRuntimeObservationAdapter(
        _boundary(),
        expected_target_resource=TARGET,
    )


def test_runtime_signal_translates_and_uses_creation_boundary():
    adapter = _adapter()
    observation_input = adapter.to_input(_signal())
    observation = adapter.create_observation(_signal())
    assert observation_input.target_resource == TARGET
    assert observation.observation_id == "observation:distcc:runtime:001"
    assert observation.independence is SecurityObservationIndependence.TARGET_SIDE
    assert observation.source_identity == "sensor:target-side-tcpdump"
    assert observation.collection_method is SecurityObservationCollectionMethod.PACKET_CAPTURE
    assert observation.provenance.source_reference == "tcpdump:distcc:runtime:001"


@pytest.mark.parametrize(
    "field, value",
    [
        ("observed_at", datetime(2026, 8, 20, 12, 0)),
        ("target_identifier", "172.18.0.20"),
        ("target_resource", AIResourceReference(AIResourceType.ASSET, "asset-other")),
        ("protocol", "UDP"),
        ("destination_port", 80),
        ("source_reference", ""),
    ],
)
def test_invalid_runtime_signal_fails_closed(field, value):
    with pytest.raises((ValueError, TargetSideObservationAdapterError)):
        _adapter().create_observation(_signal(**{field: value}))


def test_unknown_producer_is_rejected_by_adapter_and_boundary():
    with pytest.raises(TargetSideObservationAdapterError):
        _adapter().create_observation(_signal(producer_id="unknown"))


def test_target_side_adapter_cannot_assign_independent_sensor():
    observation = _adapter().create_observation(_signal())
    assert observation.independence is SecurityObservationIndependence.TARGET_SIDE
    assert not hasattr(observation, "exploit_success")
    assert not hasattr(observation, "compromise_confirmed")
    assert not hasattr(observation, "evidence")


def test_adapter_does_not_add_incident_or_correlation_side_effects():
    observation = _adapter().create_observation(_signal())
    assert observation.target_resource.resource_id == "asset-lab-metasploitable2-001"
