from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.decision.models import (
    ConfidenceLevel,
    DecisionAction,
    DecisionPriority,
)
from core.explainability.explanation_item import ExplanationItem


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

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Decision trace finding ID must not be empty.")

        if not self.decision.strip():
            raise ValueError("Decision trace decision must not be empty.")

        if not 0 <= self.confidence_score <= 100:
            raise ValueError(
                "Decision trace confidence score must be between 0 and 100."
            )

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