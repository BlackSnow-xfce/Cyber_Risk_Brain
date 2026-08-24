import json

import pytest

from application import (
    FileHuntHypothesisRepository,
    HuntHypothesisConfigurationError,
    HuntHypothesisDataError,
    HuntHypothesisQueryService,
)
from core.threat_hunting import HuntHypothesisStatus


def test_repository_loads_canonical_hypotheses(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(json.dumps(_document([_record()])), encoding="utf-8")

    hypotheses = HuntHypothesisQueryService(
        FileHuntHypothesisRepository(str(path))
    ).list()

    assert len(hypotheses) == 1
    assert hypotheses[0].hypothesis_id == "hypothesis-001"
    assert hypotheses[0].status is HuntHypothesisStatus.ACTIVE
    assert hypotheses[0].target_references[0].reference_type.value == "asset"
    assert hypotheses[0].threat_references[0].reference_type.value == "technique"


def test_repository_returns_empty_canonical_collection(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(json.dumps(_document([])), encoding="utf-8")

    assert FileHuntHypothesisRepository(str(path)).list() == ()


def test_repository_fails_when_unconfigured() -> None:
    with pytest.raises(HuntHypothesisConfigurationError):
        FileHuntHypothesisRepository(None).list()


@pytest.mark.parametrize(
    "change",
    [
        lambda record: record.pop("title"),
        lambda record: record.update(status="invented"),
        lambda record: record.update(created_at="2026-08-24T10:00:00"),
        lambda record: record.update(
            target_references=[
                {"reference_type": "technique", "reference_id": "T1059"}
            ]
        ),
    ],
)
def test_repository_rejects_malformed_canonical_records(tmp_path, change) -> None:
    record = _record()
    change(record)
    path = tmp_path / "hypotheses.json"
    path.write_text(json.dumps(_document([record])), encoding="utf-8")

    with pytest.raises(HuntHypothesisDataError):
        FileHuntHypothesisRepository(str(path)).list()


def test_repository_rejects_duplicate_hypothesis_ids(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(_document([_record(), _record()])), encoding="utf-8"
    )

    with pytest.raises(HuntHypothesisDataError, match="duplicate"):
        FileHuntHypothesisRepository(str(path)).list()


def _document(records: list[dict]) -> dict:
    return {"contract_version": "1.0", "hypotheses": records}


def _record() -> dict:
    return {
        "hypothesis_id": "hypothesis-001",
        "title": "Administrative execution from an exposed service",
        "statement": "A service account may be executing unexpected commands.",
        "status": "active",
        "created_at": "2026-08-24T10:00:00+00:00",
        "created_by": "threat-hunter-001",
        "target_references": [
            {"reference_type": "asset", "reference_id": "asset-001"}
        ],
        "threat_references": [
            {"reference_type": "technique", "reference_id": "T1059"}
        ],
        "rationale": "Unexpected command execution warrants investigation.",
        "contract_version": "1.0",
    }
