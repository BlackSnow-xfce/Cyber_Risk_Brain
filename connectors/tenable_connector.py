from connectors.base_connector import BaseConnector


class TenableConnector(BaseConnector):

    def test_connection(self):
        print("Tenable connector initialized")

    def get_findings(self):
        return []