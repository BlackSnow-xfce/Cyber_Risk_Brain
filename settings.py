from dotenv import load_dotenv
import os

load_dotenv()

APP_ENV = os.getenv("APP_ENV")
DEBUG = os.getenv("DEBUG")

WIZ_ENABLED = os.getenv("WIZ_ENABLED")
WIZ_API_URL = os.getenv("WIZ_API_URL")
WIZ_API_TOKEN = os.getenv("WIZ_API_TOKEN")

JIRA_ENABLED = os.getenv("JIRA_ENABLED")
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

REDIS_ENABLED = os.getenv("REDIS_ENABLED")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

NEO4J_ENABLED = os.getenv("NEO4J_ENABLED")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

DEFENDER_ENABLED = os.getenv("DEFENDER_ENABLED")
QRADAR_ENABLED = os.getenv("QRADAR_ENABLED")
CROWDSTRIKE_ENABLED = os.getenv("CROWDSTRIKE_ENABLED")
TENABLE_ENABLED = os.getenv("TENABLE_ENABLED")
QUALYS_ENABLED = os.getenv("QUALYS_ENABLED")
RAPID7_ENABLED = os.getenv("RAPID7_ENABLED")

