from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

import api_app
from application import IncidentCommandCenterQueryService
from application import FileIncidentContextRepository
from core.incident_response import (
    IncidentLifecycleStatus,
    SecurityIncidentContext,
)


NOW = datetime(2026, 8, 18, 16, 0, tzinfo=timezone.utc)


def test_incident_command_center_get_serializes_read_model_without_engines() -> None:
    calls: list[str] = []

    def reader(incident_id: str) -> SecurityIncidentContext:
        calls.append(incident_id)
        return SecurityIncidentContext(
            incident_id=incident_id,
            lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
            source="soc",
            source_reference="soc:incident-001",
            title="Controlled incident",
            created_at=NOW,
            updated_at=NOW,
        )

    response = api_app.incident_command_center(
        "incident-001",
        IncidentCommandCenterQueryService(),
        reader,
    )
    payload = response.model_dump(mode="json")

    assert calls == ["incident-001"]
    assert payload["contract_version"] == "1.0"
    assert payload["incident"]["incident_id"] == "incident-001"
    assert payload["incident"]["lifecycle_status"] == "investigating"
    assert payload["completeness"]["status"] == "no_data"
    assert payload["findings"] == []
    assert payload["notes"] == []
    assert payload["activities"] == []


def test_unknown_incident_is_404() -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.incident_command_center(
            "missing-incident",
            IncidentCommandCenterQueryService(),
            lambda _incident_id: None,
        )

    assert captured.value.status_code == 404
    assert captured.value.detail == "Incident was not found."


def test_persisted_incident_is_returned_by_command_center_endpoint(monkeypatch) -> None:
    from pathlib import Path

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
        lambda self, text, encoding: state.update(
            source=text,
            exists=True,
        ),
    )
    monkeypatch.setattr(Path, "mkdir", lambda self, parents, exist_ok: None)
    repository = FileIncidentContextRepository("controlled-incidents.json")
    context = SecurityIncidentContext(
        incident_id="incident-persisted",
        lifecycle_status=IncidentLifecycleStatus.OPEN,
        source="controlled-lab",
        source_reference="controlled-lab:incident-persisted",
        title="Persisted incident",
        created_at=NOW,
        updated_at=NOW,
    )
    repository.save(context)

    response = api_app.incident_command_center(
        context.incident_id,
        IncidentCommandCenterQueryService(),
        repository.get,
    )

    assert response.incident.incident_id == context.incident_id
    assert response.incident.lifecycle_status == "open"


def test_empty_incident_id_is_422() -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.incident_command_center(
            " ",
            IncidentCommandCenterQueryService(),
            lambda _incident_id: None,
        )

    assert captured.value.status_code == 422


def test_router_does_not_run_predator_engine(monkeypatch) -> None:
    def fail_engine() -> None:
        raise AssertionError("Engines must not run for the read endpoint.")

    monkeypatch.setattr(api_app.engine, "run", fail_engine)
    response = api_app.incident_command_center(
        "incident-001",
        IncidentCommandCenterQueryService(),
        lambda _incident_id: SecurityIncidentContext(
            incident_id="incident-001",
            lifecycle_status=IncidentLifecycleStatus.OPEN,
            source="soc",
            source_reference="soc:incident-001",
            title="Read-only incident",
            created_at=NOW,
            updated_at=NOW,
        ),
    )

    assert response.incident.incident_id == "incident-001"
