from settings import (
    WIZ_ENABLED,
    JIRA_ENABLED,
    DEFENDER_ENABLED,
    QRADAR_ENABLED,
    CROWDSTRIKE_ENABLED,
    TENABLE_ENABLED,
    QUALYS_ENABLED,
    RAPID7_ENABLED
)

from connectors.wiz_connector import WizConnector
from connectors.jira_connector import JiraConnector
from connectors.defender_connector import DefenderConnector
from connectors.qradar_connector import QRadarConnector
from connectors.crowdstrike_connector import CrowdStrikeConnector
from connectors.tenable_connector import TenableConnector
from connectors.qualys_connector import QualysConnector
from connectors.rapid7_connector import Rapid7Connector


class ConnectorManager:

    def __init__(self):

        self.connectors = []

    def load_connectors(self):

        if WIZ_ENABLED == "true":
            self.connectors.append(
                WizConnector()
            )

        if DEFENDER_ENABLED == "true":
            self.connectors.append(
                DefenderConnector()
            )

        if QRADAR_ENABLED == "true":
            self.connectors.append(
                QRadarConnector()
            )

        if CROWDSTRIKE_ENABLED == "true":
            self.connectors.append(
                CrowdStrikeConnector()
            )

        if TENABLE_ENABLED == "true":
            self.connectors.append(
                TenableConnector()
            )

        if QUALYS_ENABLED == "true":
            self.connectors.append(
                QualysConnector()
            )

        if RAPID7_ENABLED == "true":
            self.connectors.append(
                Rapid7Connector()
            )

        if JIRA_ENABLED == "true":
            self.connectors.append(
                JiraConnector()
            )

        return self.connectors

    def show_enabled_connectors(self):

        print("Enabled Connectors:")

        for connector in self.connectors:

            print(
                "-",
                connector.__class__.__name__
            )