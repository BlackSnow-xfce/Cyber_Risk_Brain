from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.decision.models import DecisionResult
from llm.reasoning_result import ReasoningResult


@dataclass(slots=True)
class DecisionMemoryEntry:
    """
    Represents one historical PredatorAI decision.
    """

    timestamp: datetime

    decision: DecisionResult

    reasoning: ReasoningResult

    human_verdict: str = ""

    incident_occurred: bool = False

    feedback: str = ""
    