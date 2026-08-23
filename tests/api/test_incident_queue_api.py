import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from api_app import (
    app,
    get_incident_queue_query_service,
)
from application import (
    IncidentContextConfigurationError,
    IncidentContextDataError,
    IncidentQueueQueryService,
    FileIncidentContextRepository,
)
from core.incident_response import (
    CanonicalAssetReference,
    EvidenceReference,
    FindingReference,
    IncidentLifecycleStatus,
    IncidentParticipant,
    IncidentParticipantRole,
    IncidentPrincipalReference,
    IncidentPrincipalType,
    IncidentRelationship,
    IncidentRelationshipRole,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


class Repository:
    def __init__(self, contexts):
        self.contexts = contexts

    def list(self):
        return tuple(self.contexts)


def test_incident_list_http_success_projects_stable_canonical_queue_response() -> None:
    status_code, payload = _request_incidents(
        IncidentQueueQueryService(Repository([_context()]))
    )

    assert status_code == 200
    assert len(payload) == 1
    assert payload[0] == {
        "incident_id": "incident-001",
        "lifecycle_status": "investigating",
        "source": "controlled-lab",
        "source_reference": "source:incident-001",
        "title": "DistCC investigation",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "owner": {"principal_type": "user", "principal_id": "analyst-001"},
        "participant_count": 1,
        "finding_count": 1,
        "asset_count": 1,
        "threat_intelligence_count": 1,
        "evidence_count": 1,
    }
    forbidden = {
        "severity", "risk", "risk_score", "confidence", "confidence_score",
        "compromise", "compromise_state", "threat_actor", "threat_actor_attribution",
    }
    assert forbidden.isdisjoint(payload[0])


def test_incident_list_http_empty_repository_is_successful() -> None:
    status_code, payload = _request_incidents(
        IncidentQueueQueryService(Repository([]))
    )

    assert status_code == 200
    assert payload == []


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (IncidentContextConfigurationError("not configured"), 503),
        (IncidentContextDataError("invalid persisted data"), 500),
    ],
)
def test_incident_list_http_preserves_repository_error_semantics(error, status_code) -> None:
    class FailingService:
        def list(self):
            raise error

    response_status, payload = _request_incidents(FailingService())

    assert response_status == status_code
    assert "detail" in payload


def test_incident_list_http_missing_configuration_is_503() -> None:
    status_code, payload = _request_incidents(
        IncidentQueueQueryService(FileIncidentContextRepository(None))
    )

    assert status_code == 503
    assert "detail" in payload


def test_incident_list_http_invalid_persistence_is_500(monkeypatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, encoding: json.dumps(
            {"contractVersion": "1.0", "incidents": [{"incidentId": "bad"}]}
        ),
    )
    status_code, payload = _request_incidents(
        IncidentQueueQueryService(FileIncidentContextRepository("invalid-incidents.json"))
    )

    assert status_code == 500
    assert "detail" in payload


def _request_incidents(service: object) -> tuple[int, dict | list]:
    app.dependency_overrides[get_incident_queue_query_service] = lambda: service
    try:
        status_code, body = asyncio.run(_asgi_get("/api/incidents"))
    finally:
        app.dependency_overrides.pop(get_incident_queue_query_service, None)
    return status_code, json.loads(body.decode("utf-8"))


async def _asgi_get(path: str) -> tuple[int, bytes]:
    messages: list[dict] = []
    request_sent = False

    async def receive() -> dict:
        nonlocal request_sent
        if request_sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], body


def _context() -> SecurityIncidentContext:
    return SecurityIncidentContext(
        incident_id="incident-001",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="controlled-lab",
        source_reference="source:incident-001",
        title="DistCC investigation",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        owner=IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001"),
        participants=(
            IncidentParticipant(
                principal=IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001"),
                role=IncidentParticipantRole.ANALYST,
            ),
        ),
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
            IncidentRelationship(
                relationship_id="evidence-relationship",
                role=IncidentRelationshipRole.SUPPORTING_EVIDENCE,
                target=EvidenceReference("evidence-001", "1.0"),
            ),
        ),
    )
