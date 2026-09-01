from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from core.context_supply import ContextObservation, ContextScope, ContextSubject, ContextType, DetectionCoverageObservation, ExposureObservation, ExposureReachability, MitreMapping, ObservationProvenance


class FileContextObservationRepository:
    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def add(self, observation: ContextObservation) -> ContextObservation:
        target_id = observation.revokes_observation_id or observation.supersedes_observation_id
        if target_id is not None:
            target = self.get(target_id)
            if target is None:
                raise ValueError("Supersession or revocation target does not exist.")
            if (target.organization_id, target.subject, target.scope, target.context_type) != (observation.organization_id, observation.subject, observation.scope, observation.context_type):
                raise ValueError("Supersession or revocation crosses context scope.")
            if observation.revokes_observation_id and any(item.revokes_observation_id == target_id for item in self.list(organization_id=observation.organization_id)):
                raise ValueError("Observation revocation was already recorded.")
        path = self._path(observation.observation_id)
        encoded = self._encode(observation)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            existing = self.get(observation.observation_id)
            if existing == observation:
                return existing
            raise ValueError("Observation identity already exists with changed content.") from None
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        persisted = self.get(observation.observation_id)
        if persisted != observation:
            raise ValueError("Observation read-back verification failed.")
        return observation

    def get(self, observation_id: str) -> ContextObservation | None:
        path = self._path(observation_id)
        if not path.exists(): return None
        try:
            result = self._decode(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
            raise ValueError("Stored observation is invalid.") from error
        if result.observation_id != observation_id:
            raise ValueError("Stored observation identity mismatch.")
        return result

    def list(self, *, organization_id: str, context_type: ContextType | None = None, asset_id: str | None = None, finding_id: str | None = None) -> tuple[ContextObservation, ...]:
        observations = (self.get(path.stem) for path in sorted(self._directory.glob("*.json")))
        return tuple(item for item in observations if item is not None and item.organization_id == organization_id and (context_type is None or item.context_type is context_type) and (asset_id is None or item.subject.asset_id == asset_id) and (finding_id is None or item.subject.finding_id == finding_id))

    def _path(self, observation_id: str) -> Path:
        if not observation_id or any(character not in "0123456789abcdef" for character in observation_id) or len(observation_id) != 64:
            raise ValueError("Invalid observation ID.")
        return self._directory / f"{observation_id}.json"

    @staticmethod
    def _encode(observation: ContextObservation) -> str:
        data = asdict(observation)
        data["context_type"] = observation.context_type.value
        for name in ("observed_at", "ingested_at", "valid_until"): data[name] = getattr(observation, name).isoformat()
        payload = observation.payload
        data["payload_type"] = type(payload).__name__
        if isinstance(payload, ExposureObservation): data["payload"]["reachability"] = payload.reachability.value
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode(encoded: str) -> ContextObservation:
        from datetime import datetime
        data = json.loads(encoded)
        payload_type = data.pop("payload_type")
        payload_data = data.pop("payload")
        payload_factories = {
            "ExposureObservation": lambda: ExposureObservation(ExposureReachability(payload_data["reachability"]), payload_data["evaluation_complete"]),
            "DetectionCoverageObservation": lambda: DetectionCoverageObservation(**payload_data),
            "MitreMapping": lambda: MitreMapping(**payload_data),
        }
        if payload_type not in payload_factories: raise ValueError("Untyped observation payload.")
        context_type = ContextType(data.pop("context_type"))
        subject = ContextSubject(**data.pop("subject"))
        scope = ContextScope(**data.pop("scope"))
        provenance_data = data.pop("provenance")
        provenance = ObservationProvenance(
            source_reference=provenance_data["source_reference"],
            evidence_references=tuple(provenance_data["evidence_references"]),
        )
        observed_at = datetime.fromisoformat(data.pop("observed_at"))
        ingested_at = datetime.fromisoformat(data.pop("ingested_at"))
        valid_until = datetime.fromisoformat(data.pop("valid_until"))
        return ContextObservation(**data, context_type=context_type, subject=subject, scope=scope, provenance=provenance, payload=payload_factories[payload_type](), observed_at=observed_at, ingested_at=ingested_at, valid_until=valid_until)
