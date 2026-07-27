from __future__ import annotations

from core.decision.ai.reasoning_result import (
    ReasoningResult,
)
from core.decision.ai.reasoning_service import (
    ReasoningService,
)
from core.decision.models import DecisionResult


class Challenger:
    """
    Independent AI reviewer.

    Attempts to invalidate the current
    decision and identify weaknesses.
    """

    def __init__(
        self,
        service: ReasoningService,
    ) -> None:

        self.service = service

    def review(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        prompt = f"""
You are a Senior Red Team Lead.

Challenge the following decision.

Decision:
{decision.decision}

Attack Reasoning:
{decision.attack_reasoning.summary}

Business Impact:
{decision.business_impact.summary}

Your task is to DISAGREE whenever possible.

Look for:

- missing evidence
- wrong assumptions
- alternative explanations
- weaknesses
- counter arguments

Return a professional security review.
"""

        response = self.service.review(
            decision,
            prompt,
        )

        return ReasoningResult(

            verdict="Challenge",

            confidence_review=92.0,

            executive_summary=response,

            soc_summary=response,

            technical_summary=response,

            remediation_strategy=(
                "Collect additional evidence before execution."
            ),

            strengths=[],

            weaknesses=[
                "Decision may rely on incomplete context.",
            ],

            missing_evidence=[
                "Additional telemetry recommended.",
            ],

            counter_arguments=[
                "Alternative attack path may exist.",
            ],

            assumptions=[
                "Threat intelligence is current.",
            ],

            reviewer_notes=[],

            challenger_notes=[
                response,
            ],
        )
    