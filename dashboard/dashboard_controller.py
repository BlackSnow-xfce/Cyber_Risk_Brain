from __future__ import annotations

from dashboard.api_client import DashboardApiClient
from dashboard.viewmodels.decision_console_builder import (
    DecisionConsoleBuilder,
)


class DashboardController:
    """
    Supplies the dashboard with data.

    The UI never talks directly to
    the Decision Engine.
    """

    def __init__(self) -> None:

        self.client = DashboardApiClient()

        self.builder = (
            DecisionConsoleBuilder()
        )

    def load(self):

        data = self.client.decision_console()

        return data
    