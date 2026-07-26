from __future__ import annotations

from core.decision.models import (
    AttackReasoning,
    BusinessImpact,
    Confidence,
)


class ExplainabilityEngine:
    """
    Builds a human-readable explanation of the decision.
    """

    def analyze(
        self,
        reasoning: AttackReasoning,
        business: BusinessImpact,
        confidence: Confidence,
    ) -> list[str]:

        explanation: list[str] = []

        explanation.append("=== PredatorAI Decision Summary ===")

        explanation.append(reasoning.summary)

        explanation.append("")

        explanation.append("Attack Vector:")

        explanation.append(
            reasoning.attack_vector or "Unknown"
        )

        explanation.append("")

        explanation.append("Supporting Factors:")

        if reasoning.supporting_factors:

            for factor in reasoning.supporting_factors:

                explanation.append(
                    f"- {factor}"
                )

        else:

            explanation.append(
                "- None"
            )

        explanation.append("")

        explanation.append("Limiting Factors:")

        if reasoning.limiting_factors:

            for factor in reasoning.limiting_factors:

                explanation.append(
                    f"- {factor}"
                )

        else:

            explanation.append(
                "- None"
            )

        explanation.append("")

        explanation.append("Likely Outcomes:")

        if reasoning.likely_outcomes:

            for outcome in reasoning.likely_outcomes:

                explanation.append(
                    f"- {outcome}"
                )

        else:

            explanation.append(
                "- Unknown"
            )

        explanation.append("")

        explanation.append("Business Impact:")

        explanation.append(
            business.summary
        )

        explanation.append("")

        explanation.append(
            f"Confidentiality: {business.confidentiality_impact}"
        )

        explanation.append(
            f"Integrity: {business.integrity_impact}"
        )

        explanation.append(
            f"Availability: {business.availability_impact}"
        )

        explanation.append(
            f"Operational: {business.operational_impact}"
        )

        explanation.append(
            f"Financial: {business.financial_impact}"
        )

        explanation.append(
            f"Regulatory: {business.regulatory_impact}"
        )

        explanation.append(
            f"Reputational: {business.reputational_impact}"
        )

        explanation.append("")

        explanation.append(
            f"Decision Confidence: {confidence.score:.0f}%"
        )

        explanation.append(
            f"Confidence Level: {confidence.level.value}"
        )

        explanation.append("")

        if confidence.reasons:

            explanation.append(
                "Confidence Factors:"
            )

            for reason in confidence.reasons:

                explanation.append(
                    f"- {reason}"
                )

            explanation.append("")

        if confidence.missing_information:

            explanation.append(
                "Missing Information:"
            )

            for item in confidence.missing_information:

                explanation.append(
                    f"- {item}"
                )

        return explanation