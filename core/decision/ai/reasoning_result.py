from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReasoningResult:
    """
    Final AI reasoning result produced by
    the Reviewer/Challenger/Judge pipeline.
    """

    verdict: str

    confidence_review: float

    executive_summary: str

    soc_summary: str

    technical_summary: str

    remediation_strategy: str

    strengths: list[str] = field(
        default_factory=list
    )

    weaknesses: list[str] = field(
        default_factory=list
    )

    missing_evidence: list[str] = field(
        default_factory=list
    )

    counter_arguments: list[str] = field(
        default_factory=list
    )

    assumptions: list[str] = field(
        default_factory=list
    )

    reviewer_notes: list[str] = field(
        default_factory=list
    )

    challenger_notes: list[str] = field(
        default_factory=list
    )
    