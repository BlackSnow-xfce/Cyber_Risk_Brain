from datetime import datetime, timezone

import pytest

from application import (
    SecurityObservationCreationBoundary,
    SecurityObservationCreationError,
    SecurityObservationInput,
    SecurityObservationProducerPolicy,
)
from core.ai_authorization import AIResourceReference, AIResourceType
from core.security_observation import (
    SecurityObservationCollectionMethod,
    SecurityObservationIndependence,
    SecurityObservationType,
)


TARGET = AIResourceReference(AIResourceType.ASSET, "asset-lab-metasploitable2-001")
OBSERVED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _policy(
    producer_id="target-side-tcpdump",
    source_identity="sensor:target-side-tcpdump",
    collection_method=SecurityObservationCollectionMethod.PACKET_CAPTURE,
    independence=SecurityObservationIndependence.TARGET_SIDE,
):
    return SecurityObservationProducerPolicy(
        producer_id=producer_id,
        source_identity=source_identity,
        collection_method=collection_method,
        independence=independence,
        allowed_observation_types=frozenset(
            {SecurityObservationType.NETWORK_TRAFFIC}
        ),
    )


def _request(**overrides):
    values = {
        "producer_id": "target-side-tcpdump",
        "observation_type": SecurityObservationType.NETWORK_TRAFFIC,
        "observed_at": OBSERVED_AT,
        "target_resource": TARGET,
        "source_reference": "capture:distcc:001",
        "raw_observation_reference": "tcpdump:172.18.0.19:3632:001",
    }
    values.update(overrides)
    return SecurityObservationInput(**values)


def _boundary(*policies):
    return SecurityObservationCreationBoundary(
        policies or (_policy(),),
        observation_id_factory=lambda: "observation:generated:001",
    )


def test_allowed_producer_gets_policy_assigned_metadata():
    observation = _boundary().create(_request())
    assert observation.source_identity == "sensor:target-side-tcpdump"
    assert observation.collection_method is SecurityObservationCollectionMethod.PACKET_CAPTURE
    assert observation.independence is SecurityObservationIndependence.TARGET_SIDE
    assert observation.observation_id == "observation:generated:001"


def test_unknown_producer_is_denied():
    with pytest.raises(SecurityObservationCreationError):
        _boundary().create(_request(producer_id="unknown"))


def test_policy_is_positive_allowlist_and_type_is_explicit():
    with pytest.raises(SecurityObservationCreationError):
        _boundary().create(
            _request(observation_type=SecurityObservationType.PROCESS_ACTIVITY)
        )


def test_offensive_producer_cannot_become_independent_sensor():
    policy = _policy(
        producer_id="offensive-test-client",
        source_identity="producer:offensive-test-client",
        collection_method=SecurityObservationCollectionMethod.PRODUCER_ATTESTATION,
        independence=SecurityObservationIndependence.SELF_ATTESTED,
    )
    observation = _boundary(policy).create(
        _request(producer_id="offensive-test-client")
    )
    assert observation.independence is SecurityObservationIndependence.SELF_ATTESTED


def test_external_source_identity_is_not_used_for_trusted_identity():
    observation = _boundary().create(_request())
    assert observation.source_identity != observation.provenance.source_reference
    assert observation.source_identity == "sensor:target-side-tcpdump"


@pytest.mark.parametrize(
    "field, value",
    [
        ("observed_at", datetime(2026, 8, 20, 12, 0)),
        ("target_resource", None),
        ("source_reference", ""),
    ],
)
def test_invalid_binding_timestamp_or_provenance_fails_closed(field, value):
    with pytest.raises(SecurityObservationCreationError):
        _boundary().create(_request(**{field: value}))


def test_input_has_no_trusted_metadata_controls():
    assert "source_identity" not in SecurityObservationInput.__dataclass_fields__
    assert "independence" not in SecurityObservationInput.__dataclass_fields__
    assert "collection_method" not in SecurityObservationInput.__dataclass_fields__


def test_creation_has_no_confirmation_or_evidence_side_effects():
    observation = _boundary().create(_request())
    assert not hasattr(observation, "confirmed")
    assert not hasattr(observation, "evidence")
    assert not hasattr(observation, "incident_state")
