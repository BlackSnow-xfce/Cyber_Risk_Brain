from datetime import datetime, timezone

import pytest

from core.ai_authorization import AIResourceReference, AIResourceType
from core.security_observation import (
    SecurityObservation,
    SecurityObservationCollectionMethod,
    SecurityObservationIndependence,
    SecurityObservationProvenance,
    SecurityObservationType,
)


OBSERVED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _observation(**overrides):
    values = {
        "observation_id": "observation:distcc:001",
        "observation_type": SecurityObservationType.NETWORK_TRAFFIC,
        "observed_at": OBSERVED_AT,
        "target_resource": AIResourceReference(
            AIResourceType.ASSET,
            "asset-lab-metasploitable2-001",
        ),
        "source_identity": "sensor:target-side-tcpdump",
        "collection_method": SecurityObservationCollectionMethod.PACKET_CAPTURE,
        "independence": SecurityObservationIndependence.TARGET_SIDE,
        "provenance": SecurityObservationProvenance(
            "target-side-sensor",
            "tcpdump:172.18.0.19:3632:2026-08-20T12:00:00Z",
            "capture:distcc:001",
        ),
    }
    values.update(overrides)
    return SecurityObservation(**values)


def test_valid_observation_is_typed_and_versioned():
    observation = _observation()
    assert observation.observation_type is SecurityObservationType.NETWORK_TRAFFIC
    assert observation.independence is SecurityObservationIndependence.TARGET_SIDE
    assert observation.contract_version == "1.0"


@pytest.mark.parametrize(
    "field, value",
    [
        ("observation_id", ""),
        ("source_identity", ""),
        ("observed_at", datetime(2026, 8, 20, 12, 0)),
        ("target_resource", None),
        ("collection_method", "packet_capture"),
        ("independence", "target_side"),
        ("provenance", None),
    ],
)
def test_required_fields_and_types_fail_closed(field, value):
    with pytest.raises(ValueError):
        _observation(**{field: value})


def test_target_side_signal_does_not_encode_confirmation():
    observation = _observation()
    assert not hasattr(observation, "confirmed")
    assert not hasattr(observation, "compromise_confirmed")
    assert not hasattr(observation, "verification_state")


def test_independence_is_explicit_and_deterministic():
    independent = _observation(
        independence=SecurityObservationIndependence.INDEPENDENT_SENSOR,
        source_identity="sensor:network-monitor",
        collection_method=SecurityObservationCollectionMethod.SENSOR,
    )
    self_attested = _observation(
        independence=SecurityObservationIndependence.SELF_ATTESTED,
        source_identity="producer:offensive-client",
        collection_method=SecurityObservationCollectionMethod.PRODUCER_ATTESTATION,
    )
    assert independent.independence is not self_attested.independence


def test_observation_is_immutable():
    observation = _observation()
    with pytest.raises((AttributeError, TypeError)):
        observation.source_identity = "other"  # type: ignore[misc]
