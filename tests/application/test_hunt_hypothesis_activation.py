import json
from datetime import datetime, timezone

import pytest

from application.hunt_hypothesis_activation import (
    FileHuntHypothesisActivationAuditSink,
    HuntHypothesisActivationAuditError,
    HuntHypothesisActivationAttemptAuditor,
    HuntHypothesisActivationInput,
    HuntHypothesisActivationService,
    HuntHypothesisActivationValidationError,
)
from application.hunt_hypotheses import HuntHypothesisStateConflictError
from application.local_operator import (
    AuthenticatedPrincipal,
    HUNT_HYPOTHESIS_ACTIVATE_PERMISSION,
    LocalOperatorAuthorizationError,
)
from core.threat_hunting import HuntHypothesis, HuntHypothesisStatus


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


def test_authorized_draft_activation_is_persisted_and_safely_audited(tmp_path) -> None:
    repository = Repository(_hypothesis(HuntHypothesisStatus.DRAFT))
    audit_path = tmp_path / "audit.jsonl"
    service = HuntHypothesisActivationService(
        repository,
        FileHuntHypothesisActivationAuditSink(str(audit_path)),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "attempt-001",
    )

    result = service.activate(_request(), _principal())

    assert result.hypothesis.status is HuntHypothesisStatus.ACTIVE
    assert repository.calls == [("hypothesis-001", HuntHypothesisStatus.DRAFT)]
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert events[0] == {
        "authorization_outcome": "allowed",
        "attempt_id": "attempt-001",
        "commit_state": "pending",
        "current_status": None,
        "expected_status": "draft",
        "hypothesis_id": "hypothesis-001",
        "mutation_state": "not_started",
        "operation": "hunt_hypothesis:activate",
        "outcome": "authorized",
        "phase": "attempt",
        "principal_id": "operator-1",
        "reason": "authorized_attempt",
        "resulting_status": None,
        "timestamp": NOW.isoformat(),
    }
    assert events[1] == {
        **events[0],
        "commit_state": "committed",
        "current_status": "draft",
        "mutation_state": "persisted",
        "outcome": "activated",
        "phase": "terminal",
        "reason": "draft_activated_for_investigation",
        "resulting_status": "active",
    }
    assert "token" not in audit_path.read_text(encoding="utf-8").lower()


def test_denied_and_stale_attempts_are_audited_without_activation(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    repository = Repository(_hypothesis(HuntHypothesisStatus.DRAFT))
    service = HuntHypothesisActivationService(
        repository,
        FileHuntHypothesisActivationAuditSink(str(audit_path)),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "attempt-002",
    )
    with pytest.raises(LocalOperatorAuthorizationError):
        service.activate(_request(), _principal(permissions=frozenset()))
    assert repository.calls == []

    repository.error = HuntHypothesisStateConflictError(
        "stale", actual_status=HuntHypothesisStatus.ACTIVE
    )
    with pytest.raises(HuntHypothesisStateConflictError):
        service.activate(_request(), _principal())

    events = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert [event["reason"] for event in events] == [
        "authorization_denied",
        "authorized_attempt",
        "expected_state_mismatch",
    ]
    assert events[-1]["expected_status"] == "draft"
    assert events[-1]["current_status"] == "active"
    assert events[-2]["current_status"] is None


def test_only_draft_expected_state_is_admitted(tmp_path) -> None:
    service = HuntHypothesisActivationService(
        Repository(_hypothesis(HuntHypothesisStatus.DRAFT)),
        FileHuntHypothesisActivationAuditSink(str(tmp_path / "audit.jsonl")),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "attempt-003",
    )
    with pytest.raises(HuntHypothesisActivationValidationError):
        service.activate(
            HuntHypothesisActivationInput(
                "hypothesis-001", HuntHypothesisStatus.ACTIVE
            ),
            _principal(),
        )


def test_audit_failure_is_not_reported_as_activation_success() -> None:
    repository = Repository(_hypothesis(HuntHypothesisStatus.DRAFT))
    service = HuntHypothesisActivationService(
        repository,
        FailingAudit(),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "attempt-004",
    )
    with pytest.raises(HuntHypothesisActivationAuditError):
        service.activate(_request(), _principal())
    assert repository.calls == []


def test_terminal_audit_failure_is_propagated_after_authorized_attempt() -> None:
    repository = Repository(_hypothesis(HuntHypothesisStatus.DRAFT))
    audit = FailSecondAudit()
    service = HuntHypothesisActivationService(
        repository,
        audit,
        clock=lambda: NOW,
        attempt_id_generator=lambda: "attempt-005",
    )

    with pytest.raises(HuntHypothesisActivationAuditError):
        service.activate(_request(), _principal())

    assert repository.calls == [("hypothesis-001", HuntHypothesisStatus.DRAFT)]
    assert [event["phase"] for event in audit.events] == ["attempt"]


def test_partial_terminal_audit_write_failure_rolls_back_without_false_success(
    tmp_path, monkeypatch
) -> None:
    from application.hunt_hypotheses import FileHuntHypothesisRepository

    repository_path = tmp_path / "hypotheses.json"
    repository_path.write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "hypotheses": [_hypothesis(HuntHypothesisStatus.DRAFT).to_dict()],
            }
        ),
        encoding="utf-8",
    )
    audit_path = tmp_path / "audit.jsonl"
    import application.hunt_hypothesis_activation as activation_module

    fsync = activation_module._fsync_audit
    calls = 0

    def fail_second_fsync(file_descriptor) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated durability failure")
        fsync(file_descriptor)

    monkeypatch.setattr(activation_module, "_fsync_audit", fail_second_fsync)
    repository = FileHuntHypothesisRepository(str(repository_path))
    service = HuntHypothesisActivationService(
        repository,
        FileHuntHypothesisActivationAuditSink(str(audit_path)),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "attempt-partial-terminal",
    )

    with pytest.raises(HuntHypothesisActivationAuditError):
        service.activate(_request(), _principal())

    events = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert [event["outcome"] for event in events] == ["authorized", "rolled_back"]
    assert all(event["commit_state"] != "committed" for event in events)
    assert events[0]["current_status"] is None
    assert events[-1]["mutation_state"] == "rolled_back"
    assert repository.list()[0].status is HuntHypothesisStatus.DRAFT


def test_http_rejection_auditor_persists_only_safe_projection(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    auditor = HuntHypothesisActivationAttemptAuditor(
        FileHuntHypothesisActivationAuditSink(str(audit_path)),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "http-rejection-001",
    )

    auditor.reject(
        hypothesis_id="hypothesis-001",
        principal_id=None,
        reason="authentication_required",
    )

    event = json.loads(audit_path.read_text(encoding="utf-8"))
    assert event == {
        "authorization_outcome": "not_evaluated",
        "attempt_id": "http-rejection-001",
        "commit_state": "not_committed",
        "current_status": None,
        "expected_status": None,
        "hypothesis_id": "hypothesis-001",
        "mutation_state": "not_started",
        "operation": "hunt_hypothesis:activate",
        "outcome": "rejected",
        "phase": "terminal",
        "principal_id": None,
        "reason": "authentication_required",
        "resulting_status": None,
        "timestamp": NOW.isoformat(),
    }
    serialized = json.dumps(event)
    for forbidden in ("cookie", "session", "csrf", "credential", "secret"):
        assert forbidden not in serialized.lower()


@pytest.mark.parametrize(
    "unsafe_id",
    [
        "not-canonical",
        "hypothesis-Bearer-sensitive-credential/segment",
        "hypothesis-" + "oversized-sensitive-marker" * 20,
        "hypothesis-sensitive%2Fencoded",
    ],
)
def test_http_rejection_auditor_redacts_untrusted_route_identity(
    tmp_path, unsafe_id
) -> None:
    audit_path = tmp_path / "audit.jsonl"
    HuntHypothesisActivationAttemptAuditor(
        FileHuntHypothesisActivationAuditSink(str(audit_path)),
        clock=lambda: NOW,
        attempt_id_generator=lambda: "http-rejection-redacted",
    ).reject(
        hypothesis_id=unsafe_id,
        principal_id=None,
        reason="authentication_required",
    )

    serialized = audit_path.read_text(encoding="utf-8")
    assert json.loads(serialized)["hypothesis_id"] is None
    assert unsafe_id not in serialized


class Repository:
    def __init__(self, hypothesis: HuntHypothesis) -> None:
        self.hypothesis = hypothesis
        self.calls = []
        self.error = None

    def list(self):
        return (self.hypothesis,)

    def create(self, hypothesis):
        return hypothesis

    def activate(self, hypothesis_id, expected_status, terminal_callback=None):
        self.calls.append((hypothesis_id, expected_status))
        if self.error:
            raise self.error
        activated = _hypothesis(HuntHypothesisStatus.ACTIVE)
        if terminal_callback is not None:
            terminal_callback(activated)
        return activated


class FailingAudit:
    def append(self, event):
        raise HuntHypothesisActivationAuditError("audit failed")


class FailSecondAudit:
    def __init__(self):
        self.events = []

    def append(self, event):
        if self.events:
            raise HuntHypothesisActivationAuditError("terminal audit failed")
        self.events.append(event)


def _request() -> HuntHypothesisActivationInput:
    return HuntHypothesisActivationInput("hypothesis-001", HuntHypothesisStatus.DRAFT)


def _principal(*, permissions=frozenset({HUNT_HYPOTHESIS_ACTIVATE_PERMISSION})):
    return AuthenticatedPrincipal("operator-1", "Operator", "human/operator", permissions)


def _hypothesis(status: HuntHypothesisStatus) -> HuntHypothesis:
    return HuntHypothesis(
        hypothesis_id="hypothesis-001",
        title="Investigate a fictional signal",
        statement="A fictional signal may warrant investigation.",
        status=status,
        created_at=NOW,
        created_by="operator-1",
        target_references=(),
        threat_references=(),
        rationale="Human investigation is required.",
    )
