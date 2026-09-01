from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DetectionCoverageObservation:
    sensor_applicable: bool | None
    sensor_healthy: bool | None
    telemetry_current: bool | None
    analytic_id: str | None
    analytic_version: str | None
    analytic_applicable: bool | None
    rule_enabled: bool | None
    alert_path_operational: bool | None
    evaluation_complete: bool

    @property
    def missing_requirements(self) -> tuple[str, ...]:
        required = (("sensor_applicable", self.sensor_applicable), ("sensor_healthy", self.sensor_healthy), ("telemetry_current", self.telemetry_current), ("analytic_applicable", self.analytic_applicable), ("rule_enabled", self.rule_enabled), ("alert_path_operational", self.alert_path_operational))
        missing = [name for name, value in required if value is None]
        if not self.analytic_id: missing.append("analytic_id")
        if not self.analytic_version: missing.append("analytic_version")
        return tuple(missing)

    @property
    def authoritative_value(self) -> bool | None:
        if not self.evaluation_complete or self.missing_requirements:
            return None
        return all((self.sensor_applicable, self.sensor_healthy, self.telemetry_current, self.analytic_applicable, self.rule_enabled, self.alert_path_operational))
