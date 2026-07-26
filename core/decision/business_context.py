from __future__ import annotations

from typing import Any

from core.decision.models import BusinessImpact


class BusinessContextEngine:
    """
    Creates a deterministic business impact assessment from graph node data.
    """

    def analyze(
        self,
        node: dict[str, Any],
    ) -> BusinessImpact:

        criticality = str(
            node.get("criticality", "LOW")
        ).upper()

        owner = node.get("owner")

        exposed = bool(
            node.get("exposed", False)
        )

        service = (
            "Business Critical Service"
            if criticality in ("CRITICAL", "HIGH")
            else "Standard Service"
        )

        affected_processes = []

        if exposed:
            affected_processes.append(
                "External Service Delivery"
            )

        affected_processes.append(
            "Security Operations"
        )

        if criticality == "CRITICAL":
            summary = (
                "Compromise of this asset would have a critical business impact."
            )
            financial = "High"
            operational = "High"
            regulatory = "Possible"
            reputational = "High"

        elif criticality == "HIGH":
            summary = (
                "Compromise of this asset would have a significant business impact."
            )
            financial = "Medium"
            operational = "High"
            regulatory = "Possible"
            reputational = "Medium"

        elif criticality == "MEDIUM":
            summary = (
                "Compromise of this asset would have a moderate business impact."
            )
            financial = "Medium"
            operational = "Medium"
            regulatory = "Low"
            reputational = "Low"

        else:
            summary = (
                "Business impact is currently assessed as limited."
            )
            financial = "Low"
            operational = "Low"
            regulatory = "Low"
            reputational = "Low"

        return BusinessImpact(
            summary=summary,
            business_service=service,
            asset_criticality=criticality,
            confidentiality_impact=financial,
            integrity_impact=operational,
            availability_impact=operational,
            financial_impact=financial,
            operational_impact=operational,
            regulatory_impact=regulatory,
            reputational_impact=reputational,
            affected_processes=affected_processes,
        )
    