from .asset_registry import AssetRegistry
from .context import AssetContext


class ContextBuilder:

    def __init__(self):

        self.registry = AssetRegistry()

    def build(self, findings):

        asset = findings[0].asset

        metadata = self.registry.get(asset.hostname)

        return AssetContext(

            asset=asset,

            metadata=metadata,

            findings=findings,

            internet_facing=any(
                f.asset.internet_facing
                for f in findings
            ),

            critical_count=sum(
                1
                for f in findings
                if f.vulnerability.severity.lower() == "critical"
            ),

            high_count=sum(
                1
                for f in findings
                if f.vulnerability.severity.lower() == "high"
            ),

            medium_count=sum(
                1
                for f in findings
                if f.vulnerability.severity.lower() == "medium"
            ),

            exploit_count=sum(
                1
                for f in findings
                if f.vulnerability.exploit_available
            ),

            max_cvss=max(
                f.vulnerability.cvss
                for f in findings
            )
        )
