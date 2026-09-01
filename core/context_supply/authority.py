from dataclasses import dataclass

from .observation import ContextObservation, ContextType


@dataclass(frozen=True, slots=True)
class SourceAuthority:
    source_id: str
    organization_id: str
    context_types: frozenset[ContextType]
    asset_ids: frozenset[str]
    authority_reference: str

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.organization_id.strip() or not self.authority_reference.strip():
            raise ValueError("Source authority identity is required.")
        if not self.context_types or not self.asset_ids or any(not asset.strip() for asset in self.asset_ids):
            raise ValueError("Source authority requires explicit context and asset scopes.")

    def permits(self, observation: ContextObservation) -> bool:
        source = self.source_id.lower().replace("_", "-")
        forbidden_roles = ("ai", "model", "greenbone", "product-owner", "administrator", "admin", "generic-operator")
        return (observation.source_id == self.source_id and observation.organization_id == self.organization_id and observation.context_type in self.context_types and observation.subject.asset_id in self.asset_ids and observation.authority_reference == self.authority_reference and not any(role in source for role in forbidden_roles))


def require_authority(observation: ContextObservation, authority: SourceAuthority) -> None:
    if not authority.permits(observation):
        raise ValueError("Source is not authoritative for this organization, context, and asset scope.")
