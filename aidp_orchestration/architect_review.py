"""Headless, fail-closed Architect review execution and authority validation."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from .contracts import (
    ArchitectFinding,
    ArchitectReviewDisposition,
    ArchitectReviewProvenance,
    ArchitectReviewRequest,
    ArchitectReviewResult,
    ExecutionStatus,
    ScopeCompliance,
    ValidationResult,
    canonical_digest,
    utc_now,
)
from .control_plane import scope_is_subset
from .executor import SubprocessRunner
from .executor_types import ProcessRunner
from .launcher import CodexLauncher, resolve_codex_launcher


ARCHITECT_OUTPUT_SCHEMA_VERSION = "architect-review-result-v1"
MAX_CAPTURE_BYTES = 1_048_576


class ProductWorktreeIdentityGuard:
    """Binds lifecycle authority to one configured Product worktree."""

    def __init__(
        self,
        product_root: Path,
        *,
        expected_branch: str,
        excluded_roots: tuple[Path, ...],
        expected_remote_url: str | None = None,
    ) -> None:
        self.product_root = product_root.resolve()
        self.expected_branch = expected_branch
        self.excluded_roots = tuple(path.resolve() for path in excluded_roots)
        self.expected_remote_url = expected_remote_url

    def validate(self, *, expected_head: str | None = None, require_clean: bool = True) -> dict[str, str]:
        if self.product_root in self.excluded_roots:
            raise ValueError("configured Product root is an excluded worktree")
        top = Path(self._git("rev-parse", "--show-toplevel")).resolve()
        if top != self.product_root:
            raise ValueError("configured Product root does not match Git top-level")
        common = Path(self._git("rev-parse", "--git-common-dir"))
        common = (self.product_root / common).resolve() if not common.is_absolute() else common.resolve()
        branch = self._git("branch", "--show-current")
        if branch != self.expected_branch:
            raise ValueError("Product branch identity mismatch")
        remote = self._git("remote", "get-url", "origin")
        if self.expected_remote_url is not None and remote != self.expected_remote_url:
            raise ValueError("Product origin identity mismatch")
        upstream = self._git("rev-parse", "@{upstream}")
        head = self._git("rev-parse", "HEAD")
        if expected_head is not None and head != expected_head:
            raise ValueError("Product HEAD is stale")
        if head != upstream:
            raise ValueError("Product branch diverges from upstream")
        if require_clean and self._git("status", "--porcelain=v1"):
            raise ValueError("Product worktree is unexpectedly dirty")
        return {
            "repository": str(self.product_root),
            "git_common_dir": str(common),
            "branch": branch,
            "remote_url": remote,
            "head": head,
        }

    def _git(self, *args: str) -> str:
        return subprocess.check_output(
            ("git", *args), cwd=self.product_root, text=True, stderr=subprocess.STDOUT,
        ).strip()


def create_review_request(**values: object) -> ArchitectReviewRequest:
    """Create a request whose identity is derived solely from immutable evidence."""

    identity = canonical_digest({
        "schema": "architect-review-request-v1",
        "task_id": values["task_id"], "review_iteration": values["review_iteration"],
        "execution_id": values["execution_id"], "authority_contract_digest": values["authority_contract_digest"],
        "review_envelope_digest": values["review_envelope_digest"],
        "expected_current_head": values["expected_current_head"], "reviewed_head": values["reviewed_head"],
        "reviewed_tree_hash": values["reviewed_tree_hash"],
    })
    return ArchitectReviewRequest(review_request_id=identity, **values)  # type: ignore[arg-type]


def create_review_result(**values: object) -> ArchitectReviewResult:
    identity = canonical_digest({"schema": "architect-review-result-v1", **values})
    return ArchitectReviewResult(review_result_id=identity, **values)  # type: ignore[arg-type]


class ArchitectReviewCoordinator:
    def __init__(
        self,
        *,
        product_root: Path,
        identity_guard: ProductWorktreeIdentityGuard,
        runner: ProcessRunner | None = None,
        launcher: CodexLauncher | None = None,
        timeout_seconds: float = 900.0,
        max_capture_bytes: int = MAX_CAPTURE_BYTES,
        clock: Callable[[], datetime] = utc_now,
        model: str = "configured-codex-model",
    ) -> None:
        if max_capture_bytes < 1:
            raise ValueError("max_capture_bytes must be positive")
        self.product_root = product_root.resolve()
        self.identity_guard = identity_guard
        self.runner = runner or SubprocessRunner(max_capture_bytes=max_capture_bytes)
        self.launcher = launcher
        self.timeout_seconds = timeout_seconds
        self.max_capture_bytes = max_capture_bytes
        self.clock = clock
        self.model = model

    def review(self, request: ArchitectReviewRequest, *, schema_path: Path) -> ArchitectReviewResult:
        started = self.clock()
        identity = self.identity_guard.validate(expected_head=request.expected_current_head)
        if (
            identity["repository"] != str(self.product_root)
            or request.repository != str(self.product_root)
            or identity["git_common_dir"] != request.git_common_dir
            or identity["branch"] != request.branch
            or identity["remote_url"] != request.remote_url
        ):
            return self._blocked(request, started, "Product repository identity does not match review request")
        try:
            launcher = self.launcher or resolve_codex_launcher()
        except Exception as exc:
            return self._blocked(request, started, f"Architect launcher unavailable: {exc.__class__.__name__}")
        capability = self.runner.run(
            (*launcher.argv_prefix, "exec", "--help"), cwd=self.product_root,
            timeout_seconds=min(self.timeout_seconds, 30.0),
        )
        required = ("--sandbox", "--ephemeral", "--ignore-user-config", "--output-schema", "--json")
        if capability.returncode != 0 or capability.error or any(flag not in capability.stdout for flag in required):
            return self._blocked(request, started, "Architect CLI capability validation failed", launcher)
        command = launcher.argv_prefix + (
            "exec", "--sandbox", "read-only", "--ephemeral", "--ignore-user-config", "--json", "--color", "never",
            "--output-schema", str(schema_path.resolve()), "--cd", str(self.product_root),
            self._prompt(request),
        )
        outcome = self.runner.run(command, cwd=self.product_root, timeout_seconds=self.timeout_seconds)
        if outcome.timed_out:
            return self._blocked(
                request, started, "Architect process timed out", launcher, outcome.process_identity,
                outcome.process_started_at, outcome.process_completed_at,
            )
        if outcome.error:
            return self._blocked(
                request, started, outcome.error, launcher, outcome.process_identity,
                outcome.process_started_at, outcome.process_completed_at,
            )
        if outcome.returncode != 0:
            return self._blocked(
                request, started, f"Architect exited with code {outcome.returncode}", launcher,
                outcome.process_identity, outcome.process_started_at, outcome.process_completed_at,
            )
        if len(outcome.stdout.encode("utf-8")) > self.max_capture_bytes or len(outcome.stderr.encode("utf-8")) > self.max_capture_bytes:
            return self._blocked(request, started, "Architect process output exceeded capture limit", launcher)
        try:
            payload = json.loads(_last_message_payload(outcome.stdout))
            if outcome.process_identity is None or outcome.process_started_at is None or outcome.process_completed_at is None:
                raise ValueError("Architect process provenance is unavailable")
            result = self._result_from_decision(
                request, payload, launcher, outcome.process_identity,
                outcome.process_started_at, outcome.process_completed_at,
            )
            validate_review_result(request, result)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self._blocked(request, started, f"Architect result is invalid: {exc.__class__.__name__}", launcher)
        return result

    def _result_from_decision(
        self,
        request: ArchitectReviewRequest,
        payload: dict[str, object],
        launcher: CodexLauncher,
        process_identity: str,
        process_started_at: datetime,
        process_completed_at: datetime,
    ) -> ArchitectReviewResult:
        if set(payload) != {
            "disposition", "findings", "allowed_rework_scope", "required_validations",
            "failure_reason", "authority_claims",
        }:
            raise ValueError("Architect decision fields do not match schema")
        finding_values = _objects(payload, "findings")
        finding_fields = {"finding_id", "rule_id", "severity", "summary", "evidence_paths", "action_id", "required_change"}
        if any(set(item) != finding_fields for item in finding_values):
            raise ValueError("Architect finding fields do not match schema")
        findings = tuple(ArchitectFinding(
            finding_id=_string(item, "finding_id"), rule_id=_string(item, "rule_id"),
            severity=_string(item, "severity"), summary=_string(item, "summary"),
            evidence_paths=tuple(_strings(item, "evidence_paths")), action_id=_string(item, "action_id"),
            required_change=_string(item, "required_change"),
        ) for item in finding_values)
        created = self.clock()
        provenance = ArchitectReviewProvenance(
            process_identity=process_identity,
            launcher_identity=" ".join(launcher.argv_prefix), model=self.model,
            invocation_started_at=process_started_at, invocation_completed_at=process_completed_at,
            output_schema_version=ARCHITECT_OUTPUT_SCHEMA_VERSION,
        )
        values = dict(
            review_request_id=request.review_request_id, task_id=request.task_id,
            execution_id=request.execution_id, review_iteration=request.review_iteration,
            disposition=ArchitectReviewDisposition(_string(payload, "disposition")),
            reviewed_head=request.reviewed_head, expected_head=request.expected_current_head,
            reviewed_tree_hash=request.reviewed_tree_hash, findings=findings,
            allowed_rework_scope=tuple(_strings(payload, "allowed_rework_scope")),
            required_validations=tuple(_strings(payload, "required_validations")), provenance=provenance,
            failure_reason=_optional_string(payload, "failure_reason"),
            authority_claims=tuple(_strings(payload, "authority_claims")), created_at=created,
        )
        return create_review_result(**values)

    def revalidate(self, request: ArchitectReviewRequest) -> None:
        identity = self.identity_guard.validate(expected_head=request.expected_current_head)
        expected = {
            "repository": request.repository,
            "git_common_dir": request.git_common_dir,
            "branch": request.branch,
            "remote_url": request.remote_url,
            "head": request.expected_current_head,
        }
        if identity != expected:
            raise ValueError("Product repository identity changed during Architect review")

    def _blocked(
        self,
        request: ArchitectReviewRequest,
        started: datetime,
        reason: str,
        launcher: CodexLauncher | None = None,
        process_identity: str | None = None,
        process_started_at: datetime | None = None,
        process_completed_at: datetime | None = None,
    ) -> ArchitectReviewResult:
        provenance = ArchitectReviewProvenance(
            process_identity=process_identity or "unavailable",
            launcher_identity="unavailable" if launcher is None else " ".join(launcher.argv_prefix),
            model=self.model,
            invocation_started_at=process_started_at or started,
            invocation_completed_at=process_completed_at or self.clock(),
            output_schema_version=ARCHITECT_OUTPUT_SCHEMA_VERSION,
        )
        values = dict(
            review_request_id=request.review_request_id,
            task_id=request.task_id,
            execution_id=request.execution_id,
            review_iteration=request.review_iteration,
            disposition=ArchitectReviewDisposition.BLOCKED,
            reviewed_head=request.reviewed_head,
            expected_head=request.expected_current_head,
            reviewed_tree_hash=request.reviewed_tree_hash,
            findings=(),
            allowed_rework_scope=(),
            required_validations=(),
            provenance=provenance,
            failure_reason=reason,
            authority_claims=(),
            created_at=self.clock(),
        )
        return create_review_result(**values)

    @staticmethod
    def _prompt(request: ArchitectReviewRequest) -> str:
        evidence = json.dumps(asdict(request), default=_json_default, sort_keys=True, separators=(",", ":"))
        return (
            "Review the immutable AIDP execution evidence. Do not modify files and do not assert Product Owner, "
            "DONE, or next-task authority. Return only the schema-constrained ArchitectReviewResult.\n"
            f"architect_review_request={evidence}"
        )


def validate_review_result(request: ArchitectReviewRequest, result: ArchitectReviewResult) -> None:
    if (
        result.review_request_id != request.review_request_id
        or result.task_id != request.task_id
        or result.execution_id != request.execution_id
        or result.review_iteration != request.review_iteration
        or result.reviewed_head != request.reviewed_head
        or result.expected_head != request.expected_current_head
        or result.reviewed_tree_hash != request.reviewed_tree_hash
    ):
        raise ValueError("Architect result does not bind exactly to its request")
    if result.disposition is ArchitectReviewDisposition.FAIL:
        if not scope_is_subset(result.allowed_rework_scope, request.original_allowed_scope):
            raise ValueError("Architect result widens task scope")
        if any(value not in request.original_validation_requirements for value in result.required_validations):
            raise ValueError("Architect result widens validator authority")
        if any(not scope_is_subset(finding.evidence_paths, request.original_allowed_scope) for finding in result.findings):
            raise ValueError("Architect finding evidence is outside task scope")


def parse_architect_review_result(payload: str) -> ArchitectReviewResult:
    value = json.loads(payload)
    expected = {
        "review_result_id", "review_request_id", "task_id", "execution_id", "review_iteration",
        "disposition", "reviewed_head", "expected_head", "reviewed_tree_hash", "findings",
        "allowed_rework_scope", "required_validations", "provenance", "failure_reason",
        "authority_claims", "created_at",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("ArchitectReviewResult fields do not match schema")
    finding_values = _objects(value, "findings")
    finding_fields = {"finding_id", "rule_id", "severity", "summary", "evidence_paths", "action_id", "required_change"}
    if any(set(item) != finding_fields for item in finding_values):
        raise ValueError("Architect finding fields do not match schema")
    findings = tuple(ArchitectFinding(
        finding_id=_string(item, "finding_id"), rule_id=_string(item, "rule_id"),
        severity=_string(item, "severity"), summary=_string(item, "summary"),
        evidence_paths=tuple(_strings(item, "evidence_paths")), action_id=_string(item, "action_id"),
        required_change=_string(item, "required_change"),
    ) for item in finding_values)
    provenance_value = _object(value, "provenance")
    if set(provenance_value) != {
        "process_identity", "launcher_identity", "model", "invocation_started_at",
        "invocation_completed_at", "output_schema_version",
    }:
        raise ValueError("Architect provenance fields do not match schema")
    provenance = ArchitectReviewProvenance(
        _string(provenance_value, "process_identity"), _string(provenance_value, "launcher_identity"),
        _string(provenance_value, "model"), datetime.fromisoformat(_string(provenance_value, "invocation_started_at")),
        datetime.fromisoformat(_string(provenance_value, "invocation_completed_at")),
        _string(provenance_value, "output_schema_version"),
    )
    return ArchitectReviewResult(
        review_result_id=_string(value, "review_result_id"),
        review_request_id=_string(value, "review_request_id"), task_id=_string(value, "task_id"),
        execution_id=_string(value, "execution_id"), review_iteration=_integer(value, "review_iteration"),
        disposition=ArchitectReviewDisposition(_string(value, "disposition")),
        reviewed_head=_string(value, "reviewed_head"), expected_head=_string(value, "expected_head"),
        reviewed_tree_hash=_string(value, "reviewed_tree_hash"), findings=findings,
        allowed_rework_scope=tuple(_strings(value, "allowed_rework_scope")),
        required_validations=tuple(_strings(value, "required_validations")), provenance=provenance,
        failure_reason=_optional_string(value, "failure_reason"),
        authority_claims=tuple(_strings(value, "authority_claims")),
        created_at=datetime.fromisoformat(_string(value, "created_at")),
    )


def parse_architect_review_request(payload: str) -> ArchitectReviewRequest:
    value = json.loads(payload)
    expected = {field.name for field in fields(ArchitectReviewRequest)}
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("ArchitectReviewRequest fields do not match schema")
    validations = tuple(
        ValidationResult(_string(item, "name"), _boolean(item, "passed"), _string(item, "detail"))
        for item in _objects(value, "validation_results")
    )
    return ArchitectReviewRequest(
        review_request_id=_string(value, "review_request_id"), task_id=_string(value, "task_id"),
        review_iteration=_integer(value, "review_iteration"), execution_id=_string(value, "execution_id"),
        repository=_string(value, "repository"), git_common_dir=_string(value, "git_common_dir"),
        branch=_string(value, "branch"), remote_url=_string(value, "remote_url"),
        authority_contract_id=_string(value, "authority_contract_id"),
        authority_contract_digest=_string(value, "authority_contract_digest"),
        original_allowed_scope=tuple(_strings(value, "original_allowed_scope")),
        original_prohibited_actions=tuple(_strings(value, "original_prohibited_actions")),
        original_validation_requirements=tuple(_strings(value, "original_validation_requirements")),
        original_acceptance_criteria=tuple(_strings(value, "original_acceptance_criteria")),
        product_owner_gate=_boolean(value, "product_owner_gate"),
        review_envelope_path=_string(value, "review_envelope_path"),
        review_envelope_digest=_string(value, "review_envelope_digest"),
        execution_status=ExecutionStatus(_string(value, "execution_status")),
        start_commit=_string(value, "start_commit"), resulting_commit=_string(value, "resulting_commit"),
        review_envelope_commit=_string(value, "review_envelope_commit"),
        changed_files=tuple(_strings(value, "changed_files")), validation_results=validations,
        scope_compliance=ScopeCompliance(_string(value, "scope_compliance")),
        expected_current_head=_string(value, "expected_current_head"), current_head=_string(value, "current_head"),
        reviewed_head=_string(value, "reviewed_head"), reviewed_tree_hash=_string(value, "reviewed_tree_hash"),
        previous_review_result_id=_optional_string(value, "previous_review_result_id"),
        previous_rework_contract_id=_optional_string(value, "previous_rework_contract_id"),
        previous_finding_fingerprints=tuple(_strings(value, "previous_finding_fingerprints")),
        created_at=datetime.fromisoformat(_string(value, "created_at")),
    )
def serialize_review_request(value: ArchitectReviewRequest) -> str:
    return json.dumps({"architect_review_request": asdict(value)}, default=_json_default, sort_keys=True, separators=(",", ":"))


def serialize_review_result(value: ArchitectReviewResult) -> str:
    return json.dumps({"architect_review_result": asdict(value)}, default=_json_default, sort_keys=True, separators=(",", ":"))


def architect_result_schema() -> dict[str, object]:
    """Strict top-level schema passed to Codex; local parsing remains authoritative."""
    finding_properties = {
        "finding_id": {"type": "string"}, "rule_id": {"type": "string"}, "severity": {"type": "string"},
        "summary": {"type": "string"}, "evidence_paths": {"type": "array", "items": {"type": "string"}},
        "action_id": {"type": "string"}, "required_change": {"type": "string"},
    }
    properties = {
        "disposition": {"enum": ["PASS", "FAIL", "BLOCKED"]},
        "findings": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": list(finding_properties), "properties": finding_properties}},
        "allowed_rework_scope": {"type": "array", "items": {"type": "string"}},
        "required_validations": {"type": "array", "items": {"type": "string"}},
        "failure_reason": {"type": ["string", "null"]},
        "authority_claims": {"type": "array", "items": {"type": "string"}},
    }
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def _last_message_payload(output: str) -> str:
    messages = []
    for line in output.splitlines():
        value = json.loads(line)
        if isinstance(value, dict) and value.get("type") == "item.completed":
            item = value.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                messages.append(item["text"])
    if len(messages) != 1:
        raise ValueError("Architect JSONL contains no unique final message")
    return messages[0]


def _json_default(value: object) -> object:
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, Enum): return value.value
    if isinstance(value, Path): return str(value)
    raise TypeError(type(value).__name__)


def _string(value: dict[str, object], name: str) -> str:
    item = value.get(name)
    if not isinstance(item, str): raise ValueError(f"{name} must be a string")
    return item


def _optional_string(value: dict[str, object], name: str) -> str | None:
    item = value.get(name)
    if item is not None and not isinstance(item, str): raise ValueError(f"{name} must be string or null")
    return item


def _integer(value: dict[str, object], name: str) -> int:
    item = value.get(name)
    if not isinstance(item, int) or isinstance(item, bool): raise ValueError(f"{name} must be integer")
    return item


def _boolean(value: dict[str, object], name: str) -> bool:
    item = value.get(name)
    if not isinstance(item, bool): raise ValueError(f"{name} must be boolean")
    return item


def _strings(value: dict[str, object], name: str) -> list[str]:
    item = value.get(name)
    if not isinstance(item, list) or any(not isinstance(entry, str) for entry in item): raise ValueError(f"{name} must be string array")
    return item


def _object(value: dict[str, object], name: str) -> dict[str, object]:
    item = value.get(name)
    if not isinstance(item, dict): raise ValueError(f"{name} must be object")
    return item


def _objects(value: dict[str, object], name: str) -> list[dict[str, object]]:
    item = value.get(name)
    if not isinstance(item, list) or any(not isinstance(entry, dict) for entry in item): raise ValueError(f"{name} must be object array")
    return item
