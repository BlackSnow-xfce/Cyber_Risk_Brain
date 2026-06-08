from connectors.base_connector import BaseConnector


class JiraConnector(BaseConnector):

    def test_connection(self):
        print("Jira connector initialized")

    def get_findings(self):
        return []