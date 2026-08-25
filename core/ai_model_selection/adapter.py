from typing import Protocol, TypeVar, runtime_checkable

from core.ai_model_selection.policy import AIModelSelectionDecision


RequestT = TypeVar("RequestT", contravariant=True)
ResponseT = TypeVar("ResponseT", covariant=True)


@runtime_checkable
class GovernedAIProviderAdapter(Protocol[RequestT, ResponseT]):
    """Provider-neutral execution boundary for capability-specific adapters."""

    provider_id: str
    model_id: str

    def execute(
        self, request: RequestT, selection: AIModelSelectionDecision
    ) -> ResponseT: ...
