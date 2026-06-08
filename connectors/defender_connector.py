from connectors.base_connector import BaseConnector


class DefenderConnector(BaseConnector):

    def test_connection(self):
        print("Defender connector initialized")

    def get_findings(self):
        return []