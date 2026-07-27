from __future__ import annotations

from core.decision.confidence_factor import (
    ConfidenceFactor,
)
from core.decision.confidence_result import (
    ConfidenceResult,
)
from core.decision.models import (
    AttackReasoning,
    ConfidenceLevel,
)


class ConfidenceEngine:
    """
    Calculates explainable confidence.
    """

    def calculate(
        self,
        attack: AttackReasoning,
    ) -> ConfidenceResult:

        score = 0.0

        factors: list[
            ConfidenceFactor
        ] = []

        reasons: list[str] = []

        def add(
            name: str,
            description: str,
            weight: float,
        ) -> None:

            nonlocal score

            score += weight

            reasons.append(name)

            factors.append(

                ConfidenceFactor(

                    name=name,

                    description=description,

                    weight=weight,

                    positive=True,

                )

            )

        if attack.attack_vector == "External Attack Surface":

            add(

                "Internet Facing",

                "Asset is reachable from the Internet.",

                15,

            )

        if attack.exploitation_probability in (

            "High",

            "Very High",

        ):

            add(

                "High Exploitation Probability",

                "Attack probability is elevated.",

                25,

            )

        if attack.supporting_factors:

            add(

                "Supporting Evidence",

                "Multiple supporting indicators available.",

                min(

                    len(
                        attack.supporting_factors
                    ) * 5,

                    30,

                ),

            )

        score = min(
            score,
            100.0,
        )

        if score >= 90:
            level = ConfidenceLevel.VERY_HIGH
        elif score >= 75:
            level = ConfidenceLevel.HIGH
        elif score >= 50:
            level = ConfidenceLevel.MEDIUM
        elif score >= 25:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW

        return ConfidenceResult(

            score=score,

            level=level,

            reasons=reasons,

            missing_information=[],

            factors=factors,

        )