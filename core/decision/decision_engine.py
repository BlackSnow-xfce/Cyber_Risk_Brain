from __future__ import annotations

from typing import Any

from core.decision.attack_reasoning import AttackReasoningEngine
from core.decision.business_context import BusinessContextEngine
from core.decision.confidence_engine import ConfidenceEngine
from core.decision.evidence_builder import EvidenceBuilder
from core.decision.explainability import ExplainabilityEngine
from core.decision.models import (
    DecisionAction,
    DecisionPriority,
    DecisionResult,
)
from core.decision.recommendation_engine import RecommendationEngine


class DecisionEngine:
    """
    Main orchestration engine for PredatorAI.
    """

    def __init__(self) -> None:

        self.attack_reasoning = AttackReasoningEngine()

        self.business_context = BusinessContextEngine()

        self.confidence = ConfidenceEngine()

        self.recommendations = RecommendationEngine()

        self.explainability = ExplainabilityEngine()

        self.evidence = EvidenceBuilder()

    def analyze(
        self,
        node: dict[str, Any],
    ) -> DecisionResult:

        reasoning = self.attack_reasoning.analyze(node)

        business = self.business_context.analyze(node)

        confidence = self.confidence.analyze(node)

        recommendations = self.recommendations.analyze(node)

        evidence = self.evidence.build(node)

        explanation = self.explainability.analyze(
            reasoning,
            business,
            confidence,
        )

        risk_score = self._calculate_risk_score(node)

        priority = self._determine_priority(risk_score)

        action = self._determine_action(priority)

        decision = (
            f"PredatorAI recommends "
            f"{action.value} "
            f"with priority "
            f"{priority.value}."
        )

        return DecisionResult(
            finding_id=str(node.get("name", "unknown")),
            priority=priority,
            action=action,
            decision=decision,
            attack_reasoning=reasoning,
            business_impact=business,
            confidence=confidence,
            recommendations=recommendations,
            evidence=evidence,
            explanation=explanation,
            metadata={
                "risk_score": risk_score,
            },
        )

    @staticmethod
    def _calculate_risk_score(
        node: dict[str, Any],
    ) -> int:

        score = 0

        criticality = str(
            node.get("criticality", "LOW")
        ).upper()

        if criticality == "CRITICAL":
            score += 40

        elif criticality == "HIGH":
            score += 30

        elif criticality == "MEDIUM":
            score += 20

        else:
            score += 10

        if node.get("exposed", False):
            score += 20

        if not node.get("detection", True):
            score += 15

        if node.get("threat_intel", False):
            score += 15

        if node.get("mitre"):
            score += 10

        return min(score, 100)

    @staticmethod
    def _determine_priority(
        risk_score: int,
    ) -> DecisionPriority:

        if risk_score >= 90:
            return DecisionPriority.CRITICAL

        if risk_score >= 75:
            return DecisionPriority.HIGH

        if risk_score >= 50:
            return DecisionPriority.MEDIUM

        if risk_score >= 25:
            return DecisionPriority.LOW

        return DecisionPriority.INFORMATIONAL

    @staticmethod
    def _determine_action(
        priority: DecisionPriority,
    ) -> DecisionAction:

        mapping = {
            DecisionPriority.CRITICAL:
                DecisionAction.REMEDIATE_NOW,

            DecisionPriority.HIGH:
                DecisionAction.REMEDIATE_PLANNED,

            DecisionPriority.MEDIUM:
                DecisionAction.MITIGATE,

            DecisionPriority.LOW:
                DecisionAction.MONITOR,

            DecisionPriority.INFORMATIONAL:
                DecisionAction.ACCEPT,
        }

        return mapping[priority]