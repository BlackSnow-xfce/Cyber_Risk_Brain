from connectors.base_connector import BaseConnector


class QRadarConnector(BaseConnector):

    def test_connection(self):
        print("QRadar connector initialized")

    def get_findings(self):
        return []