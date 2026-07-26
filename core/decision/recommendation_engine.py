from __future__ import annotations

from core.decision.models import (
    DecisionAction,
    DecisionPriority,
    Recommendation,
)


class RecommendationEngine:
    """
    Generates prioritized remediation recommendations.
    """

    def analyze(self, finding) -> list[Recommendation]:
        recommendations: list[Recommendation] = []

        internet_facing = getattr(finding.asset, "internet_facing", False)
        kev = getattr(finding, "kev", False)
        exploit = getattr(finding, "public_exploit", False)

        order = 1

        if internet_facing:
            recommendations.append(
                Recommendation(
                    title="Restrict Internet Exposure",
                    description="Limit or remove external access until remediation is complete.",
                    action=DecisionAction.MITIGATE,
                    priority=DecisionPriority.CRITICAL,
                    order=order,
                    target_time_hours=4,
                    verification_steps=[
                        "Verify service is no longer externally reachable."
                    ],
                )
            )
            order += 1

        if kev or exploit:
            recommendations.append(
                Recommendation(
                    title="Patch Vulnerability",
                    description="Apply the latest vendor security update.",
                    action=DecisionAction.REMEDIATE_NOW,
                    priority=DecisionPriority.CRITICAL,
                    order=order,
                    target_time_hours=24,
                    verification_steps=[
                        "Confirm installed version.",
                        "Run vulnerability scan.",
                    ],
                )
            )
            order += 1

        recommendations.append(
            Recommendation(
                title="Increase Monitoring",
                description="Enable enhanced monitoring and alerting for the affected asset.",
                action=DecisionAction.MONITOR,
                priority=DecisionPriority.MEDIUM,
                order=order,
                verification_steps=[
                    "Verify SIEM receives telemetry.",
                    "Verify alerts are triggered.",
                ],
            )
        )
        order += 1

        recommendations.append(
            Recommendation(
                title="Validate Remediation",
                description="Perform a verification scan after mitigation.",
                action=DecisionAction.INVESTIGATE,
                priority=DecisionPriority.MEDIUM,
                order=order,
                verification_steps=[
                    "Re-run scanner.",
                    "Verify finding is closed.",
                ],
            )
        )

        return recommendations