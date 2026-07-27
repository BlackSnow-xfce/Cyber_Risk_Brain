from __future__ import annotations

from dataclasses import dataclass, field

from core.decision.confidence_factor import (
    ConfidenceFactor,
)


@dataclass(slots=True)
class ConfidenceResult:
    """
    Result of the Confidence Engine.
    """

    score: float

    factors: list[ConfidenceFactor] = field(
        default_factory=list
    )
    