from __future__ import annotations

from typing import Any

from core.decision.action_engine import ActionEngine
from core.decision.attack_reasoning import AttackReasoningEngine
from core.decision.business_context import BusinessContextEngine
from core.decision.confidence_engine import ConfidenceEngine
from core.decision.evidence_builder import EvidenceBuilder
from core.decision.models import (
    DecisionResult,
)
from core.decision.priority_engine import PriorityEngine
from core.decision.recommendation_engine import RecommendationEngine
from core.decision.risk_engine import RiskEngine


class DecisionEngine:
    """
    Main orchestration engine for PredatorAI.
    """

    def __init__(self) -> None:

        self.attack_reasoning = AttackReasoningEngine()

        self.business_context = BusinessContextEngine()

        self.risk = RiskEngine()

        self.priority = PriorityEngine()

        self.action = ActionEngine()

        self.confidence = ConfidenceEngine()

        self.recommendations = RecommendationEngine()

        self.evidence = EvidenceBuilder()

    def analyze(
        self,
        node: dict[str, Any],
    ) -> DecisionResult:

        reasoning = self.attack_reasoning.analyze(
            node
        )

        business = self.business_context.analyze(
            node
        )

        risk_score = self.risk.calculate(
            node
        )

        priority = self.priority.calculate(
            risk_score
        )

        action = self.action.calculate(
            priority
        )

        confidence = self.confidence.calculate(
            reasoning
        )

        recommendations = self.recommendations.analyze(
            node
        )

        evidence = self.evidence.build(
            reasoning
        )

        decision = (
            f"PredatorAI recommends "
            f"{action.value} "
            f"with priority "
            f"{priority.value}."
        )

        return DecisionResult(
            finding_id=str(
                node.get(
                    "name",
                    "unknown",
                )
            ),
            priority=priority,
            action=action,
            decision=decision,
            attack_reasoning=reasoning,
            business_impact=business,
            confidence=confidence,
            recommendations=recommendations,
            evidence=evidence,
            metadata={
                "risk_score": risk_score,
            },
        )
    