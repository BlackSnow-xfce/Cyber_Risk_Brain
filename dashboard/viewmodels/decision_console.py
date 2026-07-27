from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DecisionConsoleViewModel:
    """
    ViewModel consumed by the Dashboard.

    It contains only UI-related data and is
    independent from the internal domain model.
    """

    title: str

    decision: str

    priority: str

    risk_score: float

    confidence: float

    confidence_label: str

    ai_verdict: str

    business_impact: str

    estimated_loss: str

    executive_summary: str

    reasons: list[str] = field(
        default_factory=list
    )

    recommendations: list[str] = field(
        default_factory=list
    )

    counter_arguments: list[str] = field(
        default_factory=list
    )
    