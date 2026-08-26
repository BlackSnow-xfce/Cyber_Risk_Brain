import asyncio
import json
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from urllib.parse import urlencode

import api_app
from api_app import (
    app,
    get_hunt_hypothesis_activation_service,
    get_hunt_hypothesis_activation_attempt_auditor,
    get_local_operator_authenticator,
)
from application.hunt_hypothesis_activation import (
    HuntHypothesisActivationAuditError,
    HuntHypothesisActivationAttemptAuditor,
    HuntHypothesisActivationResult,
    HuntHypothesisActivationService,
    HuntHypothesisActivationValidationError,
)
from application.hunt_hypotheses import (
    HuntHypothesisConfigurationError,
    HuntHypothesisDataError,
    HuntHypothesisPersistenceError,
    HuntHypothesisRepositoryNotFoundError,
    HuntHypothesisStateConflictError,
)
from application.local_operator import (
    AuthorizationDecision,
    HUNT_HYPOTHESIS_ACTIVATE_PERMISSION,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    LocalOperatorAuthorizationError,
    LocalOperatorAuthenticator,
)
from application.local_operator_session import (
    LocalOperatorSessionConfiguration,
    LocalOperatorSessionStore,
)
from core.threat_hunting import HuntHypothesis, HuntHypothesisStatus


TOKEN = "a-secure-local-operator-token-value-123456"
ORIGIN = "http://127.0.0.1:5173"
NOW = datetime(2026, 8, 26, 9, 0, tzinfo=timezone.utc)


def test_session_origin_csrf_and_exact_permission_protect_activation() -> None:
    service = RecordingService()
    store = _store()
    cookie, csrf = _session(store)

    status, payload = _activation_request(store, service, cookie, csrf, ORIGIN)
    assert status == 200
    assert payload["status"] == "active"
    assert service.calls == 1
    assert service.principal_id == "product-owner"
    assert service.expected_status is HuntHypothesisStatus.DRAFT

    for origin, token in (
        (None, csrf),
        ("http://malicious.example:5173", csrf),
        (ORIGIN, None),
        (ORIGIN, "wrong"),
    ):
        before = service.calls
        status, _ = _activation_request(store, service, cookie, token, origin)
        assert status == 403
        assert service.calls == before


def test_activation_requires_browser_session_and_rejects_client_authority() -> None:
    service = RecordingService()
    store = _store()
    status, _ = _activation_request(store, service, None, None, None)
    assert status == 401
    assert service.calls == 0

    cookie, csrf = _session(store)
    for field, value in (
        ("created_by", "spoofed"),
        ("principal_id", "spoofed"),
        ("permission", HUNT_HYPOTHESIS_ACTIVATE_PERMISSION),
        ("target_status", "active"),
    ):
        status, _ = _activation_request(
            store,
            service,
            cookie,
            csrf,
            ORIGIN,
            payload={"expected_status": "draft", field: value},
        )
        assert status == 422
    assert service.calls == 0


def test_http_rejections_are_safely_audited_before_service() -> None:
    service = RecordingService()
    store = _store()
    auditor = RecordingAttemptAuditor()

    status, _ = _activation_request(
        store, service, None, None, None, auditor=auditor
    )
    assert status == 401
    assert auditor.records[-1]["reason"] == "authentication_required"

    status, _ = _activation_request(
        store,
        service,
        "predatorai_operator_session=unknown-session-marker",
        None,
        None,
        auditor=auditor,
    )
    assert status == 401
    assert auditor.records[-1]["reason"] == "session_authentication_failed"

    cookie, csrf = _session(store)
    for origin, token in (
        (None, csrf),
        ("http://malicious.example", csrf),
        (ORIGIN, None),
        (ORIGIN, "wrong-csrf-marker"),
    ):
        status, _ = _activation_request(
            store, service, cookie, token, origin, auditor=auditor
        )
        assert status == 403
        assert auditor.records[-1]["reason"] == "request_verification_failed"

    serialized = json.dumps(auditor.records)
    assert "unknown-session-marker" not in serialized
    assert "wrong-csrf-marker" not in serialized
    assert csrf not in serialized
    assert TOKEN not in serialized


def test_invalid_activation_schema_is_audited_once() -> None:
    store = _store()
    cookie, csrf = _session(store)
    auditor = RecordingAttemptAuditor()

    status, _ = _activation_request(
        store,
        RecordingService(),
        cookie,
        csrf,
        ORIGIN,
        payload={"expected_status": "active", "sensitive_marker": "must-not-audit"},
        auditor=auditor,
    )

    assert status == 422
    assert [record["reason"] for record in auditor.records] == [
        "invalid_request_schema"
    ]
    assert "must-not-audit" not in json.dumps(auditor.records)


def test_untrusted_route_identity_is_redacted_from_pre_service_audit() -> None:
    marker = "Bearer-sensitive-credential-marker"
    auditor = RecordingAttemptAuditor()

    status, _ = _activation_request(
        _store(),
        RecordingService(),
        None,
        None,
        None,
        auditor=auditor,
        hypothesis_id=f"hypothesis-{marker}:hostile",
    )

    assert status == 401
    serialized = json.dumps(auditor.records)
    assert marker not in serialized
    assert auditor.records[0]["hypothesis_id"] is None


def test_authenticated_principal_without_activation_permission_is_audited_once() -> None:
    store = _store()
    cookie, csrf = _session(store, authenticator=_authenticator(HUNT_HYPOTHESIS_CREATE_PERMISSION))
    audit_sink = RecordingAuditSink()
    service = HuntHypothesisActivationService(
        MemoryRepository(),
        audit_sink,
        clock=lambda: NOW,
        attempt_id_generator=lambda: "permission-denied-attempt",
    )
    boundary_auditor = RecordingAttemptAuditor()

    status, _ = _activation_request(
        store,
        service,
        cookie,
        csrf,
        ORIGIN,
        auditor=boundary_auditor,
        authenticator=_authenticator(HUNT_HYPOTHESIS_CREATE_PERMISSION),
    )

    assert status == 403
    assert boundary_auditor.records == []
    assert len(audit_sink.events) == 1
    assert audit_sink.events[0]["reason"] == "authorization_denied"


def test_audit_failure_before_http_rejection_fails_closed() -> None:
    status, payload = _activation_request(
        _store(), RecordingService(), None, None, None, auditor=FailingAttemptAuditor()
    )
    assert status == 503
    assert payload == {"detail": "Hunt Hypothesis activation is unavailable."}


def test_activation_maps_safe_not_found_and_stale_failures() -> None:
    store = _store()
    cookie, csrf = _session(store)
    for error, expected_status in (
        (HuntHypothesisRepositoryNotFoundError("private path"), 404),
        (HuntHypothesisStateConflictError("private state"), 409),
    ):
        status, payload = _activation_request(
            store, FailingService(error), cookie, csrf, ORIGIN
        )
        assert status == expected_status
        assert "private" not in json.dumps(payload)
        assert TOKEN not in json.dumps(payload)


def test_activation_maps_validation_availability_integrity_and_audit_failures() -> None:
    store = _store()
    cookie, csrf = _session(store)
    for error, expected_status in (
        (HuntHypothesisActivationValidationError("private"), 422),
        (HuntHypothesisConfigurationError("private"), 503),
        (HuntHypothesisPersistenceError("private"), 503),
        (HuntHypothesisActivationAuditError("private"), 503),
        (HuntHypothesisDataError("private"), 500),
        (LocalOperatorAuthorizationError("private"), 403),
    ):
        status, payload = _activation_request(
            store, FailingService(error), cookie, csrf, ORIGIN
        )
        assert status == expected_status
        assert "private" not in json.dumps(payload)


class RecordingService:
    def __init__(self) -> None:
        self.calls = 0

    def activate(self, request, principal):
        self.calls += 1
        self.principal_id = principal.principal_id
        self.expected_status = request.expected_status
        return HuntHypothesisActivationResult(
            _hypothesis(),
            AuthorizationDecision(
                principal.principal_id,
                HUNT_HYPOTHESIS_ACTIVATE_PERMISSION,
                NOW,
                "allowed",
            ),
        )


class FailingService:
    def __init__(self, error) -> None:
        self.error = error

    def activate(self, request, principal):
        raise self.error


def _authenticator(
    permissions: str = HUNT_HYPOTHESIS_ACTIVATE_PERMISSION,
) -> LocalOperatorAuthenticator:
    return LocalOperatorAuthenticator.from_values(
        mode_enabled="true",
        principal_id="product-owner",
        display_name="Product Owner",
        token=TOKEN,
        permissions=permissions,
        allowed_origins=ORIGIN,
    )


def _store() -> LocalOperatorSessionStore:
    return LocalOperatorSessionStore(
        LocalOperatorSessionConfiguration.from_values(
            enabled="true",
            lifetime_seconds="1800",
            cookie_secure="false",
            cookie_name="predatorai_operator_session",
            allowed_origins=(ORIGIN,),
        ),
        clock=lambda: NOW,
    )


def _session(
    store,
    *,
    authenticator: LocalOperatorAuthenticator | None = None,
) -> tuple[str, str]:
    body = urlencode({"credential": TOKEN}).encode()
    status, headers, _ = _request(
        "POST",
        "/api/operator/session/bootstrap",
        body=body,
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "content-length": str(len(body)),
        },
        store=store,
        authenticator=authenticator,
    )
    assert status == 303
    cookie = SimpleCookie()
    cookie.load(headers["set-cookie"])
    morsel = cookie[store.configuration.cookie_name]
    cookie_header = f"{store.configuration.cookie_name}={morsel.value}"
    status, _, body = _request(
        "GET",
        "/api/operator/session",
        headers={"cookie": cookie_header, "origin": ORIGIN},
        store=store,
        authenticator=authenticator,
    )
    assert status == 200
    return cookie_header, json.loads(body)["csrf_token"]


def _activation_request(
    store,
    service,
    cookie,
    csrf,
    origin,
    *,
    payload=None,
    auditor=None,
    authenticator=None,
    hypothesis_id="hypothesis-001",
):
    headers = {"content-type": "application/json"}
    if cookie is not None:
        headers["cookie"] = cookie
    if csrf is not None:
        headers["x-csrf-token"] = csrf
    if origin is not None:
        headers["origin"] = origin
    status, _, body = _request(
        "POST",
        f"/api/hunt-hypotheses/{hypothesis_id}/activation",
        body=json.dumps(
            {"expected_status": "draft"} if payload is None else payload
        ).encode(),
        headers=headers,
        store=store,
        service=service,
        auditor=auditor,
        authenticator=authenticator,
    )
    return status, json.loads(body)


def _request(
    method,
    path,
    *,
    body=b"",
    headers=None,
    store,
    service=None,
    auditor=None,
    authenticator=None,
):
    app.dependency_overrides[get_local_operator_authenticator] = (
        lambda: authenticator or _authenticator()
    )
    app.dependency_overrides[get_hunt_hypothesis_activation_attempt_auditor] = (
        lambda: auditor or RecordingAttemptAuditor()
    )
    if service is not None:
        app.dependency_overrides[get_hunt_hypothesis_activation_service] = lambda: service
    previous = api_app._local_operator_session_store
    api_app._local_operator_session_store = store
    try:
        return asyncio.run(_asgi_request(method, path, body, headers or {}))
    finally:
        api_app._local_operator_session_store = previous
        app.dependency_overrides.pop(get_local_operator_authenticator, None)
        app.dependency_overrides.pop(get_hunt_hypothesis_activation_service, None)
        app.dependency_overrides.pop(
            get_hunt_hypothesis_activation_attempt_auditor, None
        )


async def _asgi_request(method, path, body, headers):
    messages = []
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    encoded_headers = [(key.encode(), value.encode()) for key, value in headers.items()]
    encoded_headers.append((b"host", b"127.0.0.1:8000"))
    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": encoded_headers,
            "client": ("127.0.0.1", 50000),
            "server": ("127.0.0.1", 8000),
        },
        receive,
        send,
    )
    start = next(item for item in messages if item["type"] == "http.response.start")
    response_headers = {
        key.decode().lower(): value.decode()
        for key, value in start.get("headers", [])
    }
    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return start["status"], response_headers, response_body


def _hypothesis() -> HuntHypothesis:
    return HuntHypothesis(
        hypothesis_id="hypothesis-001",
        title="Fictional hypothesis",
        statement="A fictional signal may warrant investigation.",
        status=HuntHypothesisStatus.ACTIVE,
        created_at=NOW,
        created_by="product-owner",
        target_references=(),
        threat_references=(),
        rationale="Human investigation is required.",
    )


class RecordingAttemptAuditor:
    def __init__(self) -> None:
        self.records = []

    def reject(self, **record) -> None:
        self.records.append(record)


class FailingAttemptAuditor:
    def reject(self, **record) -> None:
        raise HuntHypothesisActivationAuditError("audit unavailable")


class RecordingAuditSink:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> None:
        self.events.append(event)


class MemoryRepository:
    def activate(self, hypothesis_id, expected_status, terminal_callback=None):
        activated = _hypothesis()
        if terminal_callback is not None:
            terminal_callback(activated)
        return activated
