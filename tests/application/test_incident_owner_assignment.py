from datetime import datetime, timezone
from pathlib import Path

import pytest

from application import (
    FileIncidentContextRepository,
    IncidentCommandCenterQueryService,
    IncidentOwnerAssignmentService,
)
from core.incident_response import (
    CanonicalAssetReference,
    FindingReference,
    IncidentLifecycleStatus,
    IncidentPrincipalReference,
    IncidentPrincipalType,
    IncidentRelationship,
    IncidentRelationshipRole,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


NOW = datetime(2026, 8, 18, 17, 0, tzinfo=timezone.utc)


def test_owner_assignment_persists_and_preserves_context(monkeypatch) -> None:
    state, repository = _repository(monkeypatch)
    context = _context()
    repository.save(context)

    owner = IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-7")
    updated = IncidentOwnerAssignmentService(repository).assign(
        context.incident_id,
        owner,
    )

    assert updated.owner == owner
    assert updated.incident_id == context.incident_id
    assert updated.relationships == context.relationships
    assert updated.created_at == context.created_at
    assert updated.updated_at == context.updated_at
    loaded = repository.get(context.incident_id)
    assert loaded == updated
    projection = IncidentCommandCenterQueryService().project(loaded)
    assert projection.incident.owner == owner
    assert state["writes"] == 2


def test_owner_assignment_changes_existing_owner(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)
    original_owner = IncidentPrincipalReference(IncidentPrincipalType.TEAM, "soc")
    context = _context(owner=original_owner)
    repository.save(context)
    replacement = IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-8")

    updated = IncidentOwnerAssignmentService(repository).assign(
        context.incident_id,
        replacement,
    )

    assert updated.owner == replacement
    assert updated.owner != original_owner


def test_unknown_incident_is_fail_safe(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)
    repository.save(_context())
    owner = IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-7")

    with pytest.raises(LookupError, match="not found"):
        IncidentOwnerAssignmentService(repository).assign("missing", owner)


def test_invalid_owner_is_rejected_before_persistence(monkeypatch) -> None:
    state, repository = _repository(monkeypatch)
    repository.save(_context())

    with pytest.raises(ValueError, match="canonical principal"):
        IncidentOwnerAssignmentService(repository).assign(
            "incident-owner-001",
            object(),  # type: ignore[arg-type]
        )

    assert state["writes"] == 1


def _context(
    *, owner: IncidentPrincipalReference | None = None,
) -> SecurityIncidentContext:
    return SecurityIncidentContext(
        incident_id="incident-owner-001",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="controlled-lab",
        source_reference="controlled-lab:incident-owner-001",
        title="Owner assignment incident",
        description="Existing context must remain unchanged.",
        created_at=NOW,
        updated_at=NOW,
        owner=owner,
        relationships=(
            IncidentRelationship(
                relationship_id="finding-relationship",
                role=IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
                target=FindingReference("finding-001", "greenbone"),
            ),
            IncidentRelationship(
                relationship_id="asset-relationship",
                role=IncidentRelationshipRole.AFFECTED_ASSET,
                target=CanonicalAssetReference("asset-001"),
            ),
            IncidentRelationship(
                relationship_id="ti-relationship",
                role=IncidentRelationshipRole.THREAT_CONTEXT,
                target=ThreatIntelligenceReference("CVE-2004-2687", "1.0"),
            ),
        ),
    )


def _repository(monkeypatch):
    state: dict[str, object] = {"source": None, "exists": False, "writes": 0}

    monkeypatch.setattr(Path, "exists", lambda self: bool(state["exists"]))
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, encoding: state["source"],
    )
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda self, text, encoding: state.update(
            source=text,
            exists=True,
            writes=int(state["writes"]) + 1,
        ),
    )
    monkeypatch.setattr(Path, "mkdir", lambda self, parents, exist_ok: None)
    return state, FileIncidentContextRepository("controlled-incidents.json")
