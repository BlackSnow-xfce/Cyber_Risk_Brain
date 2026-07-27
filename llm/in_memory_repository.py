from __future__ import annotations

from llm.memory_models import DecisionMemoryEntry
from llm.memory_repository import MemoryRepository


class InMemoryRepository(
    MemoryRepository,
):
    """
    Default in-memory implementation.
    """

    def __init__(self) -> None:

        self._entries: list[
            DecisionMemoryEntry
        ] = []

    def save(
        self,
        entry: DecisionMemoryEntry,
    ) -> None:

        self._entries.append(entry)

    def load(
        self,
    ) -> list[DecisionMemoryEntry]:

        return list(self._entries)

    def clear(
        self,
    ) -> None:

        self._entries.clear()

        