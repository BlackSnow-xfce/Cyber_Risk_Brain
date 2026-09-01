from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class MitreMapping:
    technique_id: str
    tactic: str
    mapping_version: str
    governed: bool
    binding_key: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"T\d{4}(?:\.\d{3})?", self.technique_id):
            raise ValueError("MITRE technique ID is not canonical.")
        if not self.tactic.strip() or not self.mapping_version.strip() or not self.binding_key.strip():
            raise ValueError("MITRE mapping fields are required.")
        if not self.governed:
            raise ValueError("Only governed MITRE mappings are authoritative.")
