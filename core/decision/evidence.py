from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Evidence:
    """
    One individual piece of evidence that contributed
    to a PredatorAI decision.
    """

    name: str

    source: str

    description: str

    impact: float

    confidence: float
    