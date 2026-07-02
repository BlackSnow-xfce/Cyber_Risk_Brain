from dataclasses import dataclass
from typing import List

from .asset_registry.models import AssetMetadata
from .models import Asset, NormalizedFinding


@dataclass
class AssetContext:

    asset: Asset

    metadata: AssetMetadata

    findings: List[NormalizedFinding]

    internet_facing: bool

    critical_count: int

    high_count: int

    medium_count: int

    exploit_count: int

    max_cvss: float
