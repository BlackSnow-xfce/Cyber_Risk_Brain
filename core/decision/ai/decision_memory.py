from __future__ import annotations

from core.decision.ai.reasoning_result import (
    ReasoningResult,
)
from core.decision.models import DecisionResult


class DecisionMemory:
    """
    Stores historical AI reasoning results.
    """

    def __init__(self) -> None:

        self._history: list[
            tuple[
                DecisionResult,
                ReasoningResult,
            ]
        ] = []

    def add(
        self,
        decision: DecisionResult,
        reasoning: ReasoningResult,
    ) -> None:

        self._history.append(
            (
                decision,
                reasoning,
            )
        )

    def all(
        self,
    ):

        return list(
            self._history
        )

    def latest(
        self,
    ):

        if not self._history:

            return None

        return self._history[-1]

    def count(
        self,
    ) -> int:

        return len(
            self._history
        )

    def clear(
        self,
    ) -> None:

        self._history.clear()
        