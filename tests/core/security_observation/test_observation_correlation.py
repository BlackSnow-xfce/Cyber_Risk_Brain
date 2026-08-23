from datetime import datetime, timezone

import pytest

from core.ai_authorization import AIResourceReference, AIResourceType
from core.security_observation import (
    SecurityObservation,
    SecurityObservationCollectionMethod,
    SecurityObservationCorrelationService,
    SecurityObservationIndependence,
    SecurityObservationNetworkTrafficCorrelationInput,
    SecurityObservationProvenance,
    SecurityObservationType,
)


OBSERVED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
RESOURCE = AIResourceReference(
    AIResourceType.ASSET,
    "asset-lab-metasploitable2-001",
)


def observation(**overrides: object) -> SecurityObservation:
    values: dict[str, object] = {
        "observation_id": "observation:distcc:001",
        "observation_type": SecurityObservationType.NETWORK_TRAFFIC,
        "observed_at": OBSERVED_AT,
        "target_resource": RESOURCE,
        "source_identity": "sensor:target-side-tcpdump",
        "collection_method": SecurityObservationCollectionMethod.PACKET_CAPTURE,
        "independence": SecurityObservationIndependence.TARGET_SIDE,
        "provenance": SecurityObservationProvenance(
            "target-side-sensor",
            "tcpdump:metasploitable2:eth0:opaque-signal",
            "capture:distcc:001",
        ),
    }
    values.update(overrides)
    return SecurityObservation(**values)


def correlation_input(
    value: SecurityObservation | None = None,
) -> SecurityObservationNetworkTrafficCorrelationInput:
    current = value or observation()
    return SecurityObservationNetworkTrafficCorrelationInput(
        observation=current,
        observation_id=current.observation_id,
        target_resource=current.target_resource,
        observation_type=current.observation_type,
        independence=current.independence,
        provenance=current.provenance,
    )


def test_network_observation_creates_deterministic_derived_evidence() -> None:
    service = SecurityObservationCorrelationService()

    first = service.correlate_network_traffic(correlation_input())
    second = service.correlate_network_traffic(correlation_input())

    assert first == second
    assert first.evidence_type.value == "correlation"
    assert first.kind.value == "derived"
    assert first.identifier == "correlation:security-observation:observation:distcc:001"


def test_observation_id_resource_and_provenance_are_retained() -> None:
    evidence = SecurityObservationCorrelationService().correlate_network_traffic(
        correlation_input()
    )

    assert evidence.provenance is not None
    assert "observation:observation:distcc:001" in evidence.provenance.input_references
    assert "resource:asset:asset-lab-metasploitable2-001" in (
        evidence.provenance.input_references
    )
    assert any(
        reference.startswith("observation-provenance:target-side-sensor:")
        for reference in evidence.provenance.input_references
    )
    assert "asset-lab-metasploitable2-001" in str(evidence.value)


def test_inconsistent_target_binding_fails_closed() -> None:
    other_resource = AIResourceReference(AIResourceType.ASSET, "other-asset")
    current = observation()
    with pytest.raises(ValueError, match="target binding"):
        SecurityObservationNetworkTrafficCorrelationInput(
            observation=current,
            observation_id=current.observation_id,
            target_resource=other_resource,
            observation_type=current.observation_type,
            independence=current.independence,
            provenance=current.provenance,
        )


def test_missing_observation_id_fails_closed() -> None:
    current = observation()
    with pytest.raises(ValueError, match="Observation ID"):
        SecurityObservationNetworkTrafficCorrelationInput(
            observation=current,
            observation_id="",
            target_resource=current.target_resource,
            observation_type=current.observation_type,
            independence=current.independence,
            provenance=current.provenance,
        )


def test_inconsistent_provenance_fails_closed() -> None:
    current = observation()
    with pytest.raises(ValueError, match="provenance"):
        SecurityObservationNetworkTrafficCorrelationInput(
            observation=current,
            observation_id=current.observation_id,
            target_resource=current.target_resource,
            observation_type=current.observation_type,
            independence=current.independence,
            provenance=SecurityObservationProvenance(
                "other-source",
                "other-reference",
            ),
        )


def test_unsupported_observation_type_is_rejected_without_evidence() -> None:
    current = observation(
        observation_type=SecurityObservationType.PROCESS_ACTIVITY,
    )
    input_contract = correlation_input(current)

    with pytest.raises(ValueError, match="NETWORK_TRAFFIC"):
        SecurityObservationCorrelationService().correlate_network_traffic(
            input_contract
        )


def test_opaque_provenance_is_not_parsed_into_port_or_protocol_facts() -> None:
    evidence = SecurityObservationCorrelationService().correlate_network_traffic(
        correlation_input(
            observation(
                provenance=SecurityObservationProvenance(
                    "target-side-sensor",
                    "opaque:TCP/3632:untrusted-text",
                )
            )
        )
    )

    assert "3632" not in str(evidence.value)
    assert "TCP" not in str(evidence.value)


def test_derived_evidence_has_no_confirmation_semantics() -> None:
    evidence = SecurityObservationCorrelationService().correlate_network_traffic(
        correlation_input()
    )

    assert not hasattr(evidence, "confirmed")
    assert not hasattr(evidence, "verification_state")
    assert not hasattr(evidence, "compromise_confirmed")
    assert "exploit" not in str(evidence.value).lower()
    assert "compromise" not in str(evidence.value).lower()


def test_self_attested_observation_is_not_promoted() -> None:
    current = observation(
        source_identity="producer:offensive-test-client",
        collection_method=SecurityObservationCollectionMethod.PRODUCER_ATTESTATION,
        independence=SecurityObservationIndependence.SELF_ATTESTED,
    )
    evidence = SecurityObservationCorrelationService().correlate_network_traffic(
        correlation_input(current)
    )

    assert evidence.kind.value == "derived"
    assert "independent" not in str(evidence.value).lower()
    assert "confirmed" not in str(evidence.value).lower()
