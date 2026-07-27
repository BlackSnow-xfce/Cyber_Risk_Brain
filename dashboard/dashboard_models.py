from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DashboardSummary:

    total_findings: int

    critical: int

    high: int

    medium: int

    low: int


@dataclass(slots=True)
class DashboardDecision:

    title: str

    description: str

    risk_score: float

    confidence: float

    priority: str

    verdict: str

    recommended_action: str

    business_impact: str


@dataclass(slots=True)
class DashboardFeedItem:

    title: str

    risk_score: float

    priority: str


@dataclass(slots=True)
class DashboardData:

    summary: DashboardSummary

    decision: DashboardDecision

    feed: list[DashboardFeedItem] = field(
        default_factory=list
    )

    reports: list = field(
        default_factory=list
    )

    stories: list = field(
        default_factory=list
    )
    