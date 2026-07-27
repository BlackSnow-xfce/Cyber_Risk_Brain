from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Recommendation:
    """
    Represents one remediation recommendation.
    """

    title: str

    description: str

    priority: str

    estimated_risk_reduction: float

    estimated_effort: str

    estimated_cost: str

    confidence: float

    owner: str = ""

    reference: str = ""
    