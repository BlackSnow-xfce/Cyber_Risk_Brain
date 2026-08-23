from datetime import datetime, timezone

import pytest

from application import (
    SecurityObservationCreationBoundary,
    SecurityObservationProducerPolicy,
    TargetSideProcessObservationAdapter,
    TargetSideProcessObservationAdapterError,
    TargetSideProcessRuntimeSignal,
)
from core.ai_authorization import AIResourceReference, AIResourceType
from core.security_observation import (
    SecurityObservationCollectionMethod,
    SecurityObservationIndependence,
    SecurityObservationType,
)


TARGET = AIResourceReference(AIResourceType.ASSET, "asset-lab-metasploitable2-001")
OTHER_TARGET = AIResourceReference(AIResourceType.ASSET, "other-asset")
OBSERVED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
PRODUCER_ID = "target-side-process-audit"


def policy(
    *,
    producer_id: str = PRODUCER_ID,
    source_identity: str = "sensor:target-side-process-audit",
    collection_method: SecurityObservationCollectionMethod = (
        SecurityObservationCollectionMethod.SENSOR
    ),
    independence: SecurityObservationIndependence = (
        SecurityObservationIndependence.TARGET_SIDE
    ),
) -> SecurityObservationProducerPolicy:
    return SecurityObservationProducerPolicy(
        producer_id=producer_id,
        source_identity=source_identity,
        collection_method=collection_method,
        independence=independence,
        allowed_observation_types=frozenset(
            {SecurityObservationType.PROCESS_ACTIVITY}
        ),
    )


def boundary(
    *policies: SecurityObservationProducerPolicy,
) -> SecurityObservationCreationBoundary:
    return SecurityObservationCreationBoundary(
        policies or (policy(),),
        observation_id_factory=lambda: "observation:process:001",
    )


def adapter(
    creation_boundary: SecurityObservationCreationBoundary | None = None,
    *,
    expected_target_resource: AIResourceReference = TARGET,
) -> TargetSideProcessObservationAdapter:
    return TargetSideProcessObservationAdapter(
        creation_boundary or boundary(),
        expected_target_resource=expected_target_resource,
    )


def signal(**overrides: object) -> TargetSideProcessRuntimeSignal:
    values: dict[str, object] = {
        "producer_id": PRODUCER_ID,
        "observed_at": OBSERVED_AT,
        "target_resource": TARGET,
        "process_identifier": "pid:4242",
        "process_name": "distccd",
        "source_reference": "audit:metasploitable2:process:4242",
        "raw_observation_reference": "audit-log:metasploitable2:line:17",
    }
    values.update(overrides)
    return TargetSideProcessRuntimeSignal(**values)


def test_valid_process_signal_becomes_observation_input() -> None:
    input_contract = adapter().to_input(signal())

    assert input_contract.producer_id == PRODUCER_ID
    assert input_contract.observation_type is SecurityObservationType.PROCESS_ACTIVITY
    assert input_contract.target_resource == TARGET
    assert input_contract.source_reference == "audit:metasploitable2:process:4242"


def test_creation_boundary_produces_process_observation() -> None:
    observation = adapter().create_observation(signal())

    assert observation.observation_type is SecurityObservationType.PROCESS_ACTIVITY
    assert observation.observation_id == "observation:process:001"
    assert observation.target_resource == TARGET


def test_trusted_policy_assigns_source_collection_and_independence() -> None:
    observation = adapter(
        boundary(
            policy(
                source_identity="sensor:trusted-process-audit",
                collection_method=SecurityObservationCollectionMethod.SENSOR,
                independence=SecurityObservationIndependence.TARGET_SIDE,
            )
        )
    ).create_observation(signal())

    assert observation.source_identity == "sensor:trusted-process-audit"
    assert observation.collection_method is SecurityObservationCollectionMethod.SENSOR
    assert observation.independence is SecurityObservationIndependence.TARGET_SIDE


def test_provenance_is_retained_without_process_string_interpretation() -> None:
    observation = adapter().create_observation(
        signal(
            process_identifier="opaque process / CVE-2004-2687",
            process_name="untrusted text: exploit successful",
        )
    )

    assert observation.provenance.source_reference == (
        "audit:metasploitable2:process:4242"
    )
    assert observation.provenance.raw_observation_reference == (
        "audit-log:metasploitable2:line:17"
    )
    assert not hasattr(observation, "confirmed")
    assert not hasattr(observation, "compromise_confirmed")


def test_unknown_producer_is_rejected_by_creation_boundary() -> None:
    with pytest.raises(TargetSideProcessObservationAdapterError):
        adapter().create_observation(signal(producer_id="unknown-producer"))


def test_resource_binding_mismatch_is_rejected() -> None:
    with pytest.raises(TargetSideProcessObservationAdapterError, match="target resource"):
        adapter().to_input(signal(target_resource=OTHER_TARGET))


@pytest.mark.parametrize(
    "field, value",
    [
        ("observed_at", datetime(2026, 8, 20, 12, 0)),
        ("source_reference", ""),
        ("process_identifier", ""),
        ("process_name", ""),
    ],
)
def test_invalid_signal_fields_fail_closed(field: str, value: object) -> None:
    with pytest.raises(TargetSideProcessObservationAdapterError):
        signal(**{field: value})


def test_missing_raw_reference_is_allowed_when_source_reference_is_present() -> None:
    observation = adapter().create_observation(
        signal(raw_observation_reference=None)
    )

    assert observation.provenance.raw_observation_reference is None


def test_process_input_cannot_select_independence_metadata() -> None:
    process_policy = policy(
        independence=SecurityObservationIndependence.TARGET_SIDE
    )
    process_input = adapter().to_input(signal())

    assert "independence" not in process_input.__dataclass_fields__
    observation = boundary(process_policy).create(process_input)
    assert observation.independence is SecurityObservationIndependence.TARGET_SIDE


def test_self_attested_policy_does_not_promote_process_observation() -> None:
    observation = adapter(
        boundary(
            policy(
                source_identity="producer:offensive-test-client",
                collection_method=SecurityObservationCollectionMethod.PRODUCER_ATTESTATION,
                independence=SecurityObservationIndependence.SELF_ATTESTED,
            )
        )
    ).create_observation(signal())

    assert observation.independence is SecurityObservationIndependence.SELF_ATTESTED
    assert not hasattr(observation, "verification_state")
    assert not hasattr(observation, "incident_state")
