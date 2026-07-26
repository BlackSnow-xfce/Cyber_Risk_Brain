from __future__ import annotations

from typing import Any

from core.decision.models import BusinessImpact


class BusinessContextEngine:
    """
    Evaluates the business impact of a graph node.
    """

    def analyze(
        self,
        node: dict[str, Any],
    ) -> BusinessImpact:

        criticality = str(
            node.get("criticality", "LOW")
        ).upper()

        owner = node.get(
            "owner",
            "Unknown",
        )

        service = node.get(
            "business_service",
            owner,
        )

        confidentiality = "LOW"
        integrity = "LOW"
        availability = "LOW"

        financial = "LOW"
        operational = "LOW"
        regulatory = "LOW"
        reputational = "LOW"

        affected_processes: list[str] = []

        if criticality == "CRITICAL":

            confidentiality = "HIGH"
            integrity = "HIGH"
            availability = "HIGH"

            financial = "HIGH"
            operational = "HIGH"
            regulatory = "HIGH"
            reputational = "HIGH"

        elif criticality == "HIGH":

            confidentiality = "HIGH"
            integrity = "HIGH"
            availability = "MEDIUM"

            financial = "HIGH"
            operational = "HIGH"
            reputational = "HIGH"

        elif criticality == "MEDIUM":

            confidentiality = "MEDIUM"
            integrity = "MEDIUM"
            availability = "MEDIUM"

            operational = "MEDIUM"

            financial = "LOW"

        if node.get("exposed", False):

            operational = "HIGH"

            if financial == "LOW":
                financial = "MEDIUM"

        if node.get("threat_intel", False):

            regulatory = "HIGH"

            reputational = "HIGH"

        affected_processes.append(service)

        summary = (
            f"The asset belongs to '{service}' "
            f"and has business criticality "
            f"'{criticality}'."
        )

        return BusinessImpact(
            summary=summary,
            business_service=service,
            asset_criticality=criticality,
            confidentiality_impact=confidentiality,
            integrity_impact=integrity,
            availability_impact=availability,
            financial_impact=financial,
            operational_impact=operational,
            regulatory_impact=regulatory,
            reputational_impact=reputational,
            affected_processes=affected_processes,
        )