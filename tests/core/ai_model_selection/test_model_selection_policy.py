import pytest

from core.ai_egress import AIModelEgressPurpose
from core.ai_model_selection import (
    AIModelExecutionIdentity,
    AIModelSelectionError,
    AIModelSelectionPolicy,
)


def _identity() -> AIModelExecutionIdentity:
    return AIModelExecutionIdentity("openai", "gpt-5.6", "local-binding-1")


def test_approved_finding_explanation_selection_is_exact_and_immutable() -> None:
    decision = AIModelSelectionPolicy().resolve(
        AIModelEgressPurpose.FINDING_EXPLANATION,
    )

    assert decision.purpose is AIModelEgressPurpose.FINDING_EXPLANATION
    assert decision.provider_id == "openai"
    assert decision.model_id == "gpt-5.6"
    assert decision.execution_binding_version == "1.0"
    assert (
        decision.selection_policy_reference
        == "policy:ai-model-selection:finding-explanation:1.0"
    )
    with pytest.raises(AttributeError):
        decision.model_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "purpose",
    ["wrong-purpose", None],
)
def test_wrong_purpose_fails_closed(purpose: object) -> None:
    with pytest.raises(AIModelSelectionError):
        AIModelSelectionPolicy().resolve(purpose)  # type: ignore[arg-type]


def test_policy_owns_the_approved_identity() -> None:
    decision = AIModelSelectionPolicy().resolve(
        AIModelEgressPurpose.FINDING_EXPLANATION,
    )

    assert decision.provider_id == "openai"
    assert decision.model_id == "gpt-5.6"
    assert decision.execution_binding_version == "1.0"


def test_policy_has_no_adapter_candidate_input() -> None:
    with pytest.raises(TypeError):
        AIModelSelectionPolicy().resolve(
            AIModelEgressPurpose.FINDING_EXPLANATION,
            _identity(),  # type: ignore[call-arg]
        )
