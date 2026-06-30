from collections import defaultdict


class AssetResolver:

    def resolve(self, findings):

        assets = defaultdict(list)

        for finding in findings:

            key = (
                finding.asset.hostname
                if finding.asset.hostname
                else finding.asset.ip
            )

            assets[key].append(finding)

        return assets
