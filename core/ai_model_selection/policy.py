from __future__ import annotations

from dataclasses import dataclass

from core.ai_egress import AIModelEgressPurpose


AI_MODEL_SELECTION_CONTRACT_VERSION = "1.0"
SUPPORTED_PROVIDER_ID = "openai"
SUPPORTED_MODEL_ID = "gpt-5.6"
SUPPORTED_EXECUTION_BINDING_VERSION = "1.0"
FINDING_EXPLANATION_SELECTION_POLICY_REFERENCE = (
    "policy:ai-model-selection:finding-explanation:1.0"
)


class AIModelSelectionError(ValueError):
    """Raised when an execution target is not explicitly approved."""


@dataclass(frozen=True, slots=True)
class AIModelExecutionIdentity:
    provider_id: str
    model_id: str
    execution_binding_version: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (
                self.provider_id,
                self.model_id,
                self.execution_binding_version,
            )
        ):
            raise AIModelSelectionError(
                "Model execution identity requires provider, model and version."
            )


@dataclass(frozen=True, slots=True)
class AIModelSelectionDecision:
    purpose: AIModelEgressPurpose
    identity: AIModelExecutionIdentity
    selection_policy_reference: str
    contract_version: str = AI_MODEL_SELECTION_CONTRACT_VERSION

    @property
    def provider_id(self) -> str:
        return self.identity.provider_id

    @property
    def model_id(self) -> str:
        return self.identity.model_id

    @property
    def execution_binding_version(self) -> str:
        return self.identity.execution_binding_version

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, AIModelEgressPurpose):
            raise AIModelSelectionError("purpose is not supported.")
        if (
            not isinstance(self.selection_policy_reference, str)
            or not self.selection_policy_reference.strip()
        ):
            raise AIModelSelectionError(
                "selection_policy_reference must not be empty."
            )
        if self.contract_version != AI_MODEL_SELECTION_CONTRACT_VERSION:
            raise AIModelSelectionError("Unsupported model-selection contract.")


class AIModelSelectionPolicy:
    """Small positive allowlist for the currently supported AI purpose."""

    _ALLOWED = frozenset(
        {
            (
                AIModelEgressPurpose.FINDING_EXPLANATION,
                SUPPORTED_PROVIDER_ID,
                SUPPORTED_MODEL_ID,
                SUPPORTED_EXECUTION_BINDING_VERSION,
                FINDING_EXPLANATION_SELECTION_POLICY_REFERENCE,
            )
        }
    )

    def resolve(
        self,
        purpose: AIModelEgressPurpose,
    ) -> AIModelSelectionDecision:
        matches = [
            entry
            for entry in self._ALLOWED
            if entry[0] is purpose
        ]
        if len(matches) != 1:
            raise AIModelSelectionError(
                "AI model selection is not explicitly approved."
            )
        return AIModelSelectionDecision(
            purpose=purpose,
            identity=AIModelExecutionIdentity(
                provider_id=matches[0][1],
                model_id=matches[0][2],
                execution_binding_version=matches[0][3],
            ),
            selection_policy_reference=matches[0][4],
        )
