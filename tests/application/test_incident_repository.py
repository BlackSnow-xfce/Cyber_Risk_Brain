import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from application import (
    FileIncidentContextRepository,
    IncidentContextConfigurationError,
    IncidentContextCreationService,
    IncidentContextDataError,
)
from core.incident_response import (
    CanonicalAssetReference,
    IncidentLifecycleStatus,
    IncidentRelationship,
    IncidentRelationshipRole,
    SecurityIncidentContext,
)


NOW = datetime(2026, 8, 18, 17, 0, tzinfo=timezone.utc)


def test_file_repository_round_trip_preserves_canonical_context(monkeypatch) -> None:
    state, repository = _repository(monkeypatch)
    context = _context()

    IncidentContextCreationService(repository).create(context)

    loaded = repository.get(context.incident_id)
    assert state["written"] is not None
    assert loaded == context
    assert loaded is not context


def test_unknown_incident_returns_none(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)
    repository.save(_context())

    assert repository.get("missing-incident") is None


def test_list_returns_all_canonical_contexts(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)
    repository.save(_context())

    listed = repository.list()

    assert listed == (_context(),)


def test_missing_configuration_is_controlled() -> None:
    repository = FileIncidentContextRepository(None)

    with pytest.raises(IncidentContextConfigurationError):
        repository.get("incident-1")


def test_missing_file_is_not_a_synthetic_empty_incident(monkeypatch) -> None:
    _, repository = _repository(monkeypatch, source=None)

    with pytest.raises(IncidentContextConfigurationError):
        repository.get("incident-1")


def test_invalid_persisted_contract_is_rejected(monkeypatch) -> None:
    _, repository = _repository(
        monkeypatch,
        source=json.dumps(
            {"contractVersion": "1.0", "incidents": [{"incidentId": "bad"}]}
        ),
    )

    with pytest.raises(IncidentContextDataError):
        repository.get("bad")


def test_list_rejects_invalid_persisted_contract(monkeypatch) -> None:
    _, repository = _repository(
        monkeypatch,
        source=json.dumps(
            {"contractVersion": "1.0", "incidents": [{"incidentId": "bad"}]}
        ),
    )

    with pytest.raises(IncidentContextDataError):
        repository.list()


def test_creation_requires_canonical_context(monkeypatch) -> None:
    _, repository = _repository(monkeypatch)

    with pytest.raises(ValueError):
        IncidentContextCreationService(repository).create(object())  # type: ignore[arg-type]


def _context() -> SecurityIncidentContext:
    return SecurityIncidentContext(
        incident_id="incident-lab-001",
        lifecycle_status=IncidentLifecycleStatus.OPEN,
        source="product-owner:controlled-lab",
        source_reference="product-owner:controlled-lab:incident-lab-001",
        title="Controlled lab incident",
        created_at=NOW,
        updated_at=NOW,
        relationships=(
            IncidentRelationship(
                relationship_id="relationship-asset-001",
                role=IncidentRelationshipRole.AFFECTED_ASSET,
                target=CanonicalAssetReference("asset-lab-metasploitable2-001"),
            ),
        ),
    )


def _repository(monkeypatch, source: str | None = None):
    state: dict[str, object] = {
        "source": source,
        "exists": source is not None,
        "written": None,
    }
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
            written=text,
        ),
    )
    monkeypatch.setattr(Path, "mkdir", lambda self, parents, exist_ok: None)
    return state, FileIncidentContextRepository("controlled-incidents.json")
