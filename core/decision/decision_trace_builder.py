from __future__ import annotations

from core.decision.ai.reasoning_result import ReasoningResult

from core.decision.business_impact_builder import (
    BusinessImpactBuilder,
)
from core.decision.decision_context import DecisionContext
from core.decision.decision_trace import DecisionTrace
from core.decision.evidence_builder import EvidenceBuilder
from core.decision.reason_builder import ReasonBuilder
from core.decision.recommendation_builder import (
    RecommendationBuilder,
)


class DecisionTraceBuilder:
    """
    Builds the canonical DecisionTrace.
    """

    def __init__(self) -> None:

        self.evidence_builder = EvidenceBuilder()

        self.reason_builder = ReasonBuilder()

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

        reasons = self.reason_builder.build(
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

            risk_score=decision.metadata.get(
                "risk_score",
                0,
            ),

            confidence=decision.confidence,

            ai_verdict=reasoning.verdict,

            ai_confidence=reasoning.confidence_review,

            reasons=reasons,

            evidence=evidence,

            threat_intelligence=list(
                context.threat_intelligence
            ),

            correlations=list(
                context.correlations
            ),

            strengths=list(
                reasoning.strengths
            ),

            weaknesses=list(
                reasoning.weaknesses
            ),

            missing_evidence=list(
                reasoning.missing_evidence
            ),

            counter_arguments=list(
                reasoning.counter_arguments
            ),

            assumptions=list(
                reasoning.assumptions
            ),

            business_impact=business_impact,

            recommendations=recommendations,

            attack_path=list(
                context.attack_path
            ),

            affected_assets=list(
                context.related_assets
            ),

            mitre_techniques=list(
                context.mitre_techniques
            ),

            timeline=list(
                context.timeline
            ),

            executive_summary=(
                reasoning.executive_summary
            ),

            soc_summary=(
                reasoning.soc_summary
            ),

            technical_summary=(
                reasoning.technical_summary
            ),

            remediation=(
                reasoning.remediation_strategy
            ),

            tags=list(
                context.tags
            ),

            source=context.source,
        )
    