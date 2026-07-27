from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BusinessImpact:
    """
    Represents the business impact of a decision.
    """

    summary: str

    business_service: str

    affected_process: str

    financial_impact: str

    operational_impact: str

    reputation_impact: str

    regulatory_impact: str

    estimated_loss: float

    confidence: float
    