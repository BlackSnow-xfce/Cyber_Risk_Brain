from __future__ import annotations

from core.decision.models import DecisionResult
from core.decision.recommendation import Recommendation


class RecommendationBuilder:
    """
    Creates structured recommendations
    from a DecisionResult.
    """

    def build(
        self,
        decision: DecisionResult,
    ) -> list[Recommendation]:

        recommendations: list[
            Recommendation
        ] = []

        if decision.action.value == "REMEDIATE":

            recommendations.append(

                Recommendation(

                    title="Patch immediately",

                    description=(
                        "Apply the vendor security update "
                        "as soon as possible."
                    ),

                    priority="Critical",

                    estimated_risk_reduction=90.0,

                    estimated_effort="Medium",

                    estimated_cost="Low",

                    confidence=0.95,

                )

            )

        elif decision.action.value == "INVESTIGATE":

            recommendations.append(

                Recommendation(

                    title="Investigate finding",

                    description=(
                        "Collect additional evidence "
                        "before remediation."
                    ),

                    priority="High",

                    estimated_risk_reduction=40.0,

                    estimated_effort="Low",

                    estimated_cost="Low",

                    confidence=0.85,

                )

            )

        else:

            recommendations.append(

                Recommendation(

                    title="Monitor asset",

                    description=(
                        "Continue monitoring the asset "
                        "and reassess regularly."
                    ),

                    priority="Medium",

                    estimated_risk_reduction=15.0,

                    estimated_effort="Low",

                    estimated_cost="Low",

                    confidence=0.80,

                )

            )

        return recommendations
    