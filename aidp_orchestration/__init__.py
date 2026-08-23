"""Deterministic, fail-closed orchestration primitives for the AIDP workflow."""

from .acceptance import AcceptanceHarness, serialize_acceptance_result

from .contracts import (
    AIDPState,
    AcceptanceResult,
    AcceptanceStatus,
    CleanupStatus,
    CodexExecutionRequest,
    CodexExecutionResult,
    RunnerResult,
    RunnerStatus,
    ScopeCompliance,
    ValidationResult,
)
from .executor import (
    CodexExecutionService,
    ExecutionLock,
    GitInspector,
    ProcessOutcome,
    SubprocessRunner,
    serialize_execution_result,
)
from .repository import AIDPRepository
from .runner import AIDPRunner, serialize_runner_result
from .runtime import LocalRuntimeStore

__all__ = [
    "AIDPRepository",
    "AIDPState",
    "AcceptanceHarness",
    "AcceptanceResult",
    "AcceptanceStatus",
    "CleanupStatus",
    "CodexExecutionRequest",
    "CodexExecutionResult",
    "RunnerResult",
    "RunnerStatus",
    "ScopeCompliance",
    "ValidationResult",
    "CodexExecutionService",
    "ExecutionLock",
    "GitInspector",
    "ProcessOutcome",
    "SubprocessRunner",
    "serialize_execution_result",
    "serialize_acceptance_result",
    "AIDPRunner",
    "LocalRuntimeStore",
    "serialize_runner_result",
]
