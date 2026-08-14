from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from core.decision.models import (
    ConfidenceLevel,
    DecisionAction,
    DecisionPriority,
)
from core.explainability.explanation_item import ExplanationItem


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """
    Structured explainability representation of a DecisionResult.

    DecisionTrace is derived from the canonical decision domain model.
    It contains no decision-making or risk-calculation logic.

    Consumers include:

    - REST API
    - Dashboard
    - PDF output
    - Story engine
    - AI explanation layer
    """

    finding_id: str
    decision: str
    priority: DecisionPriority
    action: DecisionAction

    confidence_score: float
    confidence_level: ConfidenceLevel

    items: tuple[ExplanationItem, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    projection_version: str = "1.0"
    source_version: str = "1.0"
    generated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Decision trace finding ID must not be empty.")

        if not self.decision.strip():
            raise ValueError("Decision trace decision must not be empty.")

        if not 0 <= self.confidence_score <= 100:
            raise ValueError(
                "Decision trace confidence score must be between 0 and 100."
            )

        if not self.projection_version.strip():
            raise ValueError("Projection version must not be empty.")

        if not self.source_version.strip():
            raise ValueError("Source version must not be empty.")

        if (
            self.generated_at.tzinfo is None
            or self.generated_at.utcoffset() != timedelta(0)
        ):
            raise ValueError("Generated at must be a timezone-aware UTC value.")

        sequences = [item.sequence for item in self.items]

        if len(sequences) != len(set(sequences)):
            raise ValueError(
                "Decision trace explanation item sequences must be unique."
            )

        sorted_items = tuple(
            sorted(
                self.items,
                key=lambda item: item.sequence,
            )
        )

        object.__setattr__(self, "items", sorted_items)

    def items_by_category(
        self,
        category: str,
    ) -> tuple[ExplanationItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.category.value == category
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "projectionVersion": self.projection_version,
            "sourceVersion": self.source_version,
            "generatedAt": self.generated_at.isoformat(),
            "finding_id": self.finding_id,
            "decision": self.decision,
            "priority": self.priority.value,
            "action": self.action.value,
            "confidence": {
                "score": self.confidence_score,
                "level": self.confidence_level.value,
            },
            "items": [
                item.to_dict()
                for item in self.items
            ],
            "metadata": dict(self.metadata),
        }
