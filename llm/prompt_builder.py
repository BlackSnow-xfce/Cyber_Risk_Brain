from __future__ import annotations

from core.decision.models import DecisionResult


class PromptBuilder:
    """
    Builds review prompts for PredatorAI.

    The LLM validates and explains an existing decision.
    """

    def build(
        self,
        decision: DecisionResult,
    ) -> str:

        return f"""
You are a Principal Incident Responder,
Senior Detection Engineer,
Enterprise Security Architect
and CISO.

PredatorAI has already completed the risk analysis.

DO NOT create another decision.

Your job is to review the decision.

Return VALID JSON ONLY.

Do NOT use markdown.

Do NOT use code blocks.

Use exactly this schema:

{{
    "verdict": "",
    "confidence_review": 0,
    "explanation": "",
    "executive_summary": "",
    "soc_summary": "",
    "technical_summary": "",
    "remediation_strategy": "",
    "strengths": [],
    "weaknesses": [],
    "missing_evidence": [],
    "counter_arguments": [],
    "assumptions": []
}}

------------------------------------------------

Decision

{decision.decision}

Priority

{decision.priority.value}

Action

{decision.action.value}

Confidence

{decision.confidence.score:.2f}

------------------------------------------------

Attack Summary

{decision.attack_reasoning.summary}

------------------------------------------------

Business Impact

{decision.business_impact.summary}

------------------------------------------------

Tasks

Explain why PredatorAI reached this decision.

List all supporting evidence.

List weaknesses.

List missing evidence.

Challenge the decision.

Describe situations where the decision changes.

Produce Executive Summary.

Produce SOC Summary.

Produce Technical Summary.

Recommend remediation.

Return JSON only.
""".strip()
    