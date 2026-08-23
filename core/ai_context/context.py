from dataclasses import dataclass
from enum import StrEnum


AI_CONTEXT_ITEM_CONTRACT_VERSION = "1.0"


class AIContextType(StrEnum):
    SYSTEM_POLICY = "system_policy"
    APPLICATION_CONTEXT = "application_context"
    USER_INPUT = "user_input"
    SECURITY_FINDING = "security_finding"
    THREAT_INTELLIGENCE = "threat_intelligence"
    RETRIEVED_CONTENT = "retrieved_content"
    TOOL_RESULT = "tool_result"


class AIContextTrustLevel(StrEnum):
    TRUSTED = "trusted"
    CONTROLLED = "controlled"
    UNTRUSTED = "untrusted"


class AIContextProvenanceType(StrEnum):
    CONTROLLED_PREDATORAI = "controlled_predatorai"
    EXTERNAL = "external"


class AIContextClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass(frozen=True, slots=True)
class AIContextProvenance:
    source_type: AIContextProvenanceType
    source_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, AIContextProvenanceType):
            raise ValueError("source_type must be an AIContextProvenanceType.")
        if not isinstance(self.source_reference, str) or not self.source_reference.strip():
            raise ValueError("source_reference must not be empty.")


_ALWAYS_UNTRUSTED_TYPES = frozenset(
    {
        AIContextType.USER_INPUT,
        AIContextType.SECURITY_FINDING,
        AIContextType.THREAT_INTELLIGENCE,
        AIContextType.RETRIEVED_CONTENT,
        AIContextType.TOOL_RESULT,
    }
)


@dataclass(frozen=True, slots=True)
class AIContextItem:
    content: str
    context_type: AIContextType
    trust_level: AIContextTrustLevel
    source_reference: str
    provenance: AIContextProvenance
    classification: AIContextClassification
    contract_version: str = AI_CONTEXT_ITEM_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise ValueError("content must be a string.")
        if not isinstance(self.context_type, AIContextType):
            raise ValueError("context_type must be an AIContextType.")
        if not isinstance(self.trust_level, AIContextTrustLevel):
            raise ValueError("trust_level must be an AIContextTrustLevel.")
        if not isinstance(self.source_reference, str) or not self.source_reference.strip():
            raise ValueError("source_reference must not be empty.")
        if not isinstance(self.provenance, AIContextProvenance):
            raise ValueError("provenance must be an AIContextProvenance.")
        if self.source_reference != self.provenance.source_reference:
            raise ValueError("source_reference must match provenance.source_reference.")
        if not isinstance(self.classification, AIContextClassification):
            raise ValueError("classification must be an AIContextClassification.")
        if self.contract_version != AI_CONTEXT_ITEM_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {AI_CONTEXT_ITEM_CONTRACT_VERSION}."
            )

        controlled_source = (
            self.provenance.source_type == AIContextProvenanceType.CONTROLLED_PREDATORAI
        )
        if self.context_type in _ALWAYS_UNTRUSTED_TYPES:
            if self.trust_level != AIContextTrustLevel.UNTRUSTED:
                raise ValueError(f"{self.context_type} must remain untrusted.")
            return
        if not controlled_source and self.trust_level != AIContextTrustLevel.UNTRUSTED:
            raise ValueError("External context cannot be trusted or controlled.")

