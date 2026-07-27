from __future__ import annotations

from core.decision.models import DecisionResult

from llm.json_reasoning_parser import JsonReasoningParser
from llm.reasoning_result import ReasoningResult
from llm.reasoning_service import ReasoningService


class Challenger:
    """
    Attempts to disprove a PredatorAI decision.

    The challenger deliberately searches for
    alternative interpretations, missing evidence
    and situations where the decision may be wrong.
    """

    def __init__(
        self,
        service: ReasoningService,
    ) -> None:

        self.service = service

        self.parser = JsonReasoningParser()

    def review(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        prompt = f"""
You are an independent security reviewer.

PredatorAI has already made a decision.

Your ONLY task is to prove PredatorAI wrong.

Do NOT support the decision.

Search for:

- missing evidence
- assumptions
- false correlations
- possible false positives
- compensating controls
- situations where risk decreases

Return VALID JSON ONLY.

Decision

{decision.decision}

Priority

{decision.priority.value}

Action

{decision.action.value}

Attack Summary

{decision.attack_reasoning.summary}

Business Impact

{decision.business_impact.summary}
"""

        response = self.service.generate_prompt(
            prompt
        )

        return self.parser.parse(
            response
        )
    