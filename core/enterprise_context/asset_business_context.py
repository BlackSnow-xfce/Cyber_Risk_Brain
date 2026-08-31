from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BusinessEnvironment(str, Enum):
    PRODUCTION = "PRODUCTION"
    PRE_PRODUCTION = "PRE_PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"


class ServiceCriticality(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True, slots=True)
class AssetBusinessContext:
    canonical_asset_id: str
    business_service: str
    environment: BusinessEnvironment
    service_criticality: ServiceCriticality
    source_reference: str

    def __post_init__(self) -> None:
        for name in (
            "canonical_asset_id",
            "business_service",
            "source_reference",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Asset business context {name} must not be empty.")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.environment, BusinessEnvironment):
            raise ValueError("Asset business context environment is invalid.")
        if not isinstance(self.service_criticality, ServiceCriticality):
            raise ValueError("Asset business context service criticality is invalid.")
