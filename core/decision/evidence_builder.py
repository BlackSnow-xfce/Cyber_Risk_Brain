from __future__ import annotations

from typing import Any

from core.decision.models import Evidence, EvidenceType


class EvidenceBuilder:
    """
    Collects all evidence used during the decision process.
    """

    def build(
        self,
        node: dict[str, Any],
    ) -> list[Evidence]:

        evidence: list[Evidence] = []

        self._add(
            evidence,
            EvidenceType.ASSET,
            "asset_name",
            node.get("name"),
        )

        self._add(
            evidence,
            EvidenceType.BUSINESS_CONTEXT,
            "owner",
            node.get("owner"),
        )

        self._add(
            evidence,
            EvidenceType.BUSINESS_CONTEXT,
            "criticality",
            node.get("criticality"),
        )

        self._add(
            evidence,
            EvidenceType.EXPOSURE,
            "internet_exposed",
            node.get("exposed"),
        )

        self._add(
            evidence,
            EvidenceType.CONTROL,
            "detection",
            node.get("detection"),
        )

        self._add(
            evidence,
            EvidenceType.THREAT_INTELLIGENCE,
            "threat_intel",
            node.get("threat_intel"),
        )

        self._add(
            evidence,
            EvidenceType.ATTACK_PATH,
            "mitre",
            node.get("mitre"),
        )

        self._add(
            evidence,
            EvidenceType.BUSINESS_CONTEXT,
            "sla_days",
            node.get("sla_days"),
        )

        return evidence

    @staticmethod
    def _add(
        evidence: list[Evidence],
        evidence_type: EvidenceType,
        key: str,
        value: Any,
    ) -> None:

        if value is None:
            return

        evidence.append(
            Evidence(
                evidence_type=evidence_type,
                key=key,
                value=value,
            )
        )