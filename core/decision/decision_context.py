from __future__ import annotations

from dataclasses import dataclass, field

from core.ai.reasoning_result import ReasoningResult
from core.decision.business_impact import BusinessImpact
from core.decision.confidence_result import ConfidenceResult
from core.decision.models import DecisionResult


@dataclass(slots=True)
class DecisionContext:
    """
    Shared context passed through the
    complete Decision Intelligence pipeline.
    """

    # -------------------------------------------------
    # Core
    # -------------------------------------------------

    decision: DecisionResult

    reasoning: ReasoningResult

    # -------------------------------------------------
    # Explainability
    # -------------------------------------------------

    reasons: list = field(
        default_factory=list
    )

    evidence: list = field(
        default_factory=list
    )

    recommendations: list = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Attack Intelligence
    # -------------------------------------------------

    attack_path: list[str] = field(
        default_factory=list
    )

    threat_intelligence: list[str] = field(
        default_factory=list
    )

    correlations: list[str] = field(
        default_factory=list
    )

    mitre_techniques: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Business
    # -------------------------------------------------

    confidence: ConfidenceResult | None = None

    business_impact: BusinessImpact | None = None

    asset_context: dict | None = None

    findings: list = field(
        default_factory=list
    )

    related_assets: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Timeline
    # -------------------------------------------------

    timeline: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Metadata
    # -------------------------------------------------

    tags: list[str] = field(
        default_factory=list
    )

    source: str = "PredatorAI"

    version: str = "3.0"
    