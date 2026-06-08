from connectors.base_connector import BaseConnector


class QualysConnector(BaseConnector):

    def test_connection(self):
        print("Qualys connector initialized")

    def get_findings(self):
        return []