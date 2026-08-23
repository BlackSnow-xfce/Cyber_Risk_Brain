"""Deterministic, fail-closed orchestration primitives for the AIDP workflow."""

from .acceptance import AcceptanceHarness, serialize_acceptance_result

from .contracts import (
    AIDPState,
    AcceptanceResult,
    AcceptanceStatus,
    CleanupStatus,
    ControlPlaneAction,
    ControlPlaneDecision,
    ControlPlaneResult,
    CodexExecutionRequest,
    CodexExecutionResult,
    RunnerResult,
    RunnerStatus,
    ScopeCompliance,
    ValidationResult,
    ReworkContract,
    ArchitectInboxEntry,
)
from .control_plane import (
    AIDPControlPlane,
    LocalArchitectInbox,
    LocalReworkContractStore,
    serialize_architect_inbox_entry,
    serialize_control_plane_decision,
    serialize_control_plane_result,
    serialize_rework_contract,
)
from .executor import (
    CodexExecutionService,
    ExecutionLock,
    GitInspector,
    ProcessOutcome,
    SubprocessRunner,
    serialize_execution_result,
)
from .launcher import CodexLauncher, CodexLauncherError, resolve_codex_launcher
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
    "ControlPlaneAction",
    "ControlPlaneDecision",
    "ControlPlaneResult",
    "CodexExecutionRequest",
    "CodexExecutionResult",
    "CodexLauncher",
    "CodexLauncherError",
    "RunnerResult",
    "RunnerStatus",
    "ScopeCompliance",
    "ValidationResult",
    "ReworkContract",
    "ArchitectInboxEntry",
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
    "resolve_codex_launcher",
    "AIDPControlPlane",
    "LocalArchitectInbox",
    "LocalReworkContractStore",
    "serialize_architect_inbox_entry",
    "serialize_control_plane_decision",
    "serialize_control_plane_result",
    "serialize_rework_contract",
]
