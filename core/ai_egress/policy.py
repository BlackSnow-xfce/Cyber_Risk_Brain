from dataclasses import dataclass
from enum import StrEnum

from core.ai_authorization import AIResourceType
from core.ai_context import AIContextClassification


AI_MODEL_EGRESS_POLICY_CONTRACT_VERSION = "1.0"


class AIModelEgressPurpose(StrEnum):
    FINDING_EXPLANATION = "finding_explanation"


class AIModelEgressDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class AIModelEgressField(StrEnum):
    FINDING_ID = "finding.id"
    FINDING_SOURCE = "finding.source"
    FINDING_TITLE = "finding.title"
    FINDING_VENDOR_SEVERITY = "finding.vendor_severity"


@dataclass(frozen=True, slots=True)
class AIModelEgressPolicy:
    purpose: AIModelEgressPurpose
    resource_type: AIResourceType
    permitted_classifications: frozenset[AIContextClassification]
    allowed_fields: frozenset[AIModelEgressField]
    decision: AIModelEgressDecision
    policy_source_reference: str
    contract_version: str = AI_MODEL_EGRESS_POLICY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, AIModelEgressPurpose):
            raise ValueError("purpose must be an AIModelEgressPurpose.")
        if not isinstance(self.resource_type, AIResourceType):
            raise ValueError("resource_type must be an AIResourceType.")
        if not isinstance(self.decision, AIModelEgressDecision):
            raise ValueError("decision must be an AIModelEgressDecision.")
        self._validate_classifications()
        self._validate_fields()
        if not isinstance(self.policy_source_reference, str) or not self.policy_source_reference.strip():
            raise ValueError("policy_source_reference must not be empty.")
        if self.contract_version != AI_MODEL_EGRESS_POLICY_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {AI_MODEL_EGRESS_POLICY_CONTRACT_VERSION}."
            )
        if self.decision is AIModelEgressDecision.ALLOW:
            if not self.permitted_classifications:
                raise ValueError("ALLOW requires permitted classifications.")
            if not self.allowed_fields:
                raise ValueError("ALLOW requires an explicit field allowlist.")
        elif self.permitted_classifications or self.allowed_fields:
            raise ValueError("DENY cannot carry effective permissions.")

    def _validate_classifications(self) -> None:
        if not isinstance(self.permitted_classifications, frozenset):
            raise ValueError("permitted_classifications must be a frozenset.")
        if any(
            not isinstance(classification, AIContextClassification)
            for classification in self.permitted_classifications
        ):
            raise ValueError("permitted_classifications contains an invalid value.")

    def _validate_fields(self) -> None:
        if not isinstance(self.allowed_fields, frozenset):
            raise ValueError("allowed_fields must be a frozenset.")
        if any(not isinstance(field, AIModelEgressField) for field in self.allowed_fields):
            raise ValueError("allowed_fields contains an invalid value.")

    def permits_field(self, field: AIModelEgressField | str) -> bool:
        return (
            self.decision is AIModelEgressDecision.ALLOW
            and isinstance(field, AIModelEgressField)
            and field in self.allowed_fields
        )

    def permits_classification(
        self, classification: AIContextClassification | None
    ) -> bool:
        return (
            self.decision is AIModelEgressDecision.ALLOW
            and isinstance(classification, AIContextClassification)
            and classification in self.permitted_classifications
        )

    def applies_to_resource_type(self, resource_type: AIResourceType) -> bool:
        return (
            self.decision is AIModelEgressDecision.ALLOW
            and resource_type is self.resource_type
        )

    def applies_to_purpose(self, purpose: AIModelEgressPurpose) -> bool:
        return self.decision is AIModelEgressDecision.ALLOW and purpose is self.purpose
