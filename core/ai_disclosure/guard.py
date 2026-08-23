import re
from dataclasses import dataclass
from enum import StrEnum

from core.ai_context import AIContextClassification
from core.ai_egress import AIModelEgressPurpose


AI_OUTPUT_SECURITY_GUARD_CONTRACT_VERSION = "1.0"


class AIOutputSecurityDecision(StrEnum):
    PASS = "pass"
    DENY = "deny"


class AIOutputSecurityReason(StrEnum):
    OUTPUT_CLEAR = "output_clear"
    EMPTY_OUTPUT = "empty_output"
    PRIVATE_KEY_DETECTED = "private_key_detected"
    CREDENTIAL_ASSIGNMENT_DETECTED = "credential_assignment_detected"
    UNSUPPORTED_PURPOSE = "unsupported_purpose"
    UNSUPPORTED_CLASSIFICATION = "unsupported_classification"


@dataclass(frozen=True, slots=True)
class AIOutputSecurityResult:
    purpose: AIModelEgressPurpose
    classification: AIContextClassification
    decision: AIOutputSecurityDecision
    reason: AIOutputSecurityReason
    contract_version: str = AI_OUTPUT_SECURITY_GUARD_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, AIModelEgressPurpose):
            raise ValueError("purpose must be an AIModelEgressPurpose.")
        if not isinstance(self.classification, AIContextClassification):
            raise ValueError("classification must be an AIContextClassification.")
        if not isinstance(self.decision, AIOutputSecurityDecision):
            raise ValueError("decision must be an AIOutputSecurityDecision.")
        if not isinstance(self.reason, AIOutputSecurityReason):
            raise ValueError("reason must be an AIOutputSecurityReason.")
        if self.contract_version != AI_OUTPUT_SECURITY_GUARD_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be "
                f"{AI_OUTPUT_SECURITY_GUARD_CONTRACT_VERSION}."
            )


_PRIVATE_KEY_MARKER = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----",
    re.IGNORECASE,
)
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"\b(?:password|passwd|secret|api[ _-]?key|access[ _-]?token|client[ _-]?secret)"
    r"\b\s*(?:=|:)\s*(?P<value>[^\s,;]+)",
    re.IGNORECASE,
)
_PLACEHOLDER_VALUES = frozenset(
    {"...", "<value>", "<secret>", "<redacted>", "value", "example"}
)


class FindingExplanationOutputSecurityGuard:
    """Small high-confidence leakage guard; never redacts or calls a provider."""

    def evaluate(
        self,
        purpose: AIModelEgressPurpose | object,
        classification: AIContextClassification | object,
        output_text: str | object,
    ) -> AIOutputSecurityResult:
        if not isinstance(purpose, AIModelEgressPurpose):
            raise ValueError("Unsupported or missing output purpose.")
        if not isinstance(classification, AIContextClassification):
            raise ValueError("Missing or invalid output classification.")
        if purpose is not AIModelEgressPurpose.FINDING_EXPLANATION:
            return self._result(
                purpose,
                classification,
                AIOutputSecurityDecision.DENY,
                AIOutputSecurityReason.UNSUPPORTED_PURPOSE,
            )
        if classification is not AIContextClassification.INTERNAL:
            return self._result(
                purpose,
                classification,
                AIOutputSecurityDecision.DENY,
                AIOutputSecurityReason.UNSUPPORTED_CLASSIFICATION,
            )
        if not isinstance(output_text, str):
            raise ValueError("output_text must be a string.")
        if not output_text.strip():
            return self._result(
                purpose,
                classification,
                AIOutputSecurityDecision.DENY,
                AIOutputSecurityReason.EMPTY_OUTPUT,
            )
        if _PRIVATE_KEY_MARKER.search(output_text):
            return self._result(
                purpose,
                classification,
                AIOutputSecurityDecision.DENY,
                AIOutputSecurityReason.PRIVATE_KEY_DETECTED,
            )
        assignment = _CREDENTIAL_ASSIGNMENT.search(output_text)
        if assignment is not None:
            value = assignment.group("value").strip().lower()
            if value not in _PLACEHOLDER_VALUES and not (
                value.startswith("<") and value.endswith(">")
            ):
                return self._result(
                    purpose,
                    classification,
                    AIOutputSecurityDecision.DENY,
                    AIOutputSecurityReason.CREDENTIAL_ASSIGNMENT_DETECTED,
                )
        return self._result(
            purpose,
            classification,
            AIOutputSecurityDecision.PASS,
            AIOutputSecurityReason.OUTPUT_CLEAR,
        )

    @staticmethod
    def _result(
        purpose: AIModelEgressPurpose,
        classification: AIContextClassification,
        decision: AIOutputSecurityDecision,
        reason: AIOutputSecurityReason,
    ) -> AIOutputSecurityResult:
        return AIOutputSecurityResult(purpose, classification, decision, reason)
