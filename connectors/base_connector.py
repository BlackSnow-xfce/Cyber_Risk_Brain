class BaseConnector:

    def get_findings(self):
        raise NotImplementedError()

    def test_connection(self):
        raise NotImplementedError()