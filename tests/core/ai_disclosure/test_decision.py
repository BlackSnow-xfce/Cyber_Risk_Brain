from dataclasses import FrozenInstanceError

import pytest

from core.ai_context import AIContextClassification
from core.ai_disclosure import (
    AI_OUTPUT_DISCLOSURE_DECISION_CONTRACT_VERSION,
    AIOutputDisclosureDecision,
    AIOutputDisclosureDecisionValue,
    AIOutputDisclosureReason,
)
from core.ai_egress import AIModelEgressPurpose


def decision(**overrides):
    values = {
        "purpose": AIModelEgressPurpose.FINDING_EXPLANATION,
        "classification": AIContextClassification.INTERNAL,
        "decision": AIOutputDisclosureDecisionValue.ALLOW,
        "reason": AIOutputDisclosureReason.PURPOSE_ALLOWED,
        "decision_source_reference": "output-policy:finding-explanation",
    }
    values.update(overrides)
    return AIOutputDisclosureDecision(**values)


def test_explicit_allow_is_typed_and_purpose_bound():
    result = decision()
    assert result.decision is AIOutputDisclosureDecisionValue.ALLOW
    assert result.purpose is AIModelEgressPurpose.FINDING_EXPLANATION
    assert result.classification is AIContextClassification.INTERNAL
    assert result.reason is AIOutputDisclosureReason.PURPOSE_ALLOWED
    assert result.contract_version == AI_OUTPUT_DISCLOSURE_DECISION_CONTRACT_VERSION


def test_explicit_deny_is_not_implicit_allow():
    result = decision(
        decision=AIOutputDisclosureDecisionValue.DENY,
        reason=AIOutputDisclosureReason.OUTPUT_SECURITY_CHECK_REQUIRED,
    )
    assert result.decision is AIOutputDisclosureDecisionValue.DENY


@pytest.mark.parametrize(
    "overrides",
    [
        {"purpose": "finding_explanation"},
        {"purpose": None},
        {"classification": None},
        {"classification": "public"},
        {"decision": "allow"},
        {"reason": "purpose_allowed"},
        {"decision_source_reference": ""},
        {"contract_version": "2.0"},
        {
            "decision": AIOutputDisclosureDecisionValue.ALLOW,
            "reason": AIOutputDisclosureReason.OUTPUT_SECURITY_CHECK_REQUIRED,
        },
        {
            "decision": AIOutputDisclosureDecisionValue.DENY,
            "reason": AIOutputDisclosureReason.PURPOSE_ALLOWED,
        },
    ],
)
def test_missing_invalid_or_inconsistent_inputs_fail_closed(overrides):
    with pytest.raises(ValueError):
        decision(**overrides)


def test_purpose_binding_is_not_a_generic_authorization():
    result = decision()
    assert result.purpose is AIModelEgressPurpose.FINDING_EXPLANATION
    assert not hasattr(result, "resource_scope")
    assert not hasattr(result, "tool_permissions")
    assert not hasattr(result, "trusted_after_allow")


def test_allow_does_not_upgrade_trust_or_change_classification():
    result = decision(classification=AIContextClassification.RESTRICTED)
    assert result.decision is AIOutputDisclosureDecisionValue.ALLOW
    assert result.classification is AIContextClassification.RESTRICTED
    assert not hasattr(result, "trust_level")
    assert not hasattr(result, "mark_trusted")


def test_decision_is_immutable_and_provider_independent():
    result = decision()
    with pytest.raises(FrozenInstanceError):
        result.decision = AIOutputDisclosureDecisionValue.DENY
    assert not hasattr(result, "provider")
    assert not hasattr(result, "model")
