from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from core.ai_egress import AIModelEgressPurpose


AI_MODEL_SELECTION_CONTRACT_VERSION = "2.0"
SUPPORTED_PROVIDER_ID = "openai"
SUPPORTED_MODEL_ID = "gpt-5.6"
SUPPORTED_EXECUTION_BINDING_VERSION = "1.0"
FINDING_EXPLANATION_SELECTION_POLICY_REFERENCE = (
    "policy:ai-model-selection:finding-explanation:1.0"
)
SELECTED_DECISION_REASON = "explicit_enabled_registration_for_exact_capability"


class AIModelSelectionError(ValueError):
    """Raised when an execution target is not explicitly approved."""


class AIProviderFamily(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL_OPENAI_COMPATIBLE = "local_openai_compatible"


class AIModelCapability(StrEnum):
    FINDING_EXPLANATION = "finding_explanation"
    HUNT_HYPOTHESIS_PROPOSAL = "hunt_hypothesis_proposal"


class AIProtocolFamily(StrEnum):
    OPENAI_RESPONSES = "openai_responses"
    ANTHROPIC_MESSAGES = "anthropic_messages"
    GOOGLE_GENERATE_CONTENT = "google_generate_content"
    OPENAI_COMPATIBLE = "openai_compatible"


class AIModelDeploymentClass(StrEnum):
    MANAGED_PROVIDER_API = "managed_provider_api"
    LOCAL_DEPLOYMENT = "local_deployment"


class AIModelRegistrationStatus(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class AIModelExecutionIdentity:
    provider: AIProviderFamily
    model_id: str
    api_protocol_family: AIProtocolFamily
    deployment_class: AIModelDeploymentClass
    execution_binding_version: str

    @property
    def provider_id(self) -> str:
        return self.provider.value

    def __post_init__(self) -> None:
        if not isinstance(self.provider, AIProviderFamily):
            raise AIModelSelectionError("provider is not supported.")
        if not isinstance(self.api_protocol_family, AIProtocolFamily):
            raise AIModelSelectionError("API protocol family is not supported.")
        if not isinstance(self.deployment_class, AIModelDeploymentClass):
            raise AIModelSelectionError("deployment class is not supported.")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.model_id, self.execution_binding_version)
        ):
            raise AIModelSelectionError(
                "Model execution identity requires model and binding version."
            )
        expected_protocol = {
            AIProviderFamily.OPENAI: AIProtocolFamily.OPENAI_RESPONSES,
            AIProviderFamily.ANTHROPIC: AIProtocolFamily.ANTHROPIC_MESSAGES,
            AIProviderFamily.GOOGLE: AIProtocolFamily.GOOGLE_GENERATE_CONTENT,
            AIProviderFamily.LOCAL_OPENAI_COMPATIBLE: AIProtocolFamily.OPENAI_COMPATIBLE,
        }[self.provider]
        if self.api_protocol_family is not expected_protocol:
            raise AIModelSelectionError(
                "Provider and API protocol family do not match."
            )
        if (
            self.provider is AIProviderFamily.LOCAL_OPENAI_COMPATIBLE
            and self.deployment_class is not AIModelDeploymentClass.LOCAL_DEPLOYMENT
        ):
            raise AIModelSelectionError(
                "Local OpenAI-compatible models require local deployment."
            )


@dataclass(frozen=True, slots=True)
class AIModelRegistration:
    identity: AIModelExecutionIdentity
    governance_policy_reference: str
    enabled_capabilities: frozenset[AIModelCapability]
    status: AIModelRegistrationStatus

    def __post_init__(self) -> None:
        if not isinstance(self.identity, AIModelExecutionIdentity):
            raise AIModelSelectionError("registration identity is invalid.")
        if (
            not isinstance(self.governance_policy_reference, str)
            or not self.governance_policy_reference.strip()
        ):
            raise AIModelSelectionError("governance policy reference is required.")
        if not isinstance(self.enabled_capabilities, frozenset) or not self.enabled_capabilities:
            raise AIModelSelectionError("registration requires explicit capabilities.")
        if any(
            not isinstance(capability, AIModelCapability)
            for capability in self.enabled_capabilities
        ):
            raise AIModelSelectionError("registration capability is invalid.")
        if not isinstance(self.status, AIModelRegistrationStatus):
            raise AIModelSelectionError("registration status is invalid.")


@dataclass(frozen=True, slots=True)
class AIModelSelectionAuditProjection:
    capability: str
    provider: str
    model_id: str
    policy_reference: str
    decision_outcome: str
    decision_reason: str
    timestamp: datetime

    def to_dict(self) -> dict[str, str]:
        return {
            "capability": self.capability,
            "provider": self.provider,
            "model_id": self.model_id,
            "policy_reference": self.policy_reference,
            "decision_outcome": self.decision_outcome,
            "decision_reason": self.decision_reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class AIModelSelectionDecision:
    requested_capability: AIModelCapability
    identity: AIModelExecutionIdentity
    selection_policy_reference: str
    decided_at: datetime
    decision_reason: str
    contract_version: str = AI_MODEL_SELECTION_CONTRACT_VERSION

    @property
    def purpose(self) -> AIModelEgressPurpose:
        if self.requested_capability is AIModelCapability.FINDING_EXPLANATION:
            return AIModelEgressPurpose.FINDING_EXPLANATION
        raise AIModelSelectionError(
            "Capability has no approved model-egress purpose binding."
        )

    @property
    def provider_id(self) -> str:
        return self.identity.provider_id

    @property
    def model_id(self) -> str:
        return self.identity.model_id

    @property
    def execution_binding_version(self) -> str:
        return self.identity.execution_binding_version

    @property
    def audit_projection(self) -> AIModelSelectionAuditProjection:
        return AIModelSelectionAuditProjection(
            capability=self.requested_capability.value,
            provider=self.provider_id,
            model_id=self.model_id,
            policy_reference=self.selection_policy_reference,
            decision_outcome="selected",
            decision_reason=self.decision_reason,
            timestamp=self.decided_at,
        )

    def __post_init__(self) -> None:
        if not isinstance(self.requested_capability, AIModelCapability):
            raise AIModelSelectionError("requested capability is not supported.")
        if not isinstance(self.identity, AIModelExecutionIdentity):
            raise AIModelSelectionError("selection identity is invalid.")
        if (
            not isinstance(self.selection_policy_reference, str)
            or not self.selection_policy_reference.strip()
        ):
            raise AIModelSelectionError(
                "selection_policy_reference must not be empty."
            )
        if not isinstance(self.decided_at, datetime) or self.decided_at.tzinfo is None:
            raise AIModelSelectionError("decision timestamp must be timezone-aware.")
        if not isinstance(self.decision_reason, str) or not self.decision_reason.strip():
            raise AIModelSelectionError("decision reason must not be empty.")
        if self.contract_version != AI_MODEL_SELECTION_CONTRACT_VERSION:
            raise AIModelSelectionError("Unsupported model-selection contract.")


class AIModelRegistry:
    """Default-deny registry of exact governed provider/model identities."""

    def __init__(
        self,
        registrations: tuple[AIModelRegistration, ...],
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not isinstance(registrations, tuple):
            raise AIModelSelectionError("registrations must be an immutable tuple.")
        identities = [
            (item.identity.provider_id, item.identity.model_id)
            for item in registrations
            if isinstance(item, AIModelRegistration)
        ]
        if len(identities) != len(registrations) or len(set(identities)) != len(identities):
            raise AIModelSelectionError("registry identities must be valid and unique.")
        self._registrations = registrations
        self._clock = clock

    @property
    def registrations(self) -> tuple[AIModelRegistration, ...]:
        """Return the immutable governed registrations for read-only projection."""
        return self._registrations

    def select(
        self,
        capability: AIModelCapability,
        *,
        provider_id: str,
        model_id: str,
    ) -> AIModelSelectionDecision:
        if not isinstance(capability, AIModelCapability):
            raise AIModelSelectionError("requested capability is not supported.")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise AIModelSelectionError("provider identity is required.")
        if not isinstance(model_id, str) or not model_id.strip():
            raise AIModelSelectionError("model identity is required.")
        matches = tuple(
            registration
            for registration in self._registrations
            if registration.identity.provider_id == provider_id
            and registration.identity.model_id == model_id
        )
        if len(matches) != 1:
            raise AIModelSelectionError(
                "AI model identity is not explicitly registered."
            )
        registration = matches[0]
        if registration.status is not AIModelRegistrationStatus.ENABLED:
            raise AIModelSelectionError("AI model identity is disabled.")
        if capability not in registration.enabled_capabilities:
            raise AIModelSelectionError(
                "AI model capability is not explicitly approved."
            )
        decided_at = self._clock()
        return AIModelSelectionDecision(
            requested_capability=capability,
            identity=registration.identity,
            selection_policy_reference=registration.governance_policy_reference,
            decided_at=decided_at,
            decision_reason=SELECTED_DECISION_REASON,
        )


def default_ai_model_registry() -> AIModelRegistry:
    return AIModelRegistry(
        (
            AIModelRegistration(
                identity=AIModelExecutionIdentity(
                    provider=AIProviderFamily.OPENAI,
                    model_id=SUPPORTED_MODEL_ID,
                    api_protocol_family=AIProtocolFamily.OPENAI_RESPONSES,
                    deployment_class=AIModelDeploymentClass.MANAGED_PROVIDER_API,
                    execution_binding_version=SUPPORTED_EXECUTION_BINDING_VERSION,
                ),
                governance_policy_reference=(
                    FINDING_EXPLANATION_SELECTION_POLICY_REFERENCE
                ),
                enabled_capabilities=frozenset(
                    {AIModelCapability.FINDING_EXPLANATION}
                ),
                status=AIModelRegistrationStatus.ENABLED,
            ),
        )
    )


class AIModelSelectionPolicy:
    """TASK-0109-compatible policy backed by the governed registry."""

    def __init__(self, registry: AIModelRegistry | None = None) -> None:
        self._registry = registry or default_ai_model_registry()

    def resolve(
        self,
        purpose: AIModelEgressPurpose,
    ) -> AIModelSelectionDecision:
        if purpose is not AIModelEgressPurpose.FINDING_EXPLANATION:
            raise AIModelSelectionError("purpose is not supported.")
        return self._registry.select(
            AIModelCapability.FINDING_EXPLANATION,
            provider_id=SUPPORTED_PROVIDER_ID,
            model_id=SUPPORTED_MODEL_ID,
        )
