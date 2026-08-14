from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.explainability.explanation_item import ExplanationProvenance


class CompletenessStatus(StrEnum):
    AVAILABLE = "available"
    NO_DATA = "no_data"
    SOURCE_UNAVAILABLE = "source_unavailable"
    NOT_PART_OF_EXECUTION = "not_part_of_execution"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExplanationCompleteness:
    status: CompletenessStatus
    provenance: ExplanationProvenance
