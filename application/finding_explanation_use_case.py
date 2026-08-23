from __future__ import annotations

from collections.abc import Callable

from application.asset_context import (
    AssetContextQueryService,
    classify_observed_asset_identifier,
)
from application.finding_explanation import (
    FindingExplanationInputBuilder,
    FindingExplanationResult,
    FindingExplanationService,
)
from application.finding_model_egress import FINDING_EXPLANATION_EGRESS_POLICY
from application.trusted_ai_retrieval import (
    FINDING_RETRIEVAL_OPERATION,
    FindingResourceReader,
    FindingTrustedRetrievalService,
)
from core.ai_admission import AIContextAdmissionDecision, AIContextAdmissionPolicy
from core.ai_authorization import (
    AIAuthorizationScope,
    AIResourceReference,
    AIResourceType,
)
from core.ai_context import AIContextClassification
from core.ai_authorization import AIAuthorizationDecision, AIResourceScope
from core.ai_egress import AIModelEgressPolicy
from application.findings_query import FindingsQueryService
from application.risk_readiness import (
    RiskAssessmentInput,
    RiskReadinessService,
)


class FindingNotFoundError(LookupError):
    """Raised when the configured source has no matching finding."""


class FindingSelectionError(ValueError):
    """Raised when a finding ID is not unique in the configured source."""


def build_finding_explanation_authorization(
    finding_id: str,
    allowed_finding_ids: frozenset[str],
) -> AIAuthorizationScope | None:
    """Build the explicit, configured MVP scope for one requested Finding."""

    if finding_id not in allowed_finding_ids:
        return None
    resource = AIResourceReference(AIResourceType.FINDING, finding_id)
    return AIAuthorizationScope(
        subject_reference="mvp:configured-finding-explanation",
        operation=FINDING_RETRIEVAL_OPERATION,
        decision=AIAuthorizationDecision.ALLOW,
        authorized_scope=AIResourceScope((resource,)),
        permitted_classifications=frozenset({AIContextClassification.INTERNAL}),
        decision_source_reference="config:mvp-finding-explanation-scope",
    )


class FindingExplanationUseCase:
    """Run the existing explanation capability for one live finding."""

    def __init__(
        self,
        findings: FindingResourceReader,
        asset_contexts: AssetContextQueryService,
        risk_readiness: RiskReadinessService,
        explanations: FindingExplanationService,
        *,
        trusted_retrieval: FindingTrustedRetrievalService | None = None,
        authorization_scope_factory: Callable[
            [str], AIAuthorizationScope | None
        ] | None = None,
        context_admission_policy: object = AIContextAdmissionPolicy,
        egress_policy: AIModelEgressPolicy = FINDING_EXPLANATION_EGRESS_POLICY,
    ) -> None:
        self._trusted_retrieval = trusted_retrieval or FindingTrustedRetrievalService(
            findings
        )
        self._authorization_scope_factory = authorization_scope_factory or (
            lambda _finding_id: None
        )
        self._context_admission_policy = context_admission_policy
        self._asset_contexts = asset_contexts
        self._risk_readiness = risk_readiness
        self._explanations = explanations
        self._egress_policy = egress_policy

    def explain(self, finding_id: str) -> FindingExplanationResult:
        authorization = self._authorization_scope_factory(finding_id)
        requested_resource = AIResourceReference(AIResourceType.FINDING, finding_id)
        retrieved = self._trusted_retrieval.retrieve_finding(
            authorization,
            requested_resource,
        )
        if retrieved is None:
            raise FindingNotFoundError(finding_id)
        if (
            self._context_admission_policy.evaluate(
                retrieved.bound_context.context_item,
                authorization,
                retrieved.bound_context.resource_reference,
            )
            is not AIContextAdmissionDecision.ADMIT
        ):
            raise FindingSelectionError(
                "Finding AI context was not admitted for explanation."
            )
        finding = retrieved.finding
        observed_identifier = classify_observed_asset_identifier(
            finding.asset
        )
        asset_context = (
            self._asset_contexts.resolve(observed_identifier)
            if observed_identifier is not None
            else None
        )
        risk_input = RiskAssessmentInput.from_universal_finding(
            finding
        ).with_asset_context(asset_context)
        risk_result = self._risk_readiness.assess(risk_input)
        explanation_input = FindingExplanationInputBuilder.build(
            finding,
            asset_context,
            risk_input,
            risk_result,
            egress_policy=self._egress_policy,
        )
        return self._explanations.explain(explanation_input)
