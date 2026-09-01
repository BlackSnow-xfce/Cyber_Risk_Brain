from core.context_supply import DetectionCoverageObservation


def test_detection_requires_complete_effective_chain() -> None:
    complete = DetectionCoverageObservation(True, True, True, "rule-1", "1", True, True, True, True)
    assert complete.authoritative_value is True
    assert DetectionCoverageObservation(True, True, True, "rule-1", "1", True, False, True, True).authoritative_value is False
    assert DetectionCoverageObservation(True, None, True, "rule-1", "1", True, True, True, False).authoritative_value is None
