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
    from graph node data.
    """

    def analyze(
        self,
        node: dict[str, Any],
    ) -> list[Recommendation]:

        recommendations: list[Recommendation] = []

        order = 1

        exposed = bool(
            node.get("exposed", False)
        )

        threat_intel = bool(
            node.get("threat_intel", False)
        )

        detection = bool(
            node.get("detection", False)
        )

        criticality = str(
            node.get("criticality", "LOW")
        ).upper()

        if exposed:
            recommendations.append(
                Recommendation(
                    title="Restrict Internet Exposure",
                    description="Remove or limit external access until remediation has been verified.",
                    action=DecisionAction.MITIGATE,
                    priority=DecisionPriority.CRITICAL,
                    order=order,
                    target_time_hours=4,
                    verification_steps=[
                        "Verify the service is no longer Internet reachable."
                    ],
                )
            )
            order += 1

        if threat_intel:
            recommendations.append(
                Recommendation(
                    title="Investigate Threat Intelligence",
                    description="Validate whether active exploitation affects this finding.",
                    action=DecisionAction.INVESTIGATE,
                    priority=DecisionPriority.HIGH,
                    order=order,
                    target_time_hours=8,
                    verification_steps=[
                        "Review SIEM events.",
                        "Review EDR telemetry.",
                    ],
                )
            )
            order += 1

        if not detection:
            recommendations.append(
                Recommendation(
                    title="Improve Detection Coverage",
                    description="Deploy monitoring and alerting before remediation is completed.",
                    action=DecisionAction.MONITOR,
                    priority=DecisionPriority.HIGH,
                    order=order,
                    target_time_hours=24,
                    verification_steps=[
                        "Generate a test alert.",
                        "Verify telemetry reaches the SIEM.",
                    ],
                )
            )
            order += 1

        if criticality == "CRITICAL":
            recommendations.append(
                Recommendation(
                    title="Immediate Remediation",
                    description="Business critical asset requires immediate remediation.",
                    action=DecisionAction.REMEDIATE_NOW,
                    priority=DecisionPriority.CRITICAL,
                    order=order,
                    target_time_hours=24,
                    verification_steps=[
                        "Apply mitigation.",
                        "Run validation scan.",
                    ],
                )
            )
            order += 1

        recommendations.append(
            Recommendation(
                title="Validate Remediation",
                description="Confirm that the finding is fully resolved after mitigation.",
                action=DecisionAction.INVESTIGATE,
                priority=DecisionPriority.MEDIUM,
                order=order,
                verification_steps=[
                    "Re-run scan.",
                    "Confirm finding closure.",
                ],
            )
        )

        return recommendations
    