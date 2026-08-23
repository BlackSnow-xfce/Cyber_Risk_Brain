from dataclasses import dataclass
from enum import StrEnum

from core.ai_context import AIContextClassification
from core.ai_egress import AIModelEgressPurpose


AI_OUTPUT_DISCLOSURE_DECISION_CONTRACT_VERSION = "1.0"


class AIOutputDisclosureDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class AIOutputDisclosureReason(StrEnum):
    PURPOSE_ALLOWED = "purpose_allowed"
    PURPOSE_NOT_ALLOWED = "purpose_not_allowed"
    CLASSIFICATION_ALLOWED = "classification_allowed"
    CLASSIFICATION_NOT_ALLOWED = "classification_not_allowed"
    OUTPUT_SECURITY_CHECK_REQUIRED = "output_security_check_required"
    UNSUPPORTED_PURPOSE = "unsupported_purpose"


_ALLOW_REASONS = frozenset(
    {
        AIOutputDisclosureReason.PURPOSE_ALLOWED,
        AIOutputDisclosureReason.CLASSIFICATION_ALLOWED,
    }
)
_DENY_REASONS = frozenset(
    {
        AIOutputDisclosureReason.PURPOSE_NOT_ALLOWED,
        AIOutputDisclosureReason.CLASSIFICATION_NOT_ALLOWED,
        AIOutputDisclosureReason.OUTPUT_SECURITY_CHECK_REQUIRED,
        AIOutputDisclosureReason.UNSUPPORTED_PURPOSE,
    }
)


@dataclass(frozen=True, slots=True)
class AIOutputDisclosureDecision:
    purpose: AIModelEgressPurpose
    classification: AIContextClassification
    decision: AIOutputDisclosureDecisionValue
    reason: AIOutputDisclosureReason
    decision_source_reference: str
    contract_version: str = AI_OUTPUT_DISCLOSURE_DECISION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, AIModelEgressPurpose):
            raise ValueError("purpose must be an AIModelEgressPurpose.")
        if not isinstance(self.classification, AIContextClassification):
            raise ValueError("classification must be an AIContextClassification.")
        if not isinstance(self.decision, AIOutputDisclosureDecisionValue):
            raise ValueError(
                "decision must be an AIOutputDisclosureDecisionValue."
            )
        if not isinstance(self.reason, AIOutputDisclosureReason):
            raise ValueError("reason must be an AIOutputDisclosureReason.")
        if (
            not isinstance(self.decision_source_reference, str)
            or not self.decision_source_reference.strip()
        ):
            raise ValueError("decision_source_reference must not be empty.")
        if self.contract_version != AI_OUTPUT_DISCLOSURE_DECISION_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be "
                f"{AI_OUTPUT_DISCLOSURE_DECISION_CONTRACT_VERSION}."
            )
        valid_reasons = (
            _ALLOW_REASONS
            if self.decision is AIOutputDisclosureDecisionValue.ALLOW
            else _DENY_REASONS
        )
        if self.reason not in valid_reasons:
            raise ValueError("reason is inconsistent with the disclosure decision.")
