from dataclasses import FrozenInstanceError

import pytest

from core.ai_context import AIContextClassification
from core.ai_disclosure import (
    AIOutputSecurityDecision,
    AIOutputSecurityReason,
    FindingExplanationOutputSecurityGuard,
)
from core.ai_egress import AIModelEgressPurpose


def evaluate(text):
    return FindingExplanationOutputSecurityGuard().evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.INTERNAL,
        text,
    )


def test_normal_explanation_passes():
    result = evaluate("The finding indicates an outdated service.")
    assert result.decision is AIOutputSecurityDecision.PASS
    assert result.reason is AIOutputSecurityReason.OUTPUT_CLEAR


@pytest.mark.parametrize(
    "text",
    [
        "The password and credential terms are relevant to this finding.",
        "Rotate exposed credentials and review API keys.",
        "A token may be present in the affected service.",
        "password = <value>",
    ],
)
def test_security_terminology_and_placeholders_are_not_blocked(text):
    assert evaluate(text).decision is AIOutputSecurityDecision.PASS


def test_private_key_material_is_denied_without_echoing_content():
    result = evaluate(
        "-----BEGIN RSA PRIVATE KEY-----\nsecret-material\n-----END RSA PRIVATE KEY-----"
    )
    assert result.decision is AIOutputSecurityDecision.DENY
    assert result.reason is AIOutputSecurityReason.PRIVATE_KEY_DETECTED
    assert "secret-material" not in result.reason.value


@pytest.mark.parametrize(
    "text",
    [
        "password = hunter2",
        "passwd: p@ssword-123",
        "secret = s3cr3t-value",
        "api_key = sk-example-value",
        "client_secret: abc-def-123",
        "access_token = bearer-value-123",
    ],
)
def test_concrete_credential_assignments_are_denied(text):
    result = evaluate(text)
    assert result.decision is AIOutputSecurityDecision.DENY
    assert result.reason is AIOutputSecurityReason.CREDENTIAL_ASSIGNMENT_DETECTED


@pytest.mark.parametrize("value", [None, "finding_explanation", object()])
def test_missing_or_invalid_purpose_fails_closed(value):
    with pytest.raises(ValueError):
        FindingExplanationOutputSecurityGuard().evaluate(
            value,
            AIContextClassification.INTERNAL,
            "ordinary explanation",
        )


@pytest.mark.parametrize("value", [None, "internal", object()])
def test_missing_or_invalid_classification_fails_closed(value):
    with pytest.raises(ValueError):
        FindingExplanationOutputSecurityGuard().evaluate(
            AIModelEgressPurpose.FINDING_EXPLANATION,
            value,
            "ordinary explanation",
        )


def test_unsupported_classification_is_denied_without_fallback():
    result = FindingExplanationOutputSecurityGuard().evaluate(
        AIModelEgressPurpose.FINDING_EXPLANATION,
        AIContextClassification.RESTRICTED,
        "ordinary explanation",
    )
    assert result.decision is AIOutputSecurityDecision.DENY
    assert result.reason is AIOutputSecurityReason.UNSUPPORTED_CLASSIFICATION
    assert result.classification is AIContextClassification.RESTRICTED


def test_empty_output_is_not_treated_as_safe():
    result = evaluate("  \n")
    assert result.decision is AIOutputSecurityDecision.DENY
    assert result.reason is AIOutputSecurityReason.EMPTY_OUTPUT


def test_guard_is_deterministic_immutable_and_does_not_upgrade_trust():
    guard = FindingExplanationOutputSecurityGuard()
    first = evaluate("The token terminology is discussed.")
    second = evaluate("The token terminology is discussed.")
    assert first == second
    assert first.purpose is AIModelEgressPurpose.FINDING_EXPLANATION
    assert not hasattr(first, "trust_level")
    with pytest.raises(FrozenInstanceError):
        first.decision = AIOutputSecurityDecision.DENY
