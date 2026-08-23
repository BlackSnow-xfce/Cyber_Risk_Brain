from dataclasses import dataclass

from core.ai_context import AIContextClassification
from core.ai_egress import AIModelEgressPurpose
from core.ai_disclosure.decision import (
    AIOutputDisclosureDecision,
    AIOutputDisclosureDecisionValue,
    AIOutputDisclosureReason,
)


AI_OUTPUT_DISCLOSURE_POLICY_CONTRACT_VERSION = "1.0"
AI_OUTPUT_DISCLOSURE_POLICY_SOURCE = (
    "policy:ai-output-disclosure:finding-explanation"
)
_INITIAL_ALLOWED_CLASSIFICATIONS = frozenset(
    {AIContextClassification.INTERNAL}
)


@dataclass(frozen=True, slots=True)
class AIOutputDisclosurePolicy:
    """Metadata-only policy; it does not inspect or approve output content."""

    decision_source_reference: str = AI_OUTPUT_DISCLOSURE_POLICY_SOURCE
    contract_version: str = AI_OUTPUT_DISCLOSURE_POLICY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if (
            not isinstance(self.decision_source_reference, str)
            or not self.decision_source_reference.strip()
        ):
            raise ValueError("decision_source_reference must not be empty.")
        if self.contract_version != AI_OUTPUT_DISCLOSURE_POLICY_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be "
                f"{AI_OUTPUT_DISCLOSURE_POLICY_CONTRACT_VERSION}."
            )

    def evaluate(
        self,
        purpose: AIModelEgressPurpose | object,
        classification: AIContextClassification | object,
    ) -> AIOutputDisclosureDecision:
        if not isinstance(purpose, AIModelEgressPurpose):
            raise ValueError("Unsupported or missing output purpose.")
        if not isinstance(classification, AIContextClassification):
            raise ValueError("Missing or invalid output classification.")
        if purpose is not AIModelEgressPurpose.FINDING_EXPLANATION:
            return self._deny(
                purpose,
                classification,
                AIOutputDisclosureReason.UNSUPPORTED_PURPOSE,
            )
        if classification not in _INITIAL_ALLOWED_CLASSIFICATIONS:
            return self._deny(
                purpose,
                classification,
                AIOutputDisclosureReason.CLASSIFICATION_NOT_ALLOWED,
            )
        return AIOutputDisclosureDecision(
            purpose=purpose,
            classification=classification,
            decision=AIOutputDisclosureDecisionValue.ALLOW,
            reason=AIOutputDisclosureReason.CLASSIFICATION_ALLOWED,
            decision_source_reference=self.decision_source_reference,
        )

    def _deny(
        self,
        purpose: AIModelEgressPurpose,
        classification: AIContextClassification,
        reason: AIOutputDisclosureReason,
    ) -> AIOutputDisclosureDecision:
        return AIOutputDisclosureDecision(
            purpose=purpose,
            classification=classification,
            decision=AIOutputDisclosureDecisionValue.DENY,
            reason=reason,
            decision_source_reference=self.decision_source_reference,
        )
