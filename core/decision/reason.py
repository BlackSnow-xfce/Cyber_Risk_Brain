from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Reason:
    """
    Represents one explainable reason why
    PredatorAI reached a decision.
    """

    title: str

    description: str

    category: str

    source: str

    impact: float

    confidence: float
    