from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Mapping

from core.context_supply import ContextObservation, ContextScope, ContextSubject, ContextType, DetectionCoverageObservation, ExposureObservation, ExposureReachability, MitreMapping, ObservationProvenance, SourceAuthority, require_authority


class StructuredContextImportReader:
    def __init__(self, authorities: Mapping[str, SourceAuthority], organization_id: str) -> None:
        self._authorities = authorities
        self._organization_id = organization_id

    def read(self, path: str | Path) -> tuple[ContextObservation, ...]:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(document, list): raise ValueError("Context import must be a list of typed observations.")
        return tuple(self.parse(item) for item in document)

    def parse(self, item: object) -> ContextObservation:
        if not isinstance(item, dict): raise ValueError("Observation must be an object.")
        data = dict(item)
        payload_type = data.pop("payload_type", None)
        payload_data = data.pop("payload", None)
        if not isinstance(payload_data, dict): raise ValueError("Typed payload is required.")
        if not isinstance(data.get("digest"), str) or not data["digest"]:
            raise ValueError("Imported observation digest is required.")
        factories = {
            "EXPOSURE": lambda: ExposureObservation(ExposureReachability(payload_data["reachability"]), payload_data["evaluation_complete"]),
            "DETECTION_COVERAGE": lambda: DetectionCoverageObservation(**payload_data),
            "MITRE_MAPPING": lambda: MitreMapping(**payload_data),
        }
        if payload_type not in factories: raise ValueError("Unknown typed context payload.")
        try:
            observation = ContextObservation(
                observation_id=data["observation_id"], organization_id=data["organization_id"], context_type=ContextType(payload_type),
                subject=ContextSubject(**data["subject"]), scope=ContextScope(**data["scope"]), source_id=data["source_id"], authority_reference=data["authority_reference"],
                provenance=ObservationProvenance(**data["provenance"]), observed_at=datetime.fromisoformat(data["observed_at"]), ingested_at=datetime.fromisoformat(data["ingested_at"]), valid_until=datetime.fromisoformat(data["valid_until"]),
                schema_version=data["schema_version"], payload=factories[payload_type](), digest=data.get("digest", ""), supersedes_observation_id=data.get("supersedes_observation_id"), revokes_observation_id=data.get("revokes_observation_id"),
            )
        except (KeyError, TypeError, ValueError) as error: raise ValueError("Invalid context observation.") from error
        if observation.organization_id != self._organization_id: raise ValueError("Observation organization mismatch.")
        authority = self._authorities.get(observation.source_id)
        if authority is None: raise ValueError("Unknown context source.")
        require_authority(observation, authority)
        return observation
