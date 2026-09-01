from core.context_supply import ExposureObservation, ExposureReachability


def test_only_explicit_external_or_negative_evaluations_project_boolean() -> None:
    assert ExposureObservation(ExposureReachability.DIRECT_EXTERNAL, True).authoritative_value is True
    assert ExposureObservation(ExposureReachability.AUTHENTICATED_EXTERNAL, True).authoritative_value is True
    assert ExposureObservation(ExposureReachability.NOT_EXTERNALLY_REACHABLE, True).authoritative_value is False
    assert ExposureObservation(ExposureReachability.INTERNAL, True).authoritative_value is None
