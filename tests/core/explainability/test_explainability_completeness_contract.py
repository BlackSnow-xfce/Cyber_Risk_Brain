from dataclasses import FrozenInstanceError, fields

import pytest

from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)


def test_completeness_status_contains_exactly_the_accepted_states() -> None:
    assert tuple(CompletenessStatus) == (
        CompletenessStatus.AVAILABLE,
        CompletenessStatus.NO_DATA,
        CompletenessStatus.SOURCE_UNAVAILABLE,
        CompletenessStatus.NOT_PART_OF_EXECUTION,
        CompletenessStatus.UNKNOWN,
    )


def test_explanation_completeness_is_frozen_and_minimal() -> None:
    completeness = ExplanationCompleteness(
        status=CompletenessStatus.UNKNOWN,
        provenance=ExplanationProvenance(
            source_type="decision_result",
            source_reference="evidence",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        completeness.status = CompletenessStatus.AVAILABLE

    assert tuple(field.name for field in fields(completeness)) == (
        "status",
        "provenance",
    )


def test_explanation_completeness_reuses_existing_provenance() -> None:
    provenance = ExplanationProvenance(
        source_type="decision_result",
        source_reference="recommendations",
    )
    completeness = ExplanationCompleteness(
        status=CompletenessStatus.NO_DATA,
        provenance=provenance,
    )

    assert completeness.provenance is provenance
