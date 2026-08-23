from dataclasses import dataclass
from enum import StrEnum

from core.ai_context.context import AIContextClassification


AI_AUTHORIZATION_SCOPE_CONTRACT_VERSION = "1.0"


class AIAuthorizationDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class AIResourceType(StrEnum):
    FINDING = "finding"
    INCIDENT = "incident"
    ASSET = "asset"
    EVIDENCE = "evidence"
    THREAT_INTELLIGENCE = "threat_intelligence"


@dataclass(frozen=True, slots=True)
class AIResourceReference:
    resource_type: AIResourceType
    resource_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.resource_type, AIResourceType):
            raise ValueError("resource_type must be an AIResourceType.")
        if not isinstance(self.resource_id, str) or not self.resource_id.strip():
            raise ValueError("resource_id must not be empty.")
        if self.resource_id == "*":
            raise ValueError("wildcard resource identifiers are not permitted.")


@dataclass(frozen=True, slots=True)
class AIResourceScope:
    resources: tuple[AIResourceReference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.resources, tuple) or not self.resources:
            raise ValueError("authorized resource scope must not be empty.")
        if any(not isinstance(resource, AIResourceReference) for resource in self.resources):
            raise ValueError("resource scope entries must be AIResourceReference values.")
        if len(set(self.resources)) != len(self.resources):
            raise ValueError("resource scope entries must be unique.")

    def permits_resource(self, resource: AIResourceReference) -> bool:
        return isinstance(resource, AIResourceReference) and resource in self.resources


@dataclass(frozen=True, slots=True)
class AIAuthorizationScope:
    subject_reference: str
    operation: str
    decision: AIAuthorizationDecision
    authorized_scope: AIResourceScope | None
    permitted_classifications: frozenset[AIContextClassification]
    decision_source_reference: str
    contract_version: str = AI_AUTHORIZATION_SCOPE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        self._required(self.subject_reference, "subject_reference")
        self._required(self.operation, "operation")
        self._required(self.decision_source_reference, "decision_source_reference")
        if not isinstance(self.decision, AIAuthorizationDecision):
            raise ValueError("decision must be an AIAuthorizationDecision.")
        if not isinstance(self.permitted_classifications, frozenset):
            raise ValueError("permitted_classifications must be a frozenset.")
        if any(
            not isinstance(classification, AIContextClassification)
            for classification in self.permitted_classifications
        ):
            raise ValueError("permitted_classifications contains an invalid value.")
        if self.contract_version != AI_AUTHORIZATION_SCOPE_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {AI_AUTHORIZATION_SCOPE_CONTRACT_VERSION}."
            )
        if self.decision is AIAuthorizationDecision.ALLOW:
            if not isinstance(self.authorized_scope, AIResourceScope):
                raise ValueError("ALLOW requires an authorized resource scope.")
            if not self.permitted_classifications:
                raise ValueError("ALLOW requires permitted classifications.")
        elif self.authorized_scope is not None or self.permitted_classifications:
            raise ValueError("DENY cannot carry an effective permissive scope.")

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must not be empty.")

    def permits_resource(self, resource: AIResourceReference) -> bool:
        return (
            self.decision is AIAuthorizationDecision.ALLOW
            and self.authorized_scope is not None
            and self.authorized_scope.permits_resource(resource)
        )

    def permits_classification(
        self, classification: AIContextClassification | None
    ) -> bool:
        return (
            self.decision is AIAuthorizationDecision.ALLOW
            and classification is not None
            and classification in self.permitted_classifications
        )
