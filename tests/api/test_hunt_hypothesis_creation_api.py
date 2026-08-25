import asyncio
import json
from datetime import datetime, timezone

import pytest

from api_app import (
    app,
    get_hunt_hypothesis_creation_service,
    get_local_operator_authenticator,
)
from application import (
    HuntHypothesisConfigurationError,
    HuntHypothesisConflictError,
    HuntHypothesisDataError,
    HuntHypothesisPersistenceError,
)
from application.hunt_hypothesis_creation import HuntHypothesisCreationResult
from application.local_operator import (
    AuthorizationDecision,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    LocalOperatorAuthenticator,
    LocalOperatorAuthorizationError,
)
from core.threat_hunting import (
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)


TOKEN = "a-secure-local-operator-token-value-123456"
NOW = datetime(2026, 8, 24, 14, 0, tzinfo=timezone.utc)


def test_creation_api_returns_exact_canonical_persisted_hypothesis() -> None:
    service = CapturingService()
    status, payload = _request(_payload(), service=service)

    assert status == 201
    assert payload == _hypothesis().to_dict() | {"created_at": "2026-08-24T14:00:00Z"}
    assert service.principal.principal_id == "configured-operator"
    assert service.request.title == _payload()["title"]
    assert set(service.request.__dataclass_fields__) == {
        "title", "statement", "rationale", "target_references", "threat_references"
    }


@pytest.mark.parametrize("authorization", [None, "Bearer invalid"])
def test_creation_api_requires_valid_authentication(authorization) -> None:
    status, payload = _request(_payload(), authorization=authorization)

    assert status == 401
    assert payload == {"detail": "Local Operator authentication failed."}


def test_caller_cannot_submit_authoritative_metadata() -> None:
    for field, value in (
        ("hypothesis_id", "spoofed"),
        ("created_by", "spoofed"),
        ("created_at", NOW.isoformat()),
        ("status", "active"),
        ("contract_version", "9.9"),
        ("permissions", [HUNT_HYPOTHESIS_CREATE_PERMISSION]),
        ("principal_id", "spoofed"),
    ):
        payload = _payload() | {field: value}
        status, _ = _request(payload)
        assert status == 422


def test_authenticated_principal_without_permission_is_forbidden() -> None:
    status, payload = _request(
        _payload(),
        service=FailingService(LocalOperatorAuthorizationError("denied")),
    )
    assert status == 403
    assert payload == {"detail": "The authenticated operator is not authorized."}


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (HuntHypothesisConflictError("path"), 409, "Hunt Hypothesis identity already exists."),
        (HuntHypothesisConfigurationError("path"), 503, "Hunt Hypothesis repository is unavailable."),
        (HuntHypothesisPersistenceError("path"), 503, "Hunt Hypothesis repository is unavailable."),
        (HuntHypothesisDataError("path"), 500, "Hunt Hypothesis repository contains invalid data."),
    ],
)
def test_creation_api_maps_safe_repository_failures(error, status, detail) -> None:
    actual_status, payload = _request(_payload(), service=FailingService(error))
    assert actual_status == status
    assert payload == {"detail": detail}
    assert "path" not in json.dumps(payload)
    assert TOKEN not in json.dumps(payload)


def test_invalid_reference_category_is_unprocessable() -> None:
    payload = _payload()
    payload["target_references"] = [
        {"reference_type": "cve", "reference_id": "CVE-2004-2687"}
    ]
    status, _ = _request(payload)
    assert status == 422


class CapturingService:
    def create(self, request, principal):
        self.request = request
        self.principal = principal
        return HuntHypothesisCreationResult(
            hypothesis=_hypothesis(),
            authorization=AuthorizationDecision(
                principal_id=principal.principal_id,
                operation=HUNT_HYPOTHESIS_CREATE_PERMISSION,
                timestamp=NOW,
                outcome="allowed",
            ),
        )


class FailingService:
    def __init__(self, error) -> None:
        self.error = error

    def create(self, request, principal):
        raise self.error


def _authenticator() -> LocalOperatorAuthenticator:
    return LocalOperatorAuthenticator.from_values(
        mode_enabled="true",
        principal_id="configured-operator",
        display_name="Configured Operator",
        token=TOKEN,
        permissions=HUNT_HYPOTHESIS_CREATE_PERMISSION,
        allowed_origins="http://127.0.0.1:5173",
    )


def _payload() -> dict:
    return {
        "title": "Investigate exposed service activity",
        "statement": "An exposed service may warrant investigation.",
        "rationale": "The hypothesis requires human-led validation.",
        "target_references": [
            {"reference_type": "asset", "reference_id": "asset-1"}
        ],
        "threat_references": [
            {"reference_type": "cve", "reference_id": "CVE-2004-2687"}
        ],
    }


def _hypothesis() -> HuntHypothesis:
    return HuntHypothesis(
        hypothesis_id="hypothesis-12345678-1234-4234-9234-123456789abc",
        title=_payload()["title"],
        statement=_payload()["statement"],
        rationale=_payload()["rationale"],
        target_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, "asset-1"),
        ),
        threat_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.CVE, "CVE-2004-2687"),
        ),
        created_by="configured-operator",
        created_at=NOW,
        status=HuntHypothesisStatus.DRAFT,
    )


def _request(payload, *, service=None, authorization=f"Bearer {TOKEN}"):
    app.dependency_overrides[get_local_operator_authenticator] = _authenticator
    app.dependency_overrides[get_hunt_hypothesis_creation_service] = (
        lambda: service or CapturingService()
    )
    headers = [(b"content-type", b"application/json")]
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("ascii")))
    try:
        return asyncio.run(_asgi_post("/api/hunt-hypotheses", payload, headers))
    finally:
        app.dependency_overrides.pop(get_local_operator_authenticator, None)
        app.dependency_overrides.pop(get_hunt_hypothesis_creation_service, None)


async def _asgi_post(path, payload, headers):
    messages = []
    sent = False
    body = json.dumps(payload).encode("utf-8")

    async def receive():
        nonlocal sent
        if sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )
    start = next(item for item in messages if item["type"] == "http.response.start")
    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))
