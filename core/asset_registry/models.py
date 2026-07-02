from dataclasses import dataclass


@dataclass(slots=True)
class AssetMetadata:

    hostname: str

    asset_type: str = "Unknown"

    owner: str = "Unknown"

    business_unit: str = "Unknown"

    environment: str = "Unknown"

    criticality: str = "Medium"

    crown_jewel: bool = False
