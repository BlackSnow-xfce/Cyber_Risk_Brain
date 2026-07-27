from __future__ import annotations

from core.decision.business_impact import BusinessImpact
from core.decision.models import DecisionResult


class BusinessImpactBuilder:
    """
    Builds business impact information from a DecisionResult.
    """

    def build(
        self,
        decision: DecisionResult,
    ) -> BusinessImpact:

        attack = decision.attack_reasoning

        if attack.crown_jewel:

            return BusinessImpact(

                summary=(
                    "Critical business service may be compromised."
                ),

                business_service="Unknown",

                affected_process="Core Business",

                financial_impact="High",

                operational_impact="Critical",

                reputation_impact="High",

                regulatory_impact="Possible",

                estimated_loss=500000.0,

                confidence=0.90,

            )

        return BusinessImpact(

            summary=(
                "Limited business impact expected."
            ),

            business_service="Unknown",

            affected_process="Unknown",

            financial_impact="Low",

            operational_impact="Low",

            reputation_impact="Low",

            regulatory_impact="None",

            estimated_loss=1000.0,

            confidence=0.75,

        )
    