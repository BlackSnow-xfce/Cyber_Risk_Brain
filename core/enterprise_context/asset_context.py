from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address


class AssetCriticality(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AssetIdentifierType(str, Enum):
    IP_ADDRESS = "ip_address"


@dataclass(frozen=True)
class ObservedAssetIdentifier:
    identifier_type: AssetIdentifierType
    value: str

    def __post_init__(self) -> None:
        normalized_value = self.value.strip()

        if not normalized_value:
            raise ValueError("Observed asset identifier must not be empty.")

        if self.identifier_type is AssetIdentifierType.IP_ADDRESS:
            try:
                normalized_value = str(ip_address(normalized_value))
            except ValueError as error:
                raise ValueError(
                    "Observed ip_address identifier is invalid."
                ) from error

        object.__setattr__(self, "value", normalized_value)


@dataclass(frozen=True)
class AssetContext:
    observed_identifier: ObservedAssetIdentifier
    canonical_asset_id: str
    criticality: AssetCriticality
    source_reference: str

    def __post_init__(self) -> None:
        canonical_asset_id = self.canonical_asset_id.strip()
        source_reference = self.source_reference.strip()

        if not canonical_asset_id:
            raise ValueError("Canonical asset ID must not be empty.")

        if not source_reference:
            raise ValueError("Asset context source reference must not be empty.")

        object.__setattr__(self, "canonical_asset_id", canonical_asset_id)
        object.__setattr__(self, "source_reference", source_reference)
