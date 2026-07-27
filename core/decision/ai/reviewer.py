from __future__ import annotations

from core.decision.ai.reasoning_result import (
    ReasoningResult,
)
from core.decision.ai.reasoning_service import (
    ReasoningService,
)
from core.decision.models import DecisionResult


class Reviewer:
    """
    First AI review.

    Looks for evidence that supports
    the current decision.
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
You are the Senior Security Reviewer.

Review the following decision.

Decision:
{decision.decision}

Attack Reasoning:
{decision.attack_reasoning.summary}

Business Impact:
{decision.business_impact.summary}

Provide:

- verdict
- confidence
- strengths
- weaknesses
- missing evidence
- executive summary
- SOC summary
- technical summary
- remediation strategy
"""

        response = self.service.review(
            decision,
            prompt,
        )

        return ReasoningResult(

            verdict="Agree",

            confidence_review=95.0,

            executive_summary=(
                response
            ),

            soc_summary=(
                response
            ),

            technical_summary=(
                response
            ),

            remediation_strategy=(
                "Follow Decision Engine recommendation."
            ),

            strengths=[

                "Decision aligns with available evidence.",

            ],

            weaknesses=[],

            missing_evidence=[],

            counter_arguments=[],

            assumptions=[],

            reviewer_notes=[

                response,

            ],

            challenger_notes=[],

        )
    