from dataclasses import dataclass

from core.ai_egress import (
    AIModelEgressDecision,
    AIModelEgressField,
    AIModelEgressPolicy,
    AIModelEgressPurpose,
)
from core.ai_authorization import AIResourceType
from core.ai_context import AIContextClassification
from core.models import UniversalFinding


FINDING_EGRESS_CLASSIFICATION = AIContextClassification.INTERNAL
FINDING_EXPLANATION_EGRESS_POLICY = AIModelEgressPolicy(
    purpose=AIModelEgressPurpose.FINDING_EXPLANATION,
    resource_type=AIResourceType.FINDING,
    permitted_classifications=frozenset({FINDING_EGRESS_CLASSIFICATION}),
    allowed_fields=frozenset(
        {
            AIModelEgressField.FINDING_TITLE,
            AIModelEgressField.FINDING_VENDOR_SEVERITY,
        }
    ),
    decision=AIModelEgressDecision.ALLOW,
    policy_source_reference="policy:finding-explanation",
)
_SUPPORTED_FIELDS = frozenset(
    {
        AIModelEgressField.FINDING_TITLE,
        AIModelEgressField.FINDING_VENDOR_SEVERITY,
    }
)


@dataclass(frozen=True, slots=True)
class FindingModelEgressPayload:
    """Minimal positive-allowlist payload for Finding explanation."""

    title: str | None = None
    vendor_severity: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {}
        if self.title is not None:
            payload[AIModelEgressField.FINDING_TITLE.value] = self.title
        if self.vendor_severity is not None:
            payload[AIModelEgressField.FINDING_VENDOR_SEVERITY.value] = (
                self.vendor_severity
            )
        return payload


class FindingModelEgressProjector:
    """Project explicitly allowed Finding fields without retrieval or I/O."""

    @staticmethod
    def project(
        finding: UniversalFinding | None,
        policy: AIModelEgressPolicy | None,
    ) -> FindingModelEgressPayload | None:
        if not isinstance(finding, UniversalFinding):
            return None
        if not isinstance(policy, AIModelEgressPolicy):
            return None
        if not policy.applies_to_purpose(AIModelEgressPurpose.FINDING_EXPLANATION):
            return None
        if not policy.applies_to_resource_type(AIResourceType.FINDING):
            return None
        if not policy.permits_classification(FINDING_EGRESS_CLASSIFICATION):
            return None
        if not policy.allowed_fields.issubset(_SUPPORTED_FIELDS):
            return None

        title = (
            finding.title
            if policy.permits_field(AIModelEgressField.FINDING_TITLE)
            else None
        )
        vendor_severity = (
            finding.vendor_severity
            if policy.permits_field(AIModelEgressField.FINDING_VENDOR_SEVERITY)
            else None
        )
        return FindingModelEgressPayload(
            title=title,
            vendor_severity=vendor_severity,
        )
