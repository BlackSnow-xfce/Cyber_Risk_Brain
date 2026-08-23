import pytest
from fastapi import HTTPException

import api_app
from application import FindingIncidentQueryService
from application.incident_repository import FindingIncidentReference
from core.incident_response import IncidentLifecycleStatus, IncidentRelationshipRole


def test_finding_incidents_serializes_persisted_reference() -> None:
    service = FindingIncidentQueryService(_Repository())

    response = api_app.finding_incidents("finding-001", service)

    assert response[0].model_dump() == {
        "incident_id": "incident-001",
        "relationship_id": "relationship-001",
        "relationship_role": "investigation_candidate",
        "lifecycle_status": "investigating",
    }


def test_finding_without_incident_returns_empty() -> None:
    response = api_app.finding_incidents(
        "missing",
        FindingIncidentQueryService(_Repository(references=())),
    )

    assert response == []


def test_empty_finding_id_is_422() -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.finding_incidents(" ", FindingIncidentQueryService(_Repository()))

    assert captured.value.status_code == 422


class _Repository:
    def __init__(self, references: tuple[FindingIncidentReference, ...] | None = None):
        self._references = (
            references
            if references is not None
            else (
            FindingIncidentReference(
                incident_id="incident-001",
                relationship_id="relationship-001",
                relationship_role=IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
                lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
            ),
            )
        )

    def find_by_finding_id(self, finding_id: str):
        return self._references if finding_id == "finding-001" else ()
