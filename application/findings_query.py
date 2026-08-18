from __future__ import annotations

from pathlib import Path

from core.models import UniversalFinding
from ingestion import load_greenbone_xml_findings


class FindingsConfigurationError(ValueError):
    """Raised when the live findings source is not configured."""


class FindingsQueryService:
    """Read canonical findings from the configured scanner export."""

    def __init__(self, report_path: str | None) -> None:
        self._report_path = report_path

    def get_findings(self) -> list[UniversalFinding]:
        if self._report_path is None or not self._report_path.strip():
            raise FindingsConfigurationError(
                "GREENBONE_REPORT_PATH is not configured."
            )

        return load_greenbone_xml_findings(
            Path(self._report_path)
        )
