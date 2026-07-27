from __future__ import annotations

from dataclasses import dataclass, field

from core.decision.business_impact import BusinessImpact
from core.decision.confidence_result import ConfidenceResult
from core.decision.evidence import Evidence
from core.decision.recommendation import Recommendation


@dataclass(slots=True)
class DecisionTrace:
    """
    Canonical output object of PredatorAI.
    """

    decision: str

    priority: str

    action: str

    confidence: float

    confidence_details: ConfidenceResult | None = None

    evidence: list[Evidence] = field(default_factory=list)

    threat_intelligence: list[str] = field(default_factory=list)

    correlations: list[str] = field(default_factory=list)

    strengths: list[str] = field(default_factory=list)

    weaknesses: list[str] = field(default_factory=list)

    missing_evidence: list[str] = field(default_factory=list)

    counter_arguments: list[str] = field(default_factory=list)

    assumptions: list[str] = field(default_factory=list)

    ai_verdict: str = ""

    ai_confidence: float = 0.0

    executive_summary: str = ""

    soc_summary: str = ""

    technical_summary: str = ""

    remediation: str = ""

    attack_path: list = field(default_factory=list)

    affected_assets: list[str] = field(default_factory=list)

    recommendations: list[Recommendation] = field(default_factory=list)

    business_impact: BusinessImpact | None = None
    