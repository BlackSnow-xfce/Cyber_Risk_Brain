from __future__ import annotations

from core.decision.models import DecisionResult

from llm.json_reasoning_parser import JsonReasoningParser
from llm.prompt_builder import PromptBuilder
from llm.reasoning_result import ReasoningResult
from llm.reasoning_service import ReasoningService


class Reviewer:
    """
    Reviews an existing PredatorAI decision.

    The reviewer NEVER creates a new decision.

    It validates, explains and challenges the
    existing decision.
    """

    def __init__(
        self,
        service: ReasoningService,
    ) -> None:

        self.service = service

        self.prompt_builder = PromptBuilder()

        self.parser = JsonReasoningParser()

    def review(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        prompt = self.prompt_builder.build(
            decision
        )

        response = self.service.generate_prompt(
            prompt
        )

        return self.parser.parse(
            response
        )
    