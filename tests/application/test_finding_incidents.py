from datetime import datetime, timezone
from pathlib import Path

from application import (
    FileIncidentContextRepository,
    FindingIncidentQueryService,
)
from core.incident_response import (
    FindingReference,
    IncidentLifecycleStatus,
    IncidentRelationship,
    IncidentRelationshipRole,
    SecurityIncidentContext,
)


def test_finding_incident_query_returns_typed_persisted_relationship(monkeypatch) -> None:
    state, repository = _repository(monkeypatch)
    repository.save(_context())

    references = FindingIncidentQueryService(repository).find_incidents("finding-001")

    assert len(references) == 1
    assert references[0].incident_id == "incident-001"
    assert references[0].relationship_id == "relationship-finding-001"
    assert references[0].relationship_role is IncidentRelationshipRole.INVESTIGATION_CANDIDATE
    assert references[0].lifecycle_status is IncidentLifecycleStatus.INVESTIGATING
    assert state["source"] is not None


def test_finding_incident_query_returns_empty_for_unrelated_finding(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)
    repository.save(_context())

    assert FindingIncidentQueryService(repository).find_incidents("missing") == ()


def test_finding_incident_query_rejects_empty_identifier(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)

    try:
        FindingIncidentQueryService(repository).find_incidents(" ")
    except ValueError as error:
        assert str(error) == "Finding ID must not be empty."
    else:
        raise AssertionError("Empty finding IDs must be rejected.")


def _context() -> SecurityIncidentContext:
    return SecurityIncidentContext(
        incident_id="incident-001",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="controlled-lab",
        source_reference="controlled-lab:incident-001",
        title="Incident",
        created_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
        updated_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
        relationships=(
            IncidentRelationship(
                relationship_id="relationship-finding-001",
                role=IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
                target=FindingReference("finding-001", "greenbone"),
            ),
        ),
    )


def _repository(monkeypatch):
    state: dict[str, object] = {"source": None, "exists": False}
    monkeypatch.setattr(Path, "exists", lambda self: bool(state["exists"]))
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, encoding: state["source"],
    )
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda self, text, encoding: state.update(source=text, exists=True),
    )
    monkeypatch.setattr(Path, "mkdir", lambda self, parents, exist_ok: None)
    return state, FileIncidentContextRepository("controlled-incidents.json")
