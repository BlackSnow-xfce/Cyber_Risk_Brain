from .models import AssetMetadata


class AssetRegistry:

    def __init__(self):

        #
        # Temporary in-memory registry.
        #
        # Later this will be replaced by:
        # - CMDB
        # - ServiceNow
        # - NetBox
        # - CSV
        # - REST API
        #

        self.assets = {

            "Server01": AssetMetadata(

                hostname="Server01",

                asset_type="Web Server",

                owner="Infrastructure",

                business_unit="IT",

                environment="Production",

                criticality="High",

                crown_jewel=True

            ),

            "Fileserver": AssetMetadata(

                hostname="Fileserver",

                asset_type="File Server",

                owner="IT Operations",

                business_unit="Corporate",

                environment="Production",

                criticality="Medium",

                crown_jewel=False

            )
        }

    def get(self, hostname):

        return self.assets.get(
            hostname,
            AssetMetadata(hostname=hostname)
        )
