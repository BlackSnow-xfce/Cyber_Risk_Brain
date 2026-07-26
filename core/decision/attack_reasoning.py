from __future__ import annotations

from core.decision.models import AttackReasoning


class AttackReasoningEngine:
    """
    Creates a human-readable attack reasoning based on
    technical context and threat intelligence.
    """

    def analyze(self, finding) -> AttackReasoning:
        supporting_factors: list[str] = []
        limiting_factors: list[str] = []
        attack_steps: list[str] = []
        likely_outcomes: list[str] = []

        # -----------------------------
        # Internet Exposure
        # -----------------------------
        if getattr(finding.asset, "internet_facing", False):
            supporting_factors.append(
                "Asset is reachable from the Internet."
            )
            attack_steps.append(
                "Attacker can directly reach the exposed service."
            )

        # -----------------------------
        # Known Exploited Vulnerability
        # -----------------------------
        if getattr(finding, "kev", False):
            supporting_factors.append(
                "Vulnerability is listed in CISA KEV."
            )
            attack_steps.append(
                "Public exploitation is already observed."
            )

        # -----------------------------
        # Public Exploit
        # -----------------------------
        if getattr(finding, "public_exploit", False):
            supporting_factors.append(
                "Public exploit is available."
            )
            attack_steps.append(
                "Exploit can likely be used with little modification."
            )

        # -----------------------------
        # EPSS
        # -----------------------------
        if getattr(finding, "epss", 0.0) >= 0.90:
            supporting_factors.append(
                "Very high EPSS score."
            )

        # -----------------------------
        # Crown Jewel
        # -----------------------------
        if getattr(finding.asset, "crown_jewel", False):
            supporting_factors.append(
                "Asset is classified as Crown Jewel."
            )
            likely_outcomes.append(
                "High business impact after compromise."
            )

        # -----------------------------
        # Domain Controller
        # -----------------------------
        asset_type = getattr(finding.asset, "asset_type", "").lower()

        if asset_type == "domain_controller":
            supporting_factors.append(
                "Target is a Domain Controller."
            )
            likely_outcomes.append(
                "Privilege escalation and lateral movement are likely."
            )

        # -----------------------------
        # Missing Context
        # -----------------------------
        if not supporting_factors:
            limiting_factors.append(
                "Insufficient contextual evidence available."
            )

        # -----------------------------
        # Probability
        # -----------------------------
        if len(supporting_factors) >= 5:
            probability = "Very High"
        elif len(supporting_factors) >= 3:
            probability = "High"
        elif len(supporting_factors) >= 2:
            probability = "Medium"
        else:
            probability = "Low"

        summary = (
            f"PredatorAI identified {len(supporting_factors)} supporting "
            f"risk indicators resulting in an estimated exploitation "
            f"probability of {probability}."
        )

        return AttackReasoning(
            summary=summary,
            attack_vector="External Attack Surface",
            exploitation_probability=probability,
            attack_steps=attack_steps,
            likely_outcomes=likely_outcomes,
            supporting_factors=supporting_factors,
            limiting_factors=limiting_factors,
        )