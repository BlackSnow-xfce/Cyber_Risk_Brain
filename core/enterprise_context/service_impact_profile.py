from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BusinessImportance(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True, slots=True)
class ServiceImpactProfile:
    canonical_asset_id: str
    business_service: str
    confidentiality_importance: BusinessImportance
    integrity_importance: BusinessImportance
    availability_importance: BusinessImportance
    source_reference: str

    def __post_init__(self) -> None:
        for name in ("canonical_asset_id", "business_service", "source_reference"):
            value = getattr(self, name)
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"Service impact profile {name} is invalid.")
        for name in (
            "confidentiality_importance",
            "integrity_importance",
            "availability_importance",
        ):
            if not isinstance(getattr(self, name), BusinessImportance):
                raise ValueError(f"Service impact profile {name} is invalid.")
