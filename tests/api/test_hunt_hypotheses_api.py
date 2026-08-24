import asyncio
import json
from datetime import datetime, timezone

import pytest

from api_app import app, get_hunt_hypothesis_query_service
from application import (
    FileHuntHypothesisRepository,
    HuntHypothesisConfigurationError,
    HuntHypothesisDataError,
    HuntHypothesisQueryService,
)
from core.threat_hunting import (
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)


class Repository:
    def __init__(self, hypotheses) -> None:
        self.hypotheses = hypotheses

    def list(self):
        return tuple(self.hypotheses)


def test_hunt_hypotheses_api_returns_canonical_collection() -> None:
    status, payload = _request(
        HuntHypothesisQueryService(Repository([_hypothesis()]))
    )

    assert status == 200
    expected = _hypothesis().to_dict()
    expected["created_at"] = "2026-08-24T10:00:00Z"
    assert payload == [expected]


def test_hunt_hypotheses_api_returns_empty_collection() -> None:
    status, payload = _request(HuntHypothesisQueryService(Repository([])))

    assert status == 200
    assert payload == []


def test_hunt_hypotheses_api_returns_503_when_unconfigured() -> None:
    status, payload = _request(
        HuntHypothesisQueryService(FileHuntHypothesisRepository(None))
    )

    assert status == 503
    assert "not configured" in payload["detail"]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (HuntHypothesisConfigurationError("unavailable"), 503),
        (HuntHypothesisDataError("invalid"), 500),
    ],
)
def test_hunt_hypotheses_api_preserves_failure_semantics(error, expected_status) -> None:
    class FailingService:
        def list(self):
            raise error

    status, payload = _request(FailingService())

    assert status == expected_status
    assert "detail" in payload


def _request(service: object) -> tuple[int, object]:
    app.dependency_overrides[get_hunt_hypothesis_query_service] = lambda: service
    try:
        status, body = asyncio.run(_asgi_get("/api/hunt-hypotheses"))
    finally:
        app.dependency_overrides.pop(get_hunt_hypothesis_query_service, None)
    return status, json.loads(body.decode("utf-8"))


async def _asgi_get(path: str) -> tuple[int, bytes]:
    messages: list[dict] = []
    sent = False

    async def receive() -> dict:
        nonlocal sent
        if sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        sent = True
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
    start = next(item for item in messages if item["type"] == "http.response.start")
    body = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return start["status"], body


def _hypothesis() -> HuntHypothesis:
    return HuntHypothesis(
        hypothesis_id="hypothesis-001",
        title="Administrative execution from an exposed service",
        statement="A service account may be executing unexpected commands.",
        status=HuntHypothesisStatus.ACTIVE,
        created_at=datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc),
        created_by="threat-hunter-001",
        target_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, "asset-001"),
        ),
        threat_references=(
            HuntHypothesisReference(
                HuntHypothesisReferenceType.TECHNIQUE, "T1059"
            ),
        ),
        rationale="Unexpected command execution warrants investigation.",
    )
