def test_canonical_core_contracts_are_importable() -> None:
    from core.decision.models import DecisionResult
    from core.explainability import DecisionTrace, DecisionTraceBuilder

    assert DecisionResult is not None
    assert DecisionTrace is not None
    assert DecisionTraceBuilder is not None
