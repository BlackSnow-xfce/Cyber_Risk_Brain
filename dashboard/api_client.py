from __future__ import annotations

import requests


class DashboardApiClient:
    """
    Client for the PredatorAI REST API.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
    ) -> None:

        self.base_url = base_url

    def decision_console(
        self,
    ) -> dict:

        response = requests.get(

            f"{self.base_url}/api/decision-console"

        )

        response.raise_for_status()

        return response.json()
    