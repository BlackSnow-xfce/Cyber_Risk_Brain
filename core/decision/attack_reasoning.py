from __future__ import annotations

from typing import Any

from core.decision.models import AttackReasoning


class AttackReasoningEngine:
    """
    Creates deterministic attack reasoning from graph node data.
    """

    def analyze(
        self,
        node: dict[str, Any],
    ) -> AttackReasoning:

        supporting_factors: list[str] = []

        limiting_factors: list[str] = []

        attack_steps: list[str] = []

        likely_outcomes: list[str] = []

        exposed = bool(
            node.get("exposed", False)
        )

        threat_intel = bool(
            node.get("threat_intel", False)
        )

        detection = bool(
            node.get("detection", False)
        )

        criticality = str(
            node.get("criticality", "LOW")
        ).upper()

        severity = str(
            node.get("severity", "UNKNOWN")
        ).upper()

        mitre = node.get("mitre")

        if exposed:

            supporting_factors.append(
                "The affected asset is exposed to the Internet."
            )

            attack_steps.append(
                "An attacker can directly reach the exposed service."
            )

        else:

            limiting_factors.append(
                "The affected asset is not directly exposed to the Internet."
            )

        if threat_intel:

            supporting_factors.append(
                "Threat intelligence indicates active or relevant exploitation context."
            )

            attack_steps.append(
                "An attacker may use known exploitation techniques against the finding."
            )

        else:

            limiting_factors.append(
                "No supporting threat intelligence is currently available."
            )

        if severity == "CRITICAL":

            supporting_factors.append(
                "The source system rated the finding as critical."
            )

            likely_outcomes.append(
                "Successful exploitation may result in severe system compromise."
            )

        elif severity == "HIGH":

            supporting_factors.append(
                "The source system rated the finding as high severity."
            )

            likely_outcomes.append(
                "Successful exploitation may result in significant security impact."
            )

        if criticality == "CRITICAL":

            supporting_factors.append(
                "The affected asset is classified as business critical."
            )

            likely_outcomes.append(
                "Compromise may cause high operational and business impact."
            )

        elif criticality == "HIGH":

            supporting_factors.append(
                "The affected asset has high business criticality."
            )

        if not detection:

            supporting_factors.append(
                "Detection coverage is missing or insufficient."
            )

            attack_steps.append(
                "Malicious activity may remain undetected during exploitation."
            )

            likely_outcomes.append(
                "The attacker may gain additional dwell time."
            )

        else:

            limiting_factors.append(
                "Detection coverage may reduce attacker dwell time."
            )

        if mitre:

            supporting_factors.append(
                "MITRE ATT&CK context is available for the finding."
            )

            attack_steps.append(
                "The attacker may follow known ATT&CK techniques associated with the finding."
            )

        if not supporting_factors:

            limiting_factors.append(
                "Insufficient contextual evidence is available for strong attack reasoning."
            )

        probability = self._determine_probability(
            supporting_factors
        )

        attack_vector = (
            "External Attack Surface"
            if exposed
            else "Internal Attack Surface"
        )

        summary = (
            f"PredatorAI identified {len(supporting_factors)} supporting "
            f"attack indicators and estimated the exploitation "
            f"probability as {probability}."
        )

        return AttackReasoning(
            summary=summary,
            attack_vector=attack_vector,
            exploitation_probability=probability,
            likely_outcomes=likely_outcomes,
            attack_steps=attack_steps,
            supporting_factors=supporting_factors,
            limiting_factors=limiting_factors,
        )

    @staticmethod
    def _determine_probability(
        supporting_factors: list[str],
    ) -> str:

        factor_count = len(
            supporting_factors
        )

        if factor_count >= 6:
            return "Very High"

        if factor_count >= 4:
            return "High"

        if factor_count >= 2:
            return "Medium"

        return "Low"
    