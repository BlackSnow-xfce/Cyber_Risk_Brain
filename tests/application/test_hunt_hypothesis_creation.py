import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from application.hunt_hypotheses import (
    FileHuntHypothesisRepository,
    HuntHypothesisConflictError,
    HuntHypothesisDataError,
    HuntHypothesisPersistenceError,
)
from application.hunt_hypothesis_creation import (
    HuntHypothesisCreationInput,
    HuntHypothesisCreationService,
    HuntHypothesisCreationValidationError,
)
from application.local_operator import (
    AuthenticatedPrincipal,
    HUNT_HYPOTHESIS_CREATE_PERMISSION,
    HuntHypothesisWriteAuthority,
    LocalOperatorAuthorizationError,
)
from core.threat_hunting import (
    HUNT_HYPOTHESIS_CONTRACT_VERSION,
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)


NOW = datetime(2026, 8, 24, 14, 0, tzinfo=timezone.utc)
UUID_ONE = UUID("12345678-1234-4234-9234-123456789abc")


def test_creation_service_assigns_all_authoritative_metadata() -> None:
    repository = RecordingRepository()
    service = HuntHypothesisCreationService(
        repository,
        id_generator=lambda: UUID_ONE,
        clock=lambda: NOW,
        authority=HuntHypothesisWriteAuthority(clock=lambda: NOW),
    )

    result = service.create(_creation_input(), _principal())

    assert result.hypothesis.hypothesis_id == f"hypothesis-{UUID_ONE}"
    assert result.hypothesis.created_by == "product-owner"
    assert result.hypothesis.created_at == NOW
    assert result.hypothesis.status is HuntHypothesisStatus.DRAFT
    assert result.hypothesis.contract_version == HUNT_HYPOTHESIS_CONTRACT_VERSION
    assert result.authorization.principal_id == "product-owner"
    assert result.authorization.operation == HUNT_HYPOTHESIS_CREATE_PERMISSION
    assert result.authorization.outcome == "allowed"
    assert repository.created == result.hypothesis


def test_creation_requires_exact_server_side_authority() -> None:
    principal = AuthenticatedPrincipal(
        principal_id="product-owner",
        display_name="Product Owner",
        principal_type="human/operator",
        permissions=frozenset(),
    )
    with pytest.raises(LocalOperatorAuthorizationError):
        HuntHypothesisCreationService(RecordingRepository()).create(
            _creation_input(), principal
        )


def test_malformed_creation_input_fails_before_persistence() -> None:
    repository = RecordingRepository()
    service = HuntHypothesisCreationService(
        repository, id_generator=lambda: UUID_ONE, clock=lambda: NOW
    )
    invalid = HuntHypothesisCreationInput(
        title=" ",
        statement="statement",
        rationale="rationale",
        target_references=(),
        threat_references=(),
    )

    with pytest.raises(HuntHypothesisCreationValidationError):
        service.create(invalid, _principal())
    assert repository.created is None


def test_repository_appends_canonical_hypothesis_and_preserves_existing(tmp_path) -> None:
    path = _repository_file(tmp_path, [_existing_hypothesis()])
    repository = FileHuntHypothesisRepository(str(path))
    created = _new_hypothesis(UUID_ONE)

    assert repository.create(created) == created
    assert repository.list() == (_existing_hypothesis(), created)


def test_repository_duplicate_identity_is_conflict_without_modification(tmp_path) -> None:
    existing = _existing_hypothesis()
    path = _repository_file(tmp_path, [existing])
    before = path.read_bytes()

    with pytest.raises(HuntHypothesisConflictError):
        FileHuntHypothesisRepository(str(path)).create(existing)
    assert path.read_bytes() == before


def test_malformed_repository_fails_closed_without_modification(tmp_path) -> None:
    path = tmp_path / "hypotheses.json"
    path.write_text('{"invalid": true}', encoding="utf-8")
    before = path.read_bytes()

    with pytest.raises(HuntHypothesisDataError):
        FileHuntHypothesisRepository(str(path)).create(_new_hypothesis(UUID_ONE))
    assert path.read_bytes() == before


def test_concurrent_creations_do_not_lose_records(tmp_path) -> None:
    path = _repository_file(tmp_path, [])
    repository = FileHuntHypothesisRepository(str(path))
    hypotheses = [
        _new_hypothesis(UUID(f"00000000-0000-4000-8000-{index:012d}"))
        for index in range(1, 7)
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        persisted = tuple(executor.map(repository.create, hypotheses))

    assert set(persisted) == set(hypotheses)
    assert set(repository.list()) == set(hypotheses)


def test_replace_failure_preserves_original_and_releases_lock(tmp_path, monkeypatch) -> None:
    path = _repository_file(tmp_path, [_existing_hypothesis()])
    before = path.read_bytes()
    repository = FileHuntHypothesisRepository(str(path))

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("application.hunt_hypotheses.os.replace", fail_replace)
    with pytest.raises(HuntHypothesisPersistenceError):
        repository.create(_new_hypothesis(UUID_ONE))
    assert path.read_bytes() == before

    monkeypatch.undo()
    assert repository.create(_new_hypothesis(UUID_ONE)).hypothesis_id.endswith(
        str(UUID_ONE)
    )


def test_temporary_file_failure_preserves_original_and_releases_lock(
    tmp_path, monkeypatch
) -> None:
    path = _repository_file(tmp_path, [_existing_hypothesis()])
    before = path.read_bytes()
    repository = FileHuntHypothesisRepository(str(path))

    def fail_temporary_file(*args, **kwargs):
        raise OSError("simulated temporary-file failure")

    monkeypatch.setattr(
        "application.hunt_hypotheses.tempfile.NamedTemporaryFile",
        fail_temporary_file,
    )
    with pytest.raises(HuntHypothesisPersistenceError):
        repository.create(_new_hypothesis(UUID_ONE))
    assert path.read_bytes() == before

    monkeypatch.undo()
    assert repository.create(_new_hypothesis(UUID_ONE)) == _new_hypothesis(UUID_ONE)


class RecordingRepository:
    def __init__(self) -> None:
        self.created = None

    def list(self):
        return ()

    def create(self, hypothesis):
        self.created = hypothesis
        return hypothesis


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        principal_id="product-owner",
        display_name="Product Owner",
        principal_type="human/operator",
        permissions=frozenset({HUNT_HYPOTHESIS_CREATE_PERMISSION}),
    )


def _creation_input() -> HuntHypothesisCreationInput:
    return HuntHypothesisCreationInput(
        title="Investigate exposed service activity",
        statement="An exposed service may warrant investigation.",
        rationale="The hypothesis requires human-led validation.",
        target_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, "asset-1"),
        ),
        threat_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.CVE, "CVE-2004-2687"),
        ),
    )


def _new_hypothesis(identifier: UUID) -> HuntHypothesis:
    request = _creation_input()
    return HuntHypothesis(
        hypothesis_id=f"hypothesis-{identifier}",
        title=request.title,
        statement=request.statement,
        rationale=request.rationale,
        target_references=request.target_references,
        threat_references=request.threat_references,
        created_by="product-owner",
        created_at=NOW,
        status=HuntHypothesisStatus.DRAFT,
    )


def _existing_hypothesis() -> HuntHypothesis:
    return HuntHypothesis(
        hypothesis_id="hypothesis-existing",
        title="Existing hypothesis",
        statement="An existing investigative assumption.",
        rationale="Preserve this canonical record.",
        target_references=(),
        threat_references=(),
        created_by="product-owner",
        created_at=NOW,
        status=HuntHypothesisStatus.DRAFT,
    )


def _repository_file(tmp_path: Path, hypotheses: list[HuntHypothesis]) -> Path:
    path = tmp_path / "hypotheses.json"
    path.write_text(
        json.dumps(
            {
                "contract_version": HUNT_HYPOTHESIS_CONTRACT_VERSION,
                "hypotheses": [item.to_dict() for item in hypotheses],
            }
        ),
        encoding="utf-8",
    )
    return path
