from __future__ import annotations

from core.ai.reasoning_result import ReasoningResult

from core.decision.decision_trace import DecisionTrace
from core.decision.evidence_builder import EvidenceBuilder
from core.decision.models import DecisionResult


class DecisionTraceBuilder:
    """
    Builds the canonical DecisionTrace object.

    This object is consumed by every external
    component of PredatorAI.
    """

    def __init__(self) -> None:

        self.evidence_builder = EvidenceBuilder()

    def build(
        self,
        decision: DecisionResult,
        reasoning: ReasoningResult,
    ) -> DecisionTrace:

        evidence = self.evidence_builder.build(
            decision
        )

        return DecisionTrace(

            decision=decision.decision,

            priority=decision.priority.value,

            action=decision.action.value,

            confidence=decision.confidence.score,

            evidence=evidence,

            threat_intelligence=[],

            correlations=[],

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

            attack_path=[],

            affected_assets=[],

            recommendations=[],

        )
    