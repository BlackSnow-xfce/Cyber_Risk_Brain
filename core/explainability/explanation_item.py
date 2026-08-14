from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExplanationCategory(StrEnum):
    DECISION = "decision"
    ATTACK_REASONING = "attack_reasoning"
    BUSINESS_IMPACT = "business_impact"
    CONFIDENCE = "confidence"
    EVIDENCE = "evidence"
    RECOMMENDATION = "recommendation"
    LIMITATION = "limitation"


@dataclass(frozen=True, slots=True)
class ExplanationProvenance:
    source_type: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.source_type.strip():
            raise ValueError("Provenance source type must not be empty.")

        if not self.source_reference.strip():
            raise ValueError("Provenance source reference must not be empty.")

    def to_dict(self) -> dict[str, str]:
        return {
            "sourceType": self.source_type,
            "sourceReference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class ExplanationItem:
    """
    One structured and explainable element of a decision trace.

    ExplanationItem contains presentation-ready reasoning information.
    It must not contain decision logic or calculate risk.
    """

    identifier: str
    category: ExplanationCategory
    title: str
    description: str
    sequence: int

    source: str | None = None
    importance: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: ExplanationProvenance | None = None

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("Explanation item identifier must not be empty.")

        if not self.title.strip():
            raise ValueError("Explanation item title must not be empty.")

        if not self.description.strip():
            raise ValueError("Explanation item description must not be empty.")

        if self.sequence < 1:
            raise ValueError(
                "Explanation item sequence must be greater than 0."
            )

        if self.importance < 0:
            raise ValueError(
                "Explanation item importance must be greater than or equal to 0."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "sequence": self.sequence,
            "source": self.source,
            "importance": self.importance,
            "metadata": dict(self.metadata),
            "provenance": (
                self.provenance.to_dict()
                if self.provenance is not None
                else None
            ),
        }
    
