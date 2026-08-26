import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from application import (
    FileHuntHypothesisRepository,
    HuntHypothesisConfigurationError,
    HuntHypothesisDataError,
    HuntHypothesisQueryService,
    HuntHypothesisRepositoryNotFoundError,
    HuntHypothesisStateConflictError,
    HuntHypothesisPersistenceError,
)
from core.threat_hunting import HuntHypothesisStatus
from application.hunt_hypothesis_activation import HuntHypothesisActivationAuditError
from application.hunt_hypotheses import (
    HuntHypothesisActivationRecoveryRequiredError,
    _RepositoryLock,
)


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


def test_repository_atomically_activates_only_expected_draft(tmp_path) -> None:
    draft = _record() | {"status": "draft"}
    other = _record() | {"hypothesis_id": "hypothesis-002"}
    path = tmp_path / "hypotheses.json"
    path.write_text(json.dumps(_document([draft, other])), encoding="utf-8")
    repository = FileHuntHypothesisRepository(str(path))

    activated = repository.activate("hypothesis-001", HuntHypothesisStatus.DRAFT)

    assert activated.status is HuntHypothesisStatus.ACTIVE
    persisted = repository.list()
    assert [item.status for item in persisted] == [
        HuntHypothesisStatus.ACTIVE,
        HuntHypothesisStatus.ACTIVE,
    ]


def test_repository_rejects_missing_or_stale_activation_without_mutation(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record()]))
    path.write_text(source, encoding="utf-8")
    repository = FileHuntHypothesisRepository(str(path))

    with pytest.raises(HuntHypothesisRepositoryNotFoundError):
        repository.activate("missing", HuntHypothesisStatus.DRAFT)
    with pytest.raises(HuntHypothesisStateConflictError):
        repository.activate("hypothesis-001", HuntHypothesisStatus.DRAFT)

    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)


def test_activation_write_failure_preserves_source_and_releases_lock(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record() | {"status": "draft"}]))
    path.write_text(source, encoding="utf-8")
    repository = FileHuntHypothesisRepository(str(path))
    original_write = repository._atomic_write

    def fail_write(*args) -> None:
        raise HuntHypothesisPersistenceError("write failed")

    monkeypatch.setattr(repository, "_atomic_write", fail_write)
    with pytest.raises(HuntHypothesisPersistenceError):
        repository.activate("hypothesis-001", HuntHypothesisStatus.DRAFT)
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)

    monkeypatch.setattr(repository, "_atomic_write", original_write)
    assert repository.activate(
        "hypothesis-001", HuntHypothesisStatus.DRAFT
    ).status is HuntHypothesisStatus.ACTIVE


def test_concurrent_activation_has_one_winner_and_one_stale_contender(tmp_path) -> None:
    draft = _record() | {"status": "draft"}
    other = _record() | {"hypothesis_id": "hypothesis-002"}
    path = tmp_path / "hypotheses.json"
    path.write_text(json.dumps(_document([draft, other])), encoding="utf-8")

    def activate() -> str:
        try:
            FileHuntHypothesisRepository(str(path)).activate(
                "hypothesis-001", HuntHypothesisStatus.DRAFT
            )
            return "activated"
        except HuntHypothesisStateConflictError as error:
            assert error.actual_status is HuntHypothesisStatus.ACTIVE
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(lambda _: activate(), range(2)))

    assert outcomes == ["activated", "stale"]
    persisted = FileHuntHypothesisRepository(str(path)).list()
    assert [item.hypothesis_id for item in persisted] == [
        "hypothesis-001",
        "hypothesis-002",
    ]
    assert persisted[0].status is HuntHypothesisStatus.ACTIVE


def test_concurrent_create_and_activate_preserve_both_records(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(_document([_record() | {"status": "draft"}])),
        encoding="utf-8",
    )
    source = FileHuntHypothesisRepository(str(path)).list()[0]
    created = replace(source, hypothesis_id="hypothesis-002")

    with ThreadPoolExecutor(max_workers=2) as executor:
        activation = executor.submit(
            FileHuntHypothesisRepository(str(path)).activate,
            "hypothesis-001",
            HuntHypothesisStatus.DRAFT,
        )
        creation = executor.submit(
            FileHuntHypothesisRepository(str(path)).create,
            created,
        )
        assert activation.result().status is HuntHypothesisStatus.ACTIVE
        assert creation.result() == created

    persisted = FileHuntHypothesisRepository(str(path)).list()
    assert {item.hypothesis_id for item in persisted} == {
        "hypothesis-001",
        "hypothesis-002",
    }


def test_activation_lock_failure_preserves_source(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record() | {"status": "draft"}]))
    path.write_text(source, encoding="utf-8")
    lock_path = path.with_name(f"{path.name}.lock")

    with _RepositoryLock(lock_path, 0.1):
        with pytest.raises(HuntHypothesisPersistenceError, match="lock"):
            FileHuntHypothesisRepository(
                str(path), lock_timeout_seconds=0.01
            ).activate("hypothesis-001", HuntHypothesisStatus.DRAFT)

    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)


def test_activation_temporary_file_failure_preserves_source_and_lock(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record() | {"status": "draft"}]))
    path.write_text(source, encoding="utf-8")

    def fail_temporary_file(*args, **kwargs):
        raise OSError("simulated temporary-file failure")

    monkeypatch.setattr(
        "application.hunt_hypotheses.tempfile.NamedTemporaryFile",
        fail_temporary_file,
    )
    with pytest.raises(HuntHypothesisPersistenceError):
        FileHuntHypothesisRepository(str(path)).activate(
            "hypothesis-001", HuntHypothesisStatus.DRAFT
        )
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)


def test_activation_replace_failure_preserves_source_and_lock(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record() | {"status": "draft"}]))
    path.write_text(source, encoding="utf-8")

    def fail_replace(source_path, destination_path):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("application.hunt_hypotheses.os.replace", fail_replace)
    with pytest.raises(HuntHypothesisPersistenceError):
        FileHuntHypothesisRepository(str(path)).activate(
            "hypothesis-001", HuntHypothesisStatus.DRAFT
        )
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)


def test_post_replace_verification_failure_rolls_back(tmp_path, monkeypatch) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record() | {"status": "draft"}]))
    path.write_text(source, encoding="utf-8")
    repository = FileHuntHypothesisRepository(str(path))
    original_list = repository.list
    calls = 0

    def fail_verification():
        nonlocal calls
        calls += 1
        if calls == 2:
            return ()
        return original_list()

    monkeypatch.setattr(repository, "list", fail_verification)
    with pytest.raises(HuntHypothesisPersistenceError, match="verification"):
        repository.activate("hypothesis-001", HuntHypothesisStatus.DRAFT)
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)


def test_terminal_audit_failure_rolls_back_under_repository_lock(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    source = json.dumps(_document([_record() | {"status": "draft"}]))
    path.write_text(source, encoding="utf-8")

    def fail_terminal(_hypothesis) -> None:
        raise HuntHypothesisActivationAuditError("terminal audit failed")

    with pytest.raises(HuntHypothesisPersistenceError, match="rollback was verified"):
        FileHuntHypothesisRepository(str(path)).activate(
            "hypothesis-001",
            HuntHypothesisStatus.DRAFT,
            fail_terminal,
        )
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(source)


def test_terminal_failure_rollback_write_failure_requires_reconciliation(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(_document([_record() | {"status": "draft"}])), encoding="utf-8"
    )
    repository = FileHuntHypothesisRepository(str(path))
    atomic_write = repository._atomic_write
    calls = 0

    def fail_rollback_write(target, document) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise HuntHypothesisPersistenceError("rollback write failed")
        atomic_write(target, document)

    monkeypatch.setattr(repository, "_atomic_write", fail_rollback_write)
    with pytest.raises(HuntHypothesisActivationRecoveryRequiredError):
        repository.activate(
            "hypothesis-001",
            HuntHypothesisStatus.DRAFT,
            _failing_terminal_audit,
        )


def test_terminal_failure_rollback_reread_failure_requires_reconciliation(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(_document([_record() | {"status": "draft"}])), encoding="utf-8"
    )
    repository = FileHuntHypothesisRepository(str(path))
    repository_list = repository.list
    calls = 0

    def fail_rollback_reread():
        nonlocal calls
        calls += 1
        if calls == 3:
            raise HuntHypothesisDataError("rollback reread failed")
        return repository_list()

    monkeypatch.setattr(repository, "list", fail_rollback_reread)
    with pytest.raises(HuntHypothesisActivationRecoveryRequiredError):
        repository.activate(
            "hypothesis-001",
            HuntHypothesisStatus.DRAFT,
            _failing_terminal_audit,
        )


def test_terminal_failure_rollback_comparison_failure_requires_reconciliation(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(_document([_record() | {"status": "draft"}])), encoding="utf-8"
    )
    repository = FileHuntHypothesisRepository(str(path))
    repository_list = repository.list
    calls = 0

    def mismatch_after_rollback():
        nonlocal calls
        calls += 1
        if calls == 3:
            return ()
        return repository_list()

    monkeypatch.setattr(repository, "list", mismatch_after_rollback)
    with pytest.raises(HuntHypothesisActivationRecoveryRequiredError):
        repository.activate(
            "hypothesis-001",
            HuntHypothesisStatus.DRAFT,
            _failing_terminal_audit,
        )


def test_activation_rejects_malformed_and_duplicate_repository(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    for document in (
        {"contract_version": "1.0", "hypotheses": [{"invalid": True}]},
        _document([_record(), _record()]),
    ):
        path.write_text(json.dumps(document), encoding="utf-8")
        source = path.read_text(encoding="utf-8")
        with pytest.raises(HuntHypothesisDataError):
            FileHuntHypothesisRepository(str(path)).activate(
                "hypothesis-001", HuntHypothesisStatus.DRAFT
            )
        assert path.read_text(encoding="utf-8") == source


def test_active_status_survives_fresh_repository_instance(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(_document([_record() | {"status": "draft"}])),
        encoding="utf-8",
    )
    FileHuntHypothesisRepository(str(path)).activate(
        "hypothesis-001", HuntHypothesisStatus.DRAFT
    )
    assert FileHuntHypothesisRepository(str(path)).list()[0].status is (
        HuntHypothesisStatus.ACTIVE
    )


def _failing_terminal_audit(_hypothesis) -> None:
    raise HuntHypothesisActivationAuditError("terminal audit failed")


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
