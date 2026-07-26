from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReasoningResult:
    """
    Result returned by an LLM after enhancing a decision.
    """

    summary: str

    technical_analysis: str

    executive_summary: str

    remediation_strategy: str

    confidence: float
    