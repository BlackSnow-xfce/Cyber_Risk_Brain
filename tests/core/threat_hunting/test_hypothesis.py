from datetime import datetime, timezone

import pytest

from core.threat_hunting import (
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)


CREATED_AT = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def make_hypothesis(**overrides) -> HuntHypothesis:
    values = {
        "hypothesis_id": "hyp-distcc-001",
        "title": "DistCC may expose remote execution risk",
        "statement": "An exposed DistCC service could be used for remote command execution.",
        "status": HuntHypothesisStatus.DRAFT,
        "created_at": CREATED_AT,
        "created_by": "analyst:alice",
        "target_references": (),
        "threat_references": (),
        "rationale": "The service exposure warrants a controlled hunt.",
    }
    values.update(overrides)
    return HuntHypothesis(**values)


def test_valid_minimal_hypothesis_is_immutable() -> None:
    hypothesis = make_hypothesis()

    assert hypothesis.status is HuntHypothesisStatus.DRAFT
    with pytest.raises((AttributeError, TypeError)):
        hypothesis.status = HuntHypothesisStatus.ACTIVE  # type: ignore[misc]


def test_target_and_threat_references_are_typed() -> None:
    hypothesis = make_hypothesis(
        target_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, "asset-1"),
            HuntHypothesisReference(HuntHypothesisReferenceType.SERVICE, "distccd:3632"),
        ),
        threat_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.CVE, "CVE-2004-2687"),
        ),
    )

    assert hypothesis.target_references[0].reference_id == "asset-1"
    assert hypothesis.threat_references[0].reference_type is HuntHypothesisReferenceType.CVE


@pytest.mark.parametrize("field", ["hypothesis_id", "title", "statement", "created_by", "rationale"])
def test_required_text_fields_reject_empty_values(field: str) -> None:
    with pytest.raises(ValueError):
        make_hypothesis(**{field: "  "})


def test_invalid_status_and_naive_timestamp_are_rejected() -> None:
    with pytest.raises(ValueError):
        make_hypothesis(status="draft")
    with pytest.raises(ValueError):
        make_hypothesis(created_at=datetime(2026, 8, 21, 12, 0))


def test_invalid_or_duplicate_references_are_rejected() -> None:
    reference = HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, "asset-1")
    with pytest.raises(ValueError):
        make_hypothesis(target_references=(reference, reference))
    with pytest.raises(ValueError):
        make_hypothesis(
            target_references=(
                HuntHypothesisReference(HuntHypothesisReferenceType.CVE, "CVE-1"),
            ),
        )
    with pytest.raises(ValueError):
        HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, " ")


def test_statement_is_structurally_accepted_without_natural_language_interpretation() -> None:
    hypothesis = make_hypothesis(statement="RCE confirmed on the target.")

    assert hypothesis.statement == "RCE confirmed on the target."


def test_status_is_not_automatically_promoted() -> None:
    hypothesis = make_hypothesis(status=HuntHypothesisStatus.ACTIVE)
    assert hypothesis.status is HuntHypothesisStatus.ACTIVE


def test_serialization_is_stable_and_typed() -> None:
    hypothesis = make_hypothesis(
        target_references=(
            HuntHypothesisReference(HuntHypothesisReferenceType.ASSET, "asset-1"),
        ),
    )

    assert hypothesis.to_dict() == {
        "hypothesis_id": "hyp-distcc-001",
        "title": "DistCC may expose remote execution risk",
        "statement": "An exposed DistCC service could be used for remote command execution.",
        "status": "draft",
        "created_at": "2026-08-21T12:00:00+00:00",
        "created_by": "analyst:alice",
        "target_references": [
            {"reference_type": "asset", "reference_id": "asset-1"},
        ],
        "threat_references": [],
        "rationale": "The service exposure warrants a controlled hunt.",
        "contract_version": "1.0",
    }
