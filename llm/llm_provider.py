from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract base class for all PredatorAI LLM providers.

    Every provider (Local, OpenAI, Ollama, etc.) must implement
    the generate() interface.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a text completion for the supplied prompt.
        """
        raise NotImplementedError
    