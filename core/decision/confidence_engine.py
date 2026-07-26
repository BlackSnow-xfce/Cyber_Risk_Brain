from __future__ import annotations

from typing import Any

from core.decision.models import (
    DecisionAction,
    DecisionPriority,
    Recommendation,
)


class RecommendationEngine:
    """
    Generates deterministic remediation recommendations
    based on graph node attributes.
    """

    def analyze(
        self,
        node: dict[str, Any],
    ) -> list[Recommendation]:

        recommendations: list[Recommendation] = []

        order = 1

        criticality = str(
            node.get("criticality", "LOW")
        ).upper()

        exposed = bool(
            node.get("exposed", False)
        )

        detection = bool(
            node.get("detection", False)
        )

        threat_intel = bool(
            node.get("threat_intel", False)
        )

        if exposed:

            recommendations.append(
                Recommendation(
                    title="Remove Internet Exposure",
                    description=(
                        "Restrict or remove external access "
                        "until remediation is completed."
                    ),
                    action=DecisionAction.MITIGATE,
                    priority=DecisionPriority.CRITICAL,
                    order=order,
                    target_time_hours=4,
                    verification_steps=[
                        "Verify asset is no longer reachable from the Internet."
                    ],
                )
            )

            order += 1

        if threat_intel:

            recommendations.append(
                Recommendation(
                    title="Investigate Threat Intelligence",
                    description=(
                        "Review threat intelligence and determine "
                        "whether exploitation has already occurred."
                    ),
                    action=DecisionAction.INVESTIGATE,
                    priority=DecisionPriority.HIGH,
                    order=order,
                    target_time_hours=8,
                    verification_steps=[
                        "Search SIEM.",
                        "Review EDR telemetry.",
                        "Check authentication logs.",
                    ],
                )
            )

            order += 1

        if not detection:

            recommendations.append(
                Recommendation(
                    title="Improve Detection Coverage",
                    description=(
                        "Deploy detection rules and ensure the "
                        "asset is monitored."
                    ),
                    action=DecisionAction.MITIGATE,
                    priority=DecisionPriority.HIGH,
                    order=order,
                    target_time_hours=24,
                    verification_steps=[
                        "Verify telemetry.",
                        "Generate test alert.",
                    ],
                )
            )

            order += 1

        if criticality == "CRITICAL":

            recommendations.append(
                Recommendation(
                    title="Immediate Remediation",
                    description=(
                        "Critical business asset requires immediate "
                        "remediation and validation."
                    ),
                    action=DecisionAction.REMEDIATE_NOW,
                    priority=DecisionPriority.CRITICAL,
                    order=order,
                    target_time_hours=24,
                    verification_steps=[
                        "Apply mitigation.",
                        "Run verification scan.",
                        "Confirm finding closure.",
                    ],
                )
            )

            order += 1

        recommendations.append(
            Recommendation(
                title="Continuous Monitoring",
                description=(
                    "Continue monitoring until the finding "
                    "has been fully remediated."
                ),
                action=DecisionAction.MONITOR,
                priority=DecisionPriority.MEDIUM,
                order=order,
                verification_steps=[
                    "Review SIEM alerts.",
                    "Verify no new indicators appear.",
                ],
            )
        )

        return recommendations