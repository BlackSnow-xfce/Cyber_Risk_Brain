from enum import StrEnum

from core.ai_authorization import AIAuthorizationScope, AIResourceReference
from core.ai_context import AIContextItem


AI_CONTEXT_ADMISSION_POLICY_VERSION = "1.0"


class AIContextAdmissionDecision(StrEnum):
    ADMIT = "admit"
    REJECT = "reject"


class AIContextAdmissionPolicy:
    """Pure, fail-closed policy for crossing the AI context boundary."""

    @staticmethod
    def evaluate(
        candidate: AIContextItem | None,
        authorization: AIAuthorizationScope | None,
        resource: AIResourceReference | None,
    ) -> AIContextAdmissionDecision:
        if not isinstance(candidate, AIContextItem):
            return AIContextAdmissionDecision.REJECT
        if not isinstance(authorization, AIAuthorizationScope):
            return AIContextAdmissionDecision.REJECT
        if not isinstance(resource, AIResourceReference):
            return AIContextAdmissionDecision.REJECT
        if not authorization.permits_resource(resource):
            return AIContextAdmissionDecision.REJECT
        if not authorization.permits_classification(candidate.classification):
            return AIContextAdmissionDecision.REJECT
        return AIContextAdmissionDecision.ADMIT
