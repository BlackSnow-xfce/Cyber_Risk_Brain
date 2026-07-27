from __future__ import annotations

from dataclasses import dataclass, field

from core.decision.evidence import Evidence


@dataclass(slots=True)
class DecisionTrace:
    """
    Canonical output object of PredatorAI.

    Every external component
    (Dashboard, REST API, Reports, Story Engine)
    consumes DecisionTrace.

    Internal models stay inside
    the Decision Engine and AI Layer.
    """

    # Decision

    decision: str

    priority: str

    action: str

    confidence: float

    # Explainability

    evidence: list[Evidence] = field(
        default_factory=list
    )

    threat_intelligence: list[str] = field(
        default_factory=list
    )

    correlations: list[str] = field(
        default_factory=list
    )

    # AI Review

    strengths: list[str] = field(
        default_factory=list
    )

    weaknesses: list[str] = field(
        default_factory=list
    )

    missing_evidence: list[str] = field(
        default_factory=list
    )

    counter_arguments: list[str] = field(
        default_factory=list
    )

    assumptions: list[str] = field(
        default_factory=list
    )

    ai_verdict: str = ""

    ai_confidence: float = 0.0

    # Stories

    executive_summary: str = ""

    soc_summary: str = ""

    technical_summary: str = ""

    remediation: str = ""

    # Future

    attack_path: list[str] = field(
        default_factory=list
    )

    affected_assets: list[str] = field(
        default_factory=list
    )

    recommendations: list[str] = field(
        default_factory=list
    )
    