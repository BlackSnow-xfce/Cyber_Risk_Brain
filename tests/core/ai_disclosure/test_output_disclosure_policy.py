from dataclasses import FrozenInstanceError

import pytest

from core.ai_context import AIContextClassification
from core.ai_disclosure import (
    AI_OUTPUT_DISCLOSURE_POLICY_CONTRACT_VERSION,
    AI_OUTPUT_DISCLOSURE_POLICY_SOURCE,
    AIOutputDisclosureDecisionValue,
    AIOutputDisclosurePolicy,
    AIOutputDisclosureReason,
)
from core.ai_egress import AIModelEgressPurpose


def test_explicit_finding_explanation_allow():
    result = AIOutputDisclosurePolicy().evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.INTERNAL,
    )
    assert result.decision is AIOutputDisclosureDecisionValue.ALLOW
    assert result.purpose is AIModelEgressPurpose.FINDING_EXPLANATION
    assert result.classification is AIContextClassification.INTERNAL
    assert result.reason is AIOutputDisclosureReason.CLASSIFICATION_ALLOWED
    assert result.decision_source_reference == AI_OUTPUT_DISCLOSURE_POLICY_SOURCE


def test_non_allowed_classification_is_denied_without_downgrade():
    result = AIOutputDisclosurePolicy().evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.RESTRICTED,
    )
    assert result.decision is AIOutputDisclosureDecisionValue.DENY
    assert result.reason is AIOutputDisclosureReason.CLASSIFICATION_NOT_ALLOWED
    assert result.classification is AIContextClassification.RESTRICTED


@pytest.mark.parametrize("value", [None, "internal", object()])
def test_missing_or_invalid_classification_fails_closed(value):
    with pytest.raises(ValueError):
        AIOutputDisclosurePolicy().evaluate(
            AIModelEgressPurpose.FINDING_EXPLANATION,
            value,
        )


@pytest.mark.parametrize("value", [None, "finding_explanation", object()])
def test_missing_or_unsupported_purpose_fails_closed(value):
    with pytest.raises(ValueError):
        AIOutputDisclosurePolicy().evaluate(
            value,
            AIContextClassification.INTERNAL,
        )


def test_identical_inputs_are_deterministic():
    policy = AIOutputDisclosurePolicy()
    first = policy.evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.INTERNAL,
    )
    second = policy.evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.INTERNAL,
    )
    assert first == second


def test_policy_is_immutable_and_not_a_trust_or_authorization_grant():
    policy = AIOutputDisclosurePolicy()
    assert policy.contract_version == AI_OUTPUT_DISCLOSURE_POLICY_CONTRACT_VERSION
    assert not hasattr(policy, "trust_level")
    assert not hasattr(policy, "resource_scope")
    assert not hasattr(policy, "tool_permissions")
    with pytest.raises(FrozenInstanceError):
        policy.decision_source_reference = "provider:safety"


def test_allow_is_not_final_content_disclosure():
    result = AIOutputDisclosurePolicy().evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.INTERNAL,
    )
    assert result.decision is AIOutputDisclosureDecisionValue.ALLOW
    assert not hasattr(result, "content")
    assert not hasattr(result, "output_security_check")
