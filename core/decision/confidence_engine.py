from __future__ import annotations

from core.decision.confidence_factor import (
    ConfidenceFactor,
)
from core.decision.confidence_result import (
    ConfidenceResult,
)
from core.decision.decision_context import (
    DecisionContext,
)


class ConfidenceEngine:
    """
    Calculates explainable confidence.

    Every confidence point can later be
    displayed inside the Dashboard.
    """

    def calculate(
        self,
        context: DecisionContext,
    ) -> ConfidenceResult:

        attack = context.decision.attack_reasoning

        score = 0.0

        factors: list[
            ConfidenceFactor
        ] = []

        def add(
            name: str,
            description: str,
            weight: float,
        ) -> None:

            nonlocal score

            score += weight

            factors.append(

                ConfidenceFactor(

                    name=name,

                    description=description,

                    weight=weight,

                    positive=True,

                )

            )

        if attack.internet_exposed:

            add(

                "Internet Facing",

                "Asset is reachable from the Internet.",

                15,

            )

        if attack.known_exploited:

            add(

                "KEV",

                "Known exploited vulnerability.",

                25,

            )

        if attack.public_exploit:

            add(

                "Public Exploit",

                "Exploit code is publicly available.",

                15,

            )

        if attack.high_epss:

            add(

                "High EPSS",

                "High probability of exploitation.",

                15,

            )

        if attack.high_cvss:

            add(

                "Critical CVSS",

                "Critical severity.",

                10,

            )

        if attack.crown_jewel:

            add(

                "Crown Jewel",

                "Business critical asset.",

                20,

            )

        score = min(
            score,
            100.0,
        )

        return ConfidenceResult(

            score=score,

            factors=factors,

        )
    