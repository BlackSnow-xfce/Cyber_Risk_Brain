from __future__ import annotations

from core.decision.evidence import Evidence
from core.decision.models import DecisionResult


class EvidenceBuilder:
    """
    Converts DecisionResult into explainable evidence.
    """

    def build(
        self,
        decision: DecisionResult,
    ) -> list[Evidence]:

        evidence: list[Evidence] = []

        attack = decision.attack_reasoning

        if attack.internet_exposed:

            evidence.append(

                Evidence(

                    name="Internet Facing",

                    source="Asset Registry",

                    description=(
                        "Asset is directly reachable "
                        "from the Internet."
                    ),

                    impact=15.0,

                    confidence=1.0,

                )

            )

        if attack.known_exploited:

            evidence.append(

                Evidence(

                    name="CISA KEV",

                    source="Threat Intelligence",

                    description=(
                        "Known exploited vulnerability."
                    ),

                    impact=25.0,

                    confidence=1.0,

                )

            )

        if attack.public_exploit:

            evidence.append(

                Evidence(

                    name="Public Exploit",

                    source="Exploit Intelligence",

                    description=(
                        "Public exploit is available."
                    ),

                    impact=20.0,

                    confidence=0.95,

                )

            )

        if attack.high_epss:

            evidence.append(

                Evidence(

                    name="High EPSS",

                    source="FIRST EPSS",

                    description=(
                        "High exploitation probability."
                    ),

                    impact=15.0,

                    confidence=0.98,

                )

            )

        if attack.high_cvss:

            evidence.append(

                Evidence(

                    name="High CVSS",

                    source="NVD",

                    description=(
                        "Critical CVSS severity."
                    ),

                    impact=10.0,

                    confidence=0.95,

                )

            )

        if attack.crown_jewel:

            evidence.append(

                Evidence(

                    name="Crown Jewel",

                    source="Asset Registry",

                    description=(
                        "Business critical asset."
                    ),

                    impact=30.0,

                    confidence=1.0,

                )

            )

        return evidence
    