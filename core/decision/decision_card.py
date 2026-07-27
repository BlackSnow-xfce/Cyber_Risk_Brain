from __future__ import annotations

from dataclasses import dataclass, field

from core.decision.business_impact import BusinessImpact
from core.decision.confidence_result import ConfidenceResult
from core.decision.reason import Reason
from core.decision.recommendation import Recommendation


@dataclass(slots=True)
class DecisionCard:
    """
    UI representation of a DecisionTrace.

    Used by Dashboard, REST API, PDF and
    Story Engine.
    """

    # -------------------------------------------------
    # Header
    # -------------------------------------------------

    title: str

    decision: str

    priority: str

    risk_score: float

    # -------------------------------------------------
    # Confidence
    # -------------------------------------------------

    confidence: ConfidenceResult

    ai_verdict: str

    # -------------------------------------------------
    # Business
    # -------------------------------------------------

    business_impact: BusinessImpact | None = None

    # -------------------------------------------------
    # Explainability
    # -------------------------------------------------

    reasons: list[Reason] = field(
        default_factory=list
    )

    recommendations: list[
        Recommendation
    ] = field(
        default_factory=list
    )

    counter_arguments: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Attack Path
    # -------------------------------------------------

    affected_assets: list[str] = field(
        default_factory=list
    )

    attack_path: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # AI Review
    # -------------------------------------------------

    strengths: list[str] = field(
        default_factory=list
    )

    weaknesses: list[str] = field(
        default_factory=list
    )

    missing_evidence: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Threat Intelligence
    # -------------------------------------------------

    threat_intelligence: list[str] = field(
        default_factory=list
    )

    correlations: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Timeline
    # -------------------------------------------------

    timeline: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # Story
    # -------------------------------------------------

    executive_summary: str = ""

    technical_summary: str = ""

    remediation_summary: str = ""

    # -------------------------------------------------
    # Dashboard
    # -------------------------------------------------

    color: str = "critical"

    icon: str = "shield"

    expanded: bool = False

    