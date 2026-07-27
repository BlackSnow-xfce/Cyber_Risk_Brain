from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReasoningResult:
    """
    LLM review of a PredatorAI decision.

    The LLM does NOT make the decision.

    It validates, explains and challenges it.
    """

    # Overall explanation

    explanation: str

    # Different audiences

    executive_summary: str

    soc_summary: str

    technical_summary: str

    # Decision review

    verdict: str

    confidence_review: float

    # Analysis

    strengths: list[str] = field(default_factory=list)

    weaknesses: list[str] = field(default_factory=list)

    missing_evidence: list[str] = field(default_factory=list)

    counter_arguments: list[str] = field(default_factory=list)

    assumptions: list[str] = field(default_factory=list)

    # Existing output

    remediation_strategy: str = ""

    # Raw LLM answer

    raw_response: str = ""
    