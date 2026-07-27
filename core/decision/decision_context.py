from __future__ import annotations

from dataclasses import dataclass, field

from core.ai.reasoning_result import ReasoningResult
from core.decision.confidence_result import ConfidenceResult
from core.decision.models import DecisionResult


@dataclass(slots=True)
class DecisionContext:
    """
    Central context object shared by all
    Decision Intelligence components.
    """

    # Core

    decision: DecisionResult

    reasoning: ReasoningResult

    # Explainability

    evidence: list = field(default_factory=list)

    recommendations: list = field(default_factory=list)

    business_impact = None

    attack_path: list = field(default_factory=list)

    threat_intelligence: list = field(default_factory=list)

    correlations: list = field(default_factory=list)

    # Confidence

    confidence: ConfidenceResult | None = None

    # Future

    asset_context = None

    findings: list = field(default_factory=list)

    related_assets: list = field(default_factory=list)

    tags: list[str] = field(default_factory=list)
    