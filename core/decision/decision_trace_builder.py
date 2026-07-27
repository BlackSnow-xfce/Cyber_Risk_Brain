from __future__ import annotations

from core.ai.reasoning_result import ReasoningResult

from core.decision.decision_context import DecisionContext
from core.decision.decision_trace import DecisionTrace
from core.decision.evidence_builder import EvidenceBuilder
from core.decision.recommendation_builder import RecommendationBuilder
from core.decision.business_impact_builder import (
    BusinessImpactBuilder,
)


class DecisionTraceBuilder:
    """
    Builds the canonical DecisionTrace object
    from a DecisionContext.

    Every external component of PredatorAI
    consumes DecisionTrace.
    """

    def __init__(self) -> None:

        self.evidence_builder = EvidenceBuilder()

        self.recommendation_builder = (
            RecommendationBuilder()
        )

        self.business_impact_builder = (
            BusinessImpactBuilder()
        )

    def build(
        self,
        context: DecisionContext,
    ) -> DecisionTrace:

        decision = context.decision

        reasoning: ReasoningResult = (
            context.reasoning
        )

        evidence = self.evidence_builder.build(
            decision
        )

        recommendations = (
            self.recommendation_builder.build(
                decision
            )
        )

        business_impact = (
            self.business_impact_builder.build(
                decision
            )
        )

        context.evidence = evidence

        context.recommendations = (
            recommendations
        )

        context.business_impact = (
            business_impact
        )

        return DecisionTrace(

            decision=decision.decision,

            priority=decision.priority.value,

            action=decision.action.value,

            confidence=decision.confidence.score,

            evidence=context.evidence,

            threat_intelligence=context.threat_intelligence,

            correlations=context.correlations,

            strengths=reasoning.strengths,

            weaknesses=reasoning.weaknesses,

            missing_evidence=reasoning.missing_evidence,

            counter_arguments=reasoning.counter_arguments,

            assumptions=reasoning.assumptions,

            ai_verdict=reasoning.verdict,

            ai_confidence=reasoning.confidence_review,

            executive_summary=reasoning.executive_summary,

            soc_summary=reasoning.soc_summary,

            technical_summary=reasoning.technical_summary,

            remediation=reasoning.remediation_strategy,

            attack_path=context.attack_path,

            affected_assets=context.related_assets,

            recommendations=context.recommendations,

            business_impact=context.business_impact,

        )
    