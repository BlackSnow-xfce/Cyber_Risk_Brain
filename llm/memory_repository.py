from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from llm.memory_models import DecisionMemoryEntry


class MemoryRepository(ABC):
    """
    Abstract persistence interface for Decision Memory.
    """

    @abstractmethod
    def save(
        self,
        entry: DecisionMemoryEntry,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(
        self,
    ) -> list[DecisionMemoryEntry]:
        raise NotImplementedError

    @abstractmethod
    def clear(
        self,
    ) -> None:
        raise NotImplementedError

    