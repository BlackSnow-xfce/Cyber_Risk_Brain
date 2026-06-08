from connectors.base_connector import BaseConnector


class Rapid7Connector(BaseConnector):

    def test_connection(self):
        print("Rapid7 connector initialized")

    def get_findings(self):
        return []