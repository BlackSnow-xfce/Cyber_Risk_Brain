import requests
from models_db import Finding
from settings import WIZ_API_URL, WIZ_API_TOKEN


class WizClient:

    def __init__(self):
        self.url = WIZ_API_URL
        self.token = WIZ_API_TOKEN

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def test_connection(self):
        print("Wiz client initialized")
        print("URL:", self.url)

    def test_api(self):

        query = {
            "query": """
            query {
                issues(first: 1) {
                    nodes {
                        id
                        severity
                    }
                }
            }
            """
        }

        try:

            response = requests.post(
                self.url,
                headers=self.get_headers(),
                json=query
            )

            print("Status Code:", response.status_code)

            if response.status_code == 200:
                print(response.json())

            elif response.status_code == 401:
                print("Authentication failed")
            elif response.status_code == 200:

                data = response.json()

                findings = []

                issues = data["data"]["issues"]["nodes"]

                for issue in issues:

                    finding = Finding(
                        issue["id"],
                        issue["severity"]
                    )

                    findings.append(finding)

                for finding in findings:
                    print(finding.to_dict())

            else:
                print(response.text)

        except Exception as error:
            print("Request failed:", error)
