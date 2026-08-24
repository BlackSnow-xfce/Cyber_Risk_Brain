import asyncio
import json

import pytest

from api_app import app, get_hunt_hypothesis_reference_resolution_service
from application import (
    HuntHypothesisNotFoundError,
    HuntHypothesisReferenceIntegrityError,
    HuntHypothesisReferenceResolution,
    HuntHypothesisReferenceResolutionResult,
    HuntHypothesisReferenceResolutionStatus,
)
from core.threat_hunting import HuntHypothesisReferenceType


class Service:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    def resolve(self, hypothesis_id: str):
        if self.error:
            raise self.error
        return self.result


def test_resolution_api_returns_exact_typed_projection() -> None:
    result = HuntHypothesisReferenceResolutionResult(
        hypothesis_id="hypothesis-001",
        references=(
            HuntHypothesisReferenceResolution(
                reference_type=HuntHypothesisReferenceType.FINDING,
                reference_id="finding-001",
                resolution_status=HuntHypothesisReferenceResolutionStatus.RESOLVED,
                authoritative_source="findings",
                resolved_identity="finding-001",
                source_reference="greenbone",
            ),
            HuntHypothesisReferenceResolution(
                reference_type=HuntHypothesisReferenceType.CVE,
                reference_id="CVE-2026-1234",
                resolution_status=(
                    HuntHypothesisReferenceResolutionStatus.SOURCE_UNAVAILABLE
                ),
                authoritative_source="threat_intelligence",
            ),
        ),
    )

    status, payload = _request(Service(result=result))

    assert status == 200
    assert payload == {
        "hypothesis_id": "hypothesis-001",
        "references": [
            {
                "reference_type": "finding",
                "reference_id": "finding-001",
                "resolution_status": "resolved",
                "authoritative_source": "findings",
                "resolved_identity": "finding-001",
                "source_reference": "greenbone",
            },
            {
                "reference_type": "cve",
                "reference_id": "CVE-2026-1234",
                "resolution_status": "source_unavailable",
                "authoritative_source": "threat_intelligence",
                "resolved_identity": None,
                "source_reference": None,
            },
        ],
    }
    assert payload["references"][1]["resolution_status"] != "not_found"


def test_resolution_api_returns_404_for_unknown_hypothesis() -> None:
    status, payload = _request(
        Service(error=HuntHypothesisNotFoundError("internal identity"))
    )

    assert status == 404
    assert payload == {"detail": "Hunt Hypothesis was not found."}


@pytest.mark.parametrize(
    "error",
    [
        HuntHypothesisReferenceIntegrityError("duplicate finding secret"),
    ],
)
def test_resolution_api_integrity_failure_is_generic(error) -> None:
    status, payload = _request(Service(error=error))

    assert status == 500
    assert payload == {
        "detail": "Hunt Hypothesis reference resolution failed integrity checks."
    }
    assert "duplicate finding secret" not in json.dumps(payload)


def _request(service: object) -> tuple[int, object]:
    dependency = get_hunt_hypothesis_reference_resolution_service
    app.dependency_overrides[dependency] = lambda: service
    try:
        status, body = asyncio.run(
            _asgi_get(
                "/api/hunt-hypotheses/hypothesis-001/reference-resolution"
            )
        )
    finally:
        app.dependency_overrides.pop(dependency, None)
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
