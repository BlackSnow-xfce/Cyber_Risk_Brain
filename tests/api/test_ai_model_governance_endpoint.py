import asyncio
import json

import api_app
from application.ai_model_governance import (
    AIModelAdapterBinding,
    AIModelGovernanceQueryService,
    AIModelSelectionService,
    FileAIModelSelectionAuditSink,
    FileAIModelSelectionStore,
)
from application.local_operator import (
    AI_MODEL_SELECTION_UPDATE_PERMISSION,
    AuthenticatedPrincipal,
    LocalOperatorAuthenticator,
)
from core.ai_model_selection import (
    AIModelCapability,
    AIProviderFamily,
    default_ai_model_registry,
)


def test_governance_endpoint_returns_safe_read_only_contract() -> None:
    status, payload = asyncio.run(_asgi_get("/api/ai-model-governance"))

    assert status == 200
    assert payload["contract_version"] == "1.0"
    assert payload["capabilities"] == [
        "finding_explanation",
        "hunt_hypothesis_proposal",
    ]
    assert [item["provider"] for item in payload["providers"]] == [
        "openai",
        "anthropic",
        "google",
        "local_openai_compatible",
    ]
    openai = payload["providers"][0]["registrations"][0]
    assert openai["model_id"] == "gpt-5.6"
    assert openai["status"] == "enabled"
    assert openai["capabilities"][0]["authorized"] is True
    assert openai["capabilities"][1]["authorized"] is False
    response_keys = _all_keys(payload)
    for forbidden in ("api_key", "credential", "secret", "token", "prompt", "response", "session", "csrf"):
        assert all(forbidden not in key.lower() for key in response_keys)


def test_governance_endpoint_is_get_only_and_does_not_execute_provider(monkeypatch) -> None:
    def forbidden_execution(*args, **kwargs):
        raise AssertionError("provider execution must not occur")

    monkeypatch.setattr(
        api_app.OpenAIFindingExplanationModel,
        "generate",
        forbidden_execution,
    )

    status, _ = asyncio.run(_asgi_get("/api/ai-model-governance"))
    route = next(route for route in api_app.app.routes if route.path == "/api/ai-model-governance")

    assert status == 200
    assert route.methods == {"GET"}


def test_selection_endpoint_persists_and_reload_projects_active_selection(tmp_path) -> None:
    state_path = tmp_path / "selection.json"
    binding = AIModelAdapterBinding(
        AIProviderFamily.OPENAI,
        "gpt-5.6",
        AIModelCapability.FINDING_EXPLANATION,
    )
    store = FileAIModelSelectionStore(str(state_path))
    selection_service = AIModelSelectionService(
        default_ai_model_registry(),
        store,
        FileAIModelSelectionAuditSink(str(tmp_path / "audit.jsonl")),
        adapter_bindings=frozenset({binding}),
        execution_bindings=frozenset({binding}),
    )
    query_service = AIModelGovernanceQueryService(
        adapter_bindings=frozenset({binding}),
        execution_bindings=frozenset({binding}),
        selection_store=store,
    )
    principal = AuthenticatedPrincipal(
        "operator",
        "Operator",
        "human/operator",
        frozenset({AI_MODEL_SELECTION_UPDATE_PERMISSION}),
    )
    api_app.app.dependency_overrides[api_app.get_creation_principal] = lambda: principal
    api_app.app.dependency_overrides[api_app.get_ai_model_selection_service] = lambda: selection_service
    api_app.app.dependency_overrides[api_app.get_ai_model_governance_query_service] = lambda: query_service
    try:
        status, payload = asyncio.run(
            _asgi_request(
                "PUT",
                "/api/ai-model-governance/selections/finding_explanation",
                {"provider": "openai", "model_id": "gpt-5.6"},
            )
        )
        reload_status, reloaded = asyncio.run(_asgi_get("/api/ai-model-governance"))
    finally:
        api_app.app.dependency_overrides.clear()

    assert status == 200
    assert reload_status == 200
    assert payload["providers"][0]["registrations"][0]["capabilities"][0]["active"] is True
    assert reloaded["providers"][0]["registrations"][0]["capabilities"][0]["active"] is True
    assert len(store.list()) == 1


def test_selection_endpoint_requires_authenticated_verified_request() -> None:
    authenticator = LocalOperatorAuthenticator.from_values(
        mode_enabled="true",
        principal_id="operator",
        display_name="Operator",
        token="a-secure-test-token-with-at-least-32-bytes",
        permissions=AI_MODEL_SELECTION_UPDATE_PERMISSION,
        allowed_origins="http://127.0.0.1:5173",
    )
    api_app.app.dependency_overrides[api_app.get_local_operator_authenticator] = lambda: authenticator
    try:
        status, payload = asyncio.run(
            _asgi_request(
                "PUT",
                "/api/ai-model-governance/selections/finding_explanation",
                {"provider": "openai", "model_id": "gpt-5.6"},
            )
        )
    finally:
        api_app.app.dependency_overrides.clear()

    assert status == 401
    assert payload == {"detail": "Local Operator authentication failed."}


async def _asgi_get(path: str) -> tuple[int, dict]:
    return await _asgi_request("GET", path)


async def _asgi_request(
    method: str,
    path: str,
    payload: dict | None = None,
) -> tuple[int, dict]:
    messages: list[dict] = []
    sent = False
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""

    async def receive() -> dict:
        nonlocal sent
        if sent:
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await api_app.app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")] if payload is not None else [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )
    start = next(item for item in messages if item["type"] == "http.response.start")
    body = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
    return start["status"], json.loads(body.decode("utf-8"))


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            nested_key
            for nested in value.values()
            for nested_key in _all_keys(nested)
        }
    if isinstance(value, list):
        return {nested_key for nested in value for nested_key in _all_keys(nested)}
    return set()
