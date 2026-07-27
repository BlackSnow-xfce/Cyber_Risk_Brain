from __future__ import annotations

from core.decision.decision_context import DecisionContext
from core.decision.reason import Reason


class ReasonBuilder:
    """
    Converts DecisionContext into structured reasons.
    """

    def build(
        self,
        context: DecisionContext,
    ) -> list[Reason]:

        attack = context.decision.attack_reasoning

        reasons: list[Reason] = []

        if attack.internet_exposed:

            reasons.append(

                Reason(

                    title="Internet Exposure",

                    description=(
                        "The affected asset is directly "
                        "reachable from the Internet."
                    ),

                    category="Exposure",

                    source="Asset Registry",

                    impact=15,

                    confidence=1.0,

                )

            )

        if attack.known_exploited:

            reasons.append(

                Reason(

                    title="Known Exploited Vulnerability",

                    description=(
                        "The vulnerability is listed "
                        "in the CISA KEV catalog."
                    ),

                    category="Threat Intelligence",

                    source="CISA KEV",

                    impact=25,

                    confidence=1.0,

                )

            )

        if attack.public_exploit:

            reasons.append(

                Reason(

                    title="Public Exploit",

                    description=(
                        "Exploit code is publicly available."
                    ),

                    category="Threat Intelligence",

                    source="Exploit Intelligence",

                    impact=20,

                    confidence=0.95,

                )

            )

        if attack.high_epss:

            reasons.append(

                Reason(

                    title="High EPSS",

                    description=(
                        "High probability of exploitation."
                    ),

                    category="Threat Intelligence",

                    source="FIRST EPSS",

                    impact=15,

                    confidence=0.98,

                )

            )

        if attack.high_cvss:

            reasons.append(

                Reason(

                    title="Critical Severity",

                    description=(
                        "Critical CVSS score."
                    ),

                    category="Severity",

                    source="NVD",

                    impact=10,

                    confidence=0.95,

                )

            )

        if attack.crown_jewel:

            reasons.append(

                Reason(

                    title="Crown Jewel",

                    description=(
                        "Business critical asset."
                    ),

                    category="Business",

                    source="Asset Registry",

                    impact=30,

                    confidence=1.0,

                )

            )

        return reasons
    