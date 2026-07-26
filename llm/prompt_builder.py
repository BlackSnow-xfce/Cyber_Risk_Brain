from __future__ import annotations

from core.decision.models import DecisionResult


class PromptBuilder:
    """
    Builds prompts for LLM reasoning.
    """

    def build(
        self,
        decision: DecisionResult,
    ) -> str:

        return f"""
You are PredatorAI.

Decision:
{decision.decision}

Priority:
{decision.priority.value}

Action:
{decision.action.value}

Attack Summary:
{decision.attack_reasoning.summary}

Business Impact:
{decision.business_impact.summary}

Confidence:
{decision.confidence.score}

Create a professional cybersecurity assessment.
""".strip()
    