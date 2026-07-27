from __future__ import annotations

from core.decision.evidence import Evidence
from core.decision.models import AttackReasoning


class EvidenceBuilder:
    """
    Converts AttackReasoning into explainable evidence.
    """

    def build(
        self,
        attack: AttackReasoning,
    ) -> list[Evidence]:

        evidence: list[Evidence] = []

        if attack.attack_vector == "External Attack Surface":

            evidence.append(

                Evidence(

                    name="Internet Facing",

                    source="Asset Registry",

                    description="Asset is directly reachable from the Internet.",

                    impact=15.0,

                    confidence=1.0,

                )

            )

        if attack.exploitation_probability in (

            "High",

            "Very High",

        ):

            evidence.append(

                Evidence(

                    name="High Exploitation Probability",

                    source="PredatorAI",

                    description="Multiple indicators support exploitation.",

                    impact=25.0,

                    confidence=1.0,

                )

            )

        for factor in attack.supporting_factors:

            evidence.append(

                Evidence(

                    name=factor,

                    source="PredatorAI",

                    description=factor,

                    impact=5.0,

                    confidence=0.9,

                )

            )

        return evidence
    