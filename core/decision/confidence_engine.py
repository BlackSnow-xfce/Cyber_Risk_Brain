from __future__ import annotations

from typing import Any

from core.decision.models import (
    Confidence,
    ConfidenceLevel,
)


class ConfidenceEngine:
    """
    Calculates a deterministic confidence assessment
    from the available graph node attributes.
    """

    def analyze(
        self,
        node: dict[str, Any],
    ) -> Confidence:

        score = 40.0

        reasons: list[str] = []

        missing_information: list[str] = []

        required_fields = (
            "name",
            "severity",
            "criticality",
            "exposed",
            "detection",
            "threat_intel",
            "mitre",
        )

        available_fields = 0

        for field_name in required_fields:

            value = node.get(field_name)

            if value is None or value == "":

                missing_information.append(
                    f"Missing value for '{field_name}'."
                )

            else:

                available_fields += 1

        completeness_score = (
            available_fields
            / len(required_fields)
        ) * 30.0

        score += completeness_score

        if node.get("severity"):

            score += 5.0

            reasons.append(
                "Vendor severity information is available."
            )

        if node.get("criticality"):

            score += 5.0

            reasons.append(
                "Asset criticality information is available."
            )

        if node.get("exposed") is not None:

            score += 5.0

            reasons.append(
                "Exposure information is available."
            )

        if node.get("detection") is not None:

            score += 5.0

            reasons.append(
                "Detection coverage information is available."
            )

        if node.get("threat_intel"):

            score += 5.0

            reasons.append(
                "Threat intelligence supports the decision."
            )

        if node.get("mitre"):

            score += 5.0

            reasons.append(
                "MITRE ATT&CK context supports the decision."
            )

        score = min(
            round(score, 2),
            100.0,
        )

        level = self._determine_level(
            score
        )

        if not reasons:

            reasons.append(
                "Confidence is based on the available finding attributes."
            )

        return Confidence(
            score=score,
            level=level,
            reasons=reasons,
            missing_information=missing_information,
        )

    @staticmethod
    def _determine_level(
        score: float,
    ) -> ConfidenceLevel:

        if score >= 90:
            return ConfidenceLevel.VERY_HIGH

        if score >= 75:
            return ConfidenceLevel.HIGH

        if score >= 50:
            return ConfidenceLevel.MEDIUM

        if score >= 25:
            return ConfidenceLevel.LOW

        return ConfidenceLevel.VERY_LOW
    