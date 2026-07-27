from __future__ import annotations

from datetime import datetime

from core.decision.models import DecisionResult

from llm.in_memory_repository import InMemoryRepository
from llm.memory_models import DecisionMemoryEntry
from llm.memory_repository import MemoryRepository
from llm.reasoning_result import ReasoningResult


class DecisionMemory:
    """
    Stores historical PredatorAI decisions.
    """

    def __init__(
        self,
        repository: MemoryRepository | None = None,
    ) -> None:

        self.repository = (
            repository
            if repository is not None
            else InMemoryRepository()
        )

    def add(
        self,
        decision: DecisionResult,
        reasoning: ReasoningResult,
    ) -> None:

        entry = DecisionMemoryEntry(
            timestamp=datetime.utcnow(),
            decision=decision,
            reasoning=reasoning,
        )

        self.repository.save(entry)

    def all(
        self,
    ) -> list[DecisionMemoryEntry]:

        return self.repository.load()

    def count(
        self,
    ) -> int:

        return len(self.repository.load())

    def clear(
        self,
    ) -> None:

        self.repository.clear()

        