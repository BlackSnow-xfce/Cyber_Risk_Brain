from dataclasses import dataclass

from core.ai_authorization.scope import AIResourceReference
from core.ai_context.context import AIContextItem


BOUND_AI_CONTEXT_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class BoundAIContext:
    """Immutable structural binding; it grants no authorization or admission."""

    context_item: AIContextItem
    resource_reference: AIResourceReference
    contract_version: str = BOUND_AI_CONTEXT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.context_item, AIContextItem):
            raise ValueError("context_item must be an AIContextItem.")
        if not isinstance(self.resource_reference, AIResourceReference):
            raise ValueError("resource_reference must be an AIResourceReference.")
        if self.contract_version != BOUND_AI_CONTEXT_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {BOUND_AI_CONTEXT_CONTRACT_VERSION}."
            )
