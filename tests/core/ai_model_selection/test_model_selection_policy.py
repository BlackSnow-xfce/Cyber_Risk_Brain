from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone

import pytest

from core.ai_egress import AIModelEgressPurpose
from core.ai_model_selection import (
    FINDING_EXPLANATION_SELECTION_POLICY_REFERENCE,
    SELECTED_DECISION_REASON,
    AIModelCapability,
    AIModelDeploymentClass,
    AIModelExecutionIdentity,
    AIModelRegistration,
    AIModelRegistrationStatus,
    AIModelRegistry,
    AIModelSelectionError,
    AIModelSelectionPolicy,
    AIProtocolFamily,
    AIProviderFamily,
)


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


def _identity(
    provider: AIProviderFamily = AIProviderFamily.OPENAI,
    model: str = "gpt-5.6",
) -> AIModelExecutionIdentity:
    protocols = {
        AIProviderFamily.OPENAI: AIProtocolFamily.OPENAI_RESPONSES,
        AIProviderFamily.ANTHROPIC: AIProtocolFamily.ANTHROPIC_MESSAGES,
        AIProviderFamily.GOOGLE: AIProtocolFamily.GOOGLE_GENERATE_CONTENT,
        AIProviderFamily.LOCAL_OPENAI_COMPATIBLE: AIProtocolFamily.OPENAI_COMPATIBLE,
    }
    deployment = (
        AIModelDeploymentClass.LOCAL_DEPLOYMENT
        if provider is AIProviderFamily.LOCAL_OPENAI_COMPATIBLE
        else AIModelDeploymentClass.MANAGED_PROVIDER_API
    )
    return AIModelExecutionIdentity(
        provider=provider,
        model_id=model,
        api_protocol_family=protocols[provider],
        deployment_class=deployment,
        execution_binding_version="1.0",
    )


def _registration(
    *,
    provider: AIProviderFamily = AIProviderFamily.OPENAI,
    model: str = "gpt-5.6",
    capabilities: frozenset[AIModelCapability] = frozenset(
        {AIModelCapability.FINDING_EXPLANATION}
    ),
    status: AIModelRegistrationStatus = AIModelRegistrationStatus.ENABLED,
) -> AIModelRegistration:
    return AIModelRegistration(
        identity=_identity(provider, model),
        governance_policy_reference="policy:test:model:1.0",
        enabled_capabilities=capabilities,
        status=status,
    )


def _registry(*registrations: AIModelRegistration) -> AIModelRegistry:
    return AIModelRegistry(tuple(registrations), clock=lambda: NOW)


def test_registered_enabled_model_is_selected_for_exact_capability() -> None:
    decision = _registry(_registration()).select(
        AIModelCapability.FINDING_EXPLANATION,
        provider_id="openai",
        model_id="gpt-5.6",
    )

    assert decision.requested_capability is AIModelCapability.FINDING_EXPLANATION
    assert decision.provider_id == "openai"
    assert decision.model_id == "gpt-5.6"
    assert decision.decided_at == NOW
    assert decision.decision_reason == SELECTED_DECISION_REASON


@pytest.mark.parametrize("provider", list(AIProviderFamily))
def test_initial_provider_families_have_explicit_canonical_identities(
    provider: AIProviderFamily,
) -> None:
    identity = _identity(provider, f"{provider.value}-model")

    assert identity.provider_id == provider.value
    assert identity.api_protocol_family in AIProtocolFamily


@pytest.mark.parametrize(
    ("provider_id", "model_id"),
    [
        ("unknown", "gpt-5.6"),
        ("openai", "unknown"),
        ("anthropic", "gpt-5.6"),
    ],
)
def test_unknown_or_provider_model_mismatch_is_rejected(
    provider_id: str, model_id: str
) -> None:
    registry = _registry(_registration())

    with pytest.raises(AIModelSelectionError):
        registry.select(
            AIModelCapability.FINDING_EXPLANATION,
            provider_id=provider_id,
            model_id=model_id,
        )


def test_disabled_identity_is_rejected() -> None:
    registry = _registry(
        _registration(status=AIModelRegistrationStatus.DISABLED)
    )

    with pytest.raises(AIModelSelectionError, match="disabled"):
        registry.select(
            AIModelCapability.FINDING_EXPLANATION,
            provider_id="openai",
            model_id="gpt-5.6",
        )


def test_capability_mismatch_is_rejected() -> None:
    registry = _registry(
        _registration(
            capabilities=frozenset({AIModelCapability.FINDING_EXPLANATION})
        )
    )

    with pytest.raises(AIModelSelectionError, match="capability"):
        registry.select(
            AIModelCapability.HUNT_HYPOTHESIS_PROPOSAL,
            provider_id="openai",
            model_id="gpt-5.6",
        )


def test_provider_protocol_mismatch_is_rejected() -> None:
    with pytest.raises(AIModelSelectionError, match="do not match"):
        AIModelExecutionIdentity(
            provider=AIProviderFamily.ANTHROPIC,
            model_id="claude-governed",
            api_protocol_family=AIProtocolFamily.OPENAI_RESPONSES,
            deployment_class=AIModelDeploymentClass.MANAGED_PROVIDER_API,
            execution_binding_version="1.0",
        )


def test_unknown_identity_does_not_fallback_to_another_registration() -> None:
    registry = _registry(
        _registration(),
        _registration(
            provider=AIProviderFamily.ANTHROPIC,
            model="claude-governed",
        ),
    )

    with pytest.raises(AIModelSelectionError):
        registry.select(
            AIModelCapability.FINDING_EXPLANATION,
            provider_id="google",
            model_id="missing",
        )


def test_decision_and_registration_are_immutable() -> None:
    registration = _registration()
    decision = _registry(registration).select(
        AIModelCapability.FINDING_EXPLANATION,
        provider_id="openai",
        model_id="gpt-5.6",
    )

    with pytest.raises(FrozenInstanceError):
        decision.decision_reason = "fallback"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        registration.status = AIModelRegistrationStatus.DISABLED  # type: ignore[misc]


def test_safe_audit_projection_is_explicit_and_secret_free() -> None:
    registration = _registration()
    decision = _registry(registration).select(
        AIModelCapability.FINDING_EXPLANATION,
        provider_id="openai",
        model_id="gpt-5.6",
    )

    projection = decision.audit_projection
    assert projection.to_dict() == {
        "capability": "finding_explanation",
        "provider": "openai",
        "model_id": "gpt-5.6",
        "policy_reference": "policy:test:model:1.0",
        "decision_outcome": "selected",
        "decision_reason": SELECTED_DECISION_REASON,
        "timestamp": NOW.isoformat(),
    }
    forbidden_fields = {
        "credential",
        "secret",
        "api_key",
        "prompt",
        "response",
        "authorization",
    }
    for governed_value in (registration, decision.identity, decision, projection):
        field_names = {field.name for field in fields(governed_value)}
        assert not field_names & forbidden_fields


def test_task_0109_policy_remains_exact_and_compatible() -> None:
    decision = AIModelSelectionPolicy().resolve(
        AIModelEgressPurpose.FINDING_EXPLANATION
    )

    assert decision.purpose is AIModelEgressPurpose.FINDING_EXPLANATION
    assert decision.provider_id == "openai"
    assert decision.model_id == "gpt-5.6"
    assert decision.execution_binding_version == "1.0"
    assert (
        decision.selection_policy_reference
        == FINDING_EXPLANATION_SELECTION_POLICY_REFERENCE
    )


@pytest.mark.parametrize("purpose", ["wrong-purpose", None])
def test_wrong_legacy_purpose_fails_closed(purpose: object) -> None:
    with pytest.raises(AIModelSelectionError):
        AIModelSelectionPolicy().resolve(purpose)  # type: ignore[arg-type]


def test_policy_has_no_adapter_candidate_input() -> None:
    with pytest.raises(TypeError):
        AIModelSelectionPolicy().resolve(
            AIModelEgressPurpose.FINDING_EXPLANATION,
            _identity(),  # type: ignore[call-arg]
        )
