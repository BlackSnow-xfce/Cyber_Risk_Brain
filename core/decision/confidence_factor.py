from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConfidenceFactor:
    """
    One individual factor influencing
    the confidence of a PredatorAI decision.
    """

    name: str

    description: str

    weight: float

    positive: bool = True
    