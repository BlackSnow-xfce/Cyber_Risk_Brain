import json
from datetime import datetime, timezone

import pytest

from application.local_operator import (
    AI_MODEL_SELECTION_UPDATE_PERMISSION,
    AuthenticatedPrincipal,
    LocalOperatorAuthorizationError,
)
from core.ai_model_selection import (
    AIModelCapability,
    AIModelDeploymentClass,
    AIModelExecutionIdentity,
    AIModelRegistration,
    AIModelRegistrationStatus,
    AIModelRegistry,
    AIProtocolFamily,
    AIProviderFamily,
)
from application.ai_model_governance import (
    AIModelAdapterBinding,
    AIModelGovernanceQueryService,
    AIModelSelectionService,
    AIModelSelectionUnavailableError,
    FileAIModelSelectionAuditSink,
    FileAIModelSelectionStore,
    PersistedAIModelSelectionPolicy,
)
from core.ai_egress import AIModelEgressPurpose
from core.ai_model_selection import AIModelSelectionError


def test_default_visibility_projects_real_registry_and_all_provider_families() -> None:
    result = AIModelGovernanceQueryService().get_visibility()

    assert [item.provider for item in result.providers] == [
        "openai",
        "anthropic",
        "google",
        "local_openai_compatible",
    ]
    assert result.capabilities == (
        "finding_explanation",
        "hunt_hypothesis_proposal",
    )
    openai = result.providers[0]
    assert openai.governance_status == "registered"
    assert [item.model_id for item in openai.registrations] == ["gpt-5.6"]
    assert openai.registrations[0].capabilities[0].active is True
    assert all(not item.registrations for item in result.providers[1:])
    assert all(item.governance_status == "foundation_only" for item in result.providers[1:])


def test_adapter_and_execution_availability_are_separate_from_authorization() -> None:
    binding = AIModelAdapterBinding(
        AIProviderFamily.OPENAI,
        "gpt-5.6",
        AIModelCapability.FINDING_EXPLANATION,
    )

    adapter_only = AIModelGovernanceQueryService(
        adapter_bindings=frozenset({binding})
    ).get_visibility().providers[0].registrations[0]
    executable = AIModelGovernanceQueryService(
        adapter_bindings=frozenset({binding}),
        execution_bindings=frozenset({binding}),
    ).get_visibility().providers[0].registrations[0]

    finding = adapter_only.capabilities[0]
    proposal = adapter_only.capabilities[1]
    assert (finding.authorized, finding.adapter_available, finding.execution_available) == (True, True, False)
    assert (proposal.authorized, proposal.adapter_available, proposal.execution_available) == (False, False, False)
    assert executable.capabilities[0].execution_available is True


def test_disabled_registration_remains_visible_but_not_executable() -> None:
    identity = AIModelExecutionIdentity(
        provider=AIProviderFamily.GOOGLE,
        model_id="governed-google-model",
        api_protocol_family=AIProtocolFamily.GOOGLE_GENERATE_CONTENT,
        deployment_class=AIModelDeploymentClass.MANAGED_PROVIDER_API,
        execution_binding_version="1.0",
    )
    registration = AIModelRegistration(
        identity=identity,
        governance_policy_reference="policy:test:google:1.0",
        enabled_capabilities=frozenset({AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL}),
        status=AIModelRegistrationStatus.DISABLED,
    )
    binding = AIModelAdapterBinding(
        AIProviderFamily.GOOGLE,
        identity.model_id,
        AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL,
    )

    result = AIModelGovernanceQueryService(
        AIModelRegistry((registration,)),
        adapter_bindings=frozenset({binding}),
        execution_bindings=frozenset({binding}),
    ).get_visibility()
    projected = result.providers[2].registrations[0]

    assert projected.status == "disabled"
    assert projected.governance_status == "disabled"
    assert projected.capabilities[1].execution_available is False


def test_governed_selection_persists_and_is_active_after_reload(tmp_path) -> None:
    state_path = tmp_path / "selection.json"
    audit_path = tmp_path / "audit.jsonl"
    binding = AIModelAdapterBinding(
        AIProviderFamily.OPENAI,
        "gpt-5.6",
        AIModelCapability.FINDING_EXPLANATION,
    )
    service = _selection_service(state_path, audit_path, binding=binding)

    result = service.change(
        AIModelCapability.FINDING_EXPLANATION,
        "openai",
        "gpt-5.6",
        _principal(AI_MODEL_SELECTION_UPDATE_PERMISSION),
    )
    visibility = AIModelGovernanceQueryService(
        adapter_bindings=frozenset({binding}),
        execution_bindings=frozenset({binding}),
        selection_store=FileAIModelSelectionStore(str(state_path)),
    ).get_visibility()

    assert result.selection.model_id == "gpt-5.6"
    assert visibility.providers[0].registrations[0].capabilities[0].active is True
    assert FileAIModelSelectionStore(str(state_path)).list() == (result.selection,)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["outcome"] == "selected"
    assert audit["previous_model_id"] is None
    assert audit["new_model_id"] == "gpt-5.6"
    assert not set(audit) & {"secret", "token", "credential", "prompt", "response"}


@pytest.mark.parametrize(
    ("provider", "model", "capability", "error_type"),
    [
        ("unknown", "unknown", AIModelCapability.FINDING_EXPLANATION, AIModelSelectionError),
        ("openai", "unknown", AIModelCapability.FINDING_EXPLANATION, AIModelSelectionError),
        ("openai", "gpt-5.6", AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL, AIModelSelectionError),
    ],
)
def test_unknown_and_capability_mismatched_selections_fail_without_fallback(
    tmp_path,
    provider,
    model,
    capability,
    error_type,
) -> None:
    binding = AIModelAdapterBinding(
        AIProviderFamily.OPENAI,
        "gpt-5.6",
        AIModelCapability.FINDING_EXPLANATION,
    )
    state_path = tmp_path / "state.json"
    service = _selection_service(
        state_path,
        tmp_path / "audit.jsonl",
        binding=binding,
    )

    with pytest.raises(error_type):
        service.change(
            capability,
            provider,
            model,
            _principal(AI_MODEL_SELECTION_UPDATE_PERMISSION),
        )

    assert FileAIModelSelectionStore(str(state_path)).list() == ()


@pytest.mark.parametrize("available", ["adapter", "execution"])
def test_missing_adapter_or_execution_availability_is_rejected(tmp_path, available) -> None:
    binding = AIModelAdapterBinding(
        AIProviderFamily.OPENAI,
        "gpt-5.6",
        AIModelCapability.FINDING_EXPLANATION,
    )
    service = _selection_service(
        tmp_path / "state.json",
        tmp_path / "audit.jsonl",
        binding=binding,
        adapter_available=available == "execution",
        execution_available=False,
    )

    with pytest.raises(AIModelSelectionUnavailableError):
        service.change(
            AIModelCapability.FINDING_EXPLANATION,
            "openai",
            "gpt-5.6",
            _principal(AI_MODEL_SELECTION_UPDATE_PERMISSION),
        )


def test_disabled_model_and_missing_permission_are_rejected(tmp_path) -> None:
    registration = _google_registration(AIModelRegistrationStatus.DISABLED)
    binding = AIModelAdapterBinding(
        AIProviderFamily.GOOGLE,
        registration.identity.model_id,
        AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL,
    )
    service = AIModelSelectionService(
        AIModelRegistry((registration,)),
        FileAIModelSelectionStore(str(tmp_path / "state.json")),
        FileAIModelSelectionAuditSink(str(tmp_path / "audit.jsonl")),
        adapter_bindings=frozenset({binding}),
        execution_bindings=frozenset({binding}),
    )

    with pytest.raises(AIModelSelectionError, match="disabled"):
        service.change(
            AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL,
            "google",
            registration.identity.model_id,
            _principal(AI_MODEL_SELECTION_UPDATE_PERMISSION),
        )
    with pytest.raises(LocalOperatorAuthorizationError):
        service.change(
            AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL,
            "google",
            registration.identity.model_id,
            _principal(),
        )


def test_finding_explanation_policy_consumes_persisted_governed_selection(tmp_path) -> None:
    binding = AIModelAdapterBinding(
        AIProviderFamily.OPENAI,
        "gpt-5.6",
        AIModelCapability.FINDING_EXPLANATION,
    )
    service = _selection_service(tmp_path / "state.json", tmp_path / "audit.jsonl", binding=binding)
    service.change(
        AIModelCapability.FINDING_EXPLANATION,
        "openai",
        "gpt-5.6",
        _principal(AI_MODEL_SELECTION_UPDATE_PERMISSION),
    )

    decision = PersistedAIModelSelectionPolicy(service).resolve(
        AIModelEgressPurpose.FINDING_EXPLANATION
    )

    assert decision.provider_id == "openai"
    assert decision.model_id == "gpt-5.6"


def _selection_service(
    state_path,
    audit_path,
    *,
    binding,
    adapter_available=True,
    execution_available=True,
):
    return AIModelSelectionService(
        AIModelRegistry((
            AIModelRegistration(
                identity=AIModelExecutionIdentity(
                    provider=AIProviderFamily.OPENAI,
                    model_id="gpt-5.6",
                    api_protocol_family=AIProtocolFamily.OPENAI_RESPONSES,
                    deployment_class=AIModelDeploymentClass.MANAGED_PROVIDER_API,
                    execution_binding_version="1.0",
                ),
                governance_policy_reference="policy:test:openai:1.0",
                enabled_capabilities=frozenset({AIModelCapability.FINDING_EXPLANATION}),
                status=AIModelRegistrationStatus.ENABLED,
            ),
        )),
        FileAIModelSelectionStore(str(state_path)),
        FileAIModelSelectionAuditSink(str(audit_path)),
        adapter_bindings=frozenset({binding}) if adapter_available else frozenset(),
        execution_bindings=frozenset({binding}) if execution_available else frozenset(),
        clock=lambda: datetime(2026, 8, 25, 15, 0, tzinfo=timezone.utc),
    )


def _principal(*permissions):
    return AuthenticatedPrincipal(
        principal_id="operator",
        display_name="Operator",
        principal_type="human/operator",
        permissions=frozenset(permissions),
    )


def _google_registration(status):
    return AIModelRegistration(
        identity=AIModelExecutionIdentity(
            provider=AIProviderFamily.GOOGLE,
            model_id="governed-google-model",
            api_protocol_family=AIProtocolFamily.GOOGLE_GENERATE_CONTENT,
            deployment_class=AIModelDeploymentClass.MANAGED_PROVIDER_API,
            execution_binding_version="1.0",
        ),
        governance_policy_reference="policy:test:google:1.0",
        enabled_capabilities=frozenset({AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL}),
        status=status,
    )
