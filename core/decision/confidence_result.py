from __future__ import annotations

from dataclasses import dataclass, field

from core.decision.confidence_factor import (
    ConfidenceFactor,
)
from core.decision.models import (
    ConfidenceLevel,
)


@dataclass(slots=True)
class ConfidenceResult:
    """
    Result of the Confidence Engine.
    """

    score: float

    level: ConfidenceLevel = ConfidenceLevel.MEDIUM

    reasons: list[str] = field(
        default_factory=list
    )

    missing_information: list[str] = field(
        default_factory=list
    )

    factors: list[ConfidenceFactor] = field(
        default_factory=list
    )
    