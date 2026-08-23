from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from core.ai_authorization import (
    AIAuthorizationScope,
    AIResourceReference,
    AIResourceType,
)
from core.ai_binding import BoundAIContext
from core.ai_context import (
    AIContextClassification,
    AIContextItem,
    AIContextProvenance,
    AIContextProvenanceType,
    AIContextTrustLevel,
    AIContextType,
)
from core.models import UniversalFinding


FINDING_RETRIEVAL_OPERATION = "retrieve_finding"


class FindingResourceReader(Protocol):
    def get_findings(self) -> Sequence[UniversalFinding]:
        ...


@dataclass(frozen=True, slots=True)
class RetrievedFinding:
    """The exact repository resource together with its bound AI context."""

    finding: UniversalFinding
    bound_context: BoundAIContext


class FindingTrustedRetrievalService:
    """Trusted boundary for one exact, repository-backed Finding retrieval."""

    def __init__(self, reader: FindingResourceReader) -> None:
        self._reader = reader

    def retrieve(
        self,
        authorization: AIAuthorizationScope | None,
        requested_resource: AIResourceReference | None,
    ) -> BoundAIContext | None:
        retrieved = self.retrieve_finding(authorization, requested_resource)
        return None if retrieved is None else retrieved.bound_context

    def retrieve_finding(
        self,
        authorization: AIAuthorizationScope | None,
        requested_resource: AIResourceReference | None,
    ) -> RetrievedFinding | None:
        if not isinstance(authorization, AIAuthorizationScope):
            return None
        if not isinstance(requested_resource, AIResourceReference):
            return None
        if requested_resource.resource_type is not AIResourceType.FINDING:
            return None
        if authorization.operation != FINDING_RETRIEVAL_OPERATION:
            return None
        if not authorization.permits_resource(requested_resource):
            return None
        if not authorization.permits_classification(AIContextClassification.INTERNAL):
            return None

        finding = self._find_exact(requested_resource.resource_id)
        if finding is None:
            return None
        bound_context = self._bind_finding(finding, requested_resource)
        if bound_context is None:
            return None
        return RetrievedFinding(finding=finding, bound_context=bound_context)

    def _find_exact(self, resource_id: str) -> UniversalFinding | None:
        match: UniversalFinding | None = None
        for finding in self._reader.get_findings():
            if isinstance(finding, UniversalFinding) and finding.id == resource_id:
                if match is not None:
                    return None
                match = finding
        return match

    @staticmethod
    def _bind_finding(
        finding: UniversalFinding,
        requested_resource: AIResourceReference,
    ) -> BoundAIContext | None:
        if finding.id != requested_resource.resource_id:
            return None
        source_reference = f"finding:{finding.source}:{finding.id}"
        item = AIContextItem(
            content=finding.title,
            context_type=AIContextType.SECURITY_FINDING,
            trust_level=AIContextTrustLevel.UNTRUSTED,
            source_reference=source_reference,
            provenance=AIContextProvenance(
                AIContextProvenanceType.EXTERNAL,
                source_reference,
            ),
            classification=AIContextClassification.INTERNAL,
        )
        return BoundAIContext(
            context_item=item,
            resource_reference=requested_resource,
        )
