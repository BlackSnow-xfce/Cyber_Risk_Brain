from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from core.incident_response import (
    SECURITY_INCIDENT_CONTEXT_CONTRACT_VERSION,
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentLifecycleStatus,
    IncidentParticipant,
    IncidentParticipantRole,
    IncidentPrincipalReference,
    IncidentPrincipalType,
    IncidentRelationship,
    IncidentRelationshipRole,
    IncidentTargetReference,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def test_valid_minimal_security_incident_context() -> None:
    context = _context()

    assert context.incident_id == "incident-001"
    assert context.lifecycle_status is IncidentLifecycleStatus.OPEN
    assert context.contract_version == SECURITY_INCIDENT_CONTEXT_CONTRACT_VERSION
    assert context.owner is None
    assert context.relationships == ()


def test_multiple_finding_and_asset_references_preserve_input_order() -> None:
    relationships = (
        _relationship(
            "relationship-finding-002",
            IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
            FindingReference("finding-002", "greenbone"),
        ),
        _relationship(
            "relationship-asset-002",
            IncidentRelationshipRole.AFFECTED_ASSET,
            CanonicalAssetReference("asset-002"),
        ),
        _relationship(
            "relationship-finding-001",
            IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
            FindingReference("finding-001", "greenbone"),
        ),
        _relationship(
            "relationship-asset-001",
            IncidentRelationshipRole.AFFECTED_ASSET,
            CanonicalAssetReference("asset-001"),
        ),
    )

    context = _context(relationships=relationships)

    assert context.relationships == relationships
    assert [item.target for item in context.relationships] == [
        FindingReference("finding-002", "greenbone"),
        CanonicalAssetReference("asset-002"),
        FindingReference("finding-001", "greenbone"),
        CanonicalAssetReference("asset-001"),
    ]


def test_decision_reference_requires_concrete_version_identity() -> None:
    reference = DecisionVersionReference(
        decision_id="decision-001",
        version_id="decision-version-003",
        evidence_snapshot_id="evidence-snapshot-003",
    )
    context = _context(
        relationships=(
            _relationship(
                "relationship-decision-001",
                IncidentRelationshipRole.RELATED_DECISION,
                reference,
            ),
        )
    )

    assert context.relationships[0].target == reference
    with pytest.raises(ValueError, match="Decision version ID"):
        DecisionVersionReference("decision-001", " ")


def test_all_cross_domain_references_contain_identity_only() -> None:
    targets = (
        FindingReference("finding-001", "greenbone"),
        CanonicalAssetReference("asset-001"),
        ThreatIntelligenceReference("CVE-2004-2687", "1.0"),
        EvidenceReference("correlation:finding-001:CVE-2004-2687", "1.0"),
        DecisionVersionReference("decision-001", "version-001"),
    )

    assert not hasattr(targets[0], "severity")
    assert not hasattr(targets[1], "criticality")
    assert not hasattr(targets[2], "value")
    assert not hasattr(targets[3], "provenance")
    assert not hasattr(targets[4], "outcome")


def test_contract_has_no_implicit_primary_semantics() -> None:
    context = _context(
        relationships=(
            _relationship(
                "relationship-finding-001",
                IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
                FindingReference("finding-001", "greenbone"),
            ),
            _relationship(
                "relationship-finding-002",
                IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
                FindingReference("finding-002", "greenbone"),
            ),
        )
    )

    assert not hasattr(context, "primary_finding")
    assert not hasattr(context, "primary_asset")
    assert not hasattr(context, "severity")
    assert not hasattr(context, "priority")
    assert not hasattr(context, "caused_by")


def test_contract_and_references_are_immutable() -> None:
    context = _context(
        relationships=(
            _relationship(
                "relationship-asset-001",
                IncidentRelationshipRole.AFFECTED_ASSET,
                CanonicalAssetReference("asset-001"),
            ),
        )
    )

    with pytest.raises(FrozenInstanceError):
        context.incident_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        context.relationships[0].target.canonical_asset_id = "changed"  # type: ignore[union-attr,misc]


def test_lifecycle_status_matches_adr_0009() -> None:
    assert tuple(status.value for status in IncidentLifecycleStatus) == (
        "open",
        "investigating",
        "resolved",
        "closed",
    )
    for status in IncidentLifecycleStatus:
        assert _context(lifecycle_status=status).lifecycle_status is status


def test_owner_and_participants_are_typed_principal_references() -> None:
    owner = IncidentPrincipalReference(IncidentPrincipalType.TEAM, "soc-tier-2")
    participants = (
        IncidentParticipant(
            IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001"),
            IncidentParticipantRole.ANALYST,
        ),
        IncidentParticipant(
            IncidentPrincipalReference(IncidentPrincipalType.USER, "responder-001"),
            IncidentParticipantRole.RESPONDER,
        ),
    )

    context = _context(owner=owner, participants=participants)

    assert context.owner == owner
    assert context.participants == participants
    assert not hasattr(context.owner, "permissions")


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: FindingReference(" ", "greenbone"), "Finding ID"),
        (lambda: FindingReference("finding-001", " "), "Finding source"),
        (lambda: CanonicalAssetReference(" "), "Canonical asset ID"),
        (
            lambda: ThreatIntelligenceReference(" ", "1.0"),
            "Threat intelligence reference ID",
        ),
        (lambda: EvidenceReference(" ", "1.0"), "Evidence ID"),
        (lambda: DecisionVersionReference(" ", "version-001"), "Decision ID"),
        (
            lambda: IncidentPrincipalReference(IncidentPrincipalType.USER, " "),
            "Incident principal ID",
        ),
    ],
)
def test_missing_reference_identities_fail_safe(factory, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


@pytest.mark.parametrize("field", ["incident_id", "source", "source_reference", "title"])
def test_missing_required_incident_identities_fail_safe(field: str) -> None:
    values = {
        "incident_id": "incident-001",
        "source": "soc",
        "source_reference": "soc:incident-001",
        "title": "Controlled incident",
    }
    values[field] = " "

    with pytest.raises(ValueError, match="must not be empty"):
        _context(**values)


def test_naive_or_inverted_timestamps_fail_safe() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _context(created_at=NOW.replace(tzinfo=None))
    with pytest.raises(ValueError, match="must not precede"):
        _context(updated_at=NOW - timedelta(seconds=1))


def test_duplicate_relationships_and_participants_fail_safe() -> None:
    relationship = _relationship(
        "relationship-finding-001",
        IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
        FindingReference("finding-001", "greenbone"),
    )
    participant = IncidentParticipant(
        IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001"),
        IncidentParticipantRole.ANALYST,
    )

    with pytest.raises(ValueError, match="relationships must be unique"):
        _context(
            relationships=(
                relationship,
                _relationship(
                    "relationship-finding-duplicate",
                    relationship.role,
                    relationship.target,
                ),
            )
        )
    with pytest.raises(ValueError, match="participants must be unique"):
        _context(participants=(participant, participant))


def test_relationship_role_must_match_reference_type() -> None:
    with pytest.raises(ValueError, match="incompatible"):
        _relationship(
            "relationship-invalid",
            IncidentRelationshipRole.AFFECTED_ASSET,
            FindingReference("finding-001", "greenbone"),
        )


def _context(
    *,
    incident_id: str = "incident-001",
    lifecycle_status: IncidentLifecycleStatus = IncidentLifecycleStatus.OPEN,
    source: str = "soc",
    source_reference: str = "soc:incident-001",
    title: str = "Controlled incident",
    created_at: datetime = NOW,
    updated_at: datetime = NOW,
    owner: IncidentPrincipalReference | None = None,
    participants: tuple[IncidentParticipant, ...] = (),
    relationships: tuple[IncidentRelationship, ...] = (),
) -> SecurityIncidentContext:
    return SecurityIncidentContext(
        incident_id=incident_id,
        lifecycle_status=lifecycle_status,
        source=source,
        source_reference=source_reference,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        owner=owner,
        participants=participants,
        relationships=relationships,
    )


def _relationship(
    relationship_id: str,
    role: IncidentRelationshipRole,
    target: IncidentTargetReference,
) -> IncidentRelationship:
    return IncidentRelationship(
        relationship_id=relationship_id,
        role=role,
        target=target,
    )
