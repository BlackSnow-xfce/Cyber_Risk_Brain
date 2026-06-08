from connectors.base_connector import BaseConnector


class CrowdStrikeConnector(BaseConnector):

    def test_connection(self):
        print("CrowdStrike connector initialized")

    def get_findings(self):
        return []