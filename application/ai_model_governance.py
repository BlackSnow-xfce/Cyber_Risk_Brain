from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable

from application.local_operator import (
    AIModelSelectionWriteAuthority,
    AuthenticatedPrincipal,
    AuthorizationDecision,
)
from core.ai_egress import AIModelEgressPurpose
from core.ai_model_selection import (
    AIModelCapability,
    AIModelRegistration,
    AIModelRegistrationStatus,
    AIModelRegistry,
    AIModelSelectionDecision,
    AIModelSelectionError,
    AIProviderFamily,
    default_ai_model_registry,
)


AI_MODEL_SELECTION_STATE_CONTRACT_VERSION = "1.0"
_STATE_LOCK = threading.Lock()
_AUDIT_LOCK = threading.Lock()


class AIModelSelectionPersistenceError(RuntimeError):
    pass


class AIModelSelectionUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AIModelAdapterBinding:
    provider: AIProviderFamily
    model_id: str
    capability: AIModelCapability


@dataclass(frozen=True, slots=True)
class AIModelCapabilityVisibility:
    capability: str
    authorized: bool
    adapter_available: bool
    execution_available: bool
    active: bool


@dataclass(frozen=True, slots=True)
class AIModelRegistrationVisibility:
    provider: str
    model_id: str
    api_protocol_family: str
    deployment_class: str
    policy_reference: str
    execution_binding: str
    status: str
    governance_status: str
    capabilities: tuple[AIModelCapabilityVisibility, ...]


@dataclass(frozen=True, slots=True)
class AIProviderGovernanceVisibility:
    provider: str
    governance_status: str
    registrations: tuple[AIModelRegistrationVisibility, ...]


@dataclass(frozen=True, slots=True)
class AIModelGovernanceVisibility:
    contract_version: str
    capabilities: tuple[str, ...]
    providers: tuple[AIProviderGovernanceVisibility, ...]


@dataclass(frozen=True, slots=True)
class PersistedAIModelSelection:
    capability: AIModelCapability
    provider: AIProviderFamily
    model_id: str
    policy_reference: str
    selected_at: datetime


@dataclass(frozen=True, slots=True)
class AIModelSelectionChangeResult:
    selection: PersistedAIModelSelection
    authorization: AuthorizationDecision


class FileAIModelSelectionStore:
    """Strict, atomic capability-scoped selection persistence."""

    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path.strip():
            raise AIModelSelectionPersistenceError(
                "AI model selection state path is unavailable."
            )
        self._path = Path(path)

    def list(self) -> tuple[PersistedAIModelSelection, ...]:
        if not self._path.exists():
            return ()
        try:
            document = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AIModelSelectionPersistenceError(
                "AI model selection state is invalid."
            ) from error
        if not isinstance(document, dict) or set(document) != {"contract_version", "selections"}:
            raise AIModelSelectionPersistenceError("AI model selection state is invalid.")
        if document["contract_version"] != AI_MODEL_SELECTION_STATE_CONTRACT_VERSION:
            raise AIModelSelectionPersistenceError("AI model selection state is invalid.")
        records = document["selections"]
        if not isinstance(records, list):
            raise AIModelSelectionPersistenceError("AI model selection state is invalid.")
        selections = tuple(self._parse(item) for item in records)
        capabilities = [item.capability for item in selections]
        if len(capabilities) != len(set(capabilities)):
            raise AIModelSelectionPersistenceError("AI model selection state is ambiguous.")
        return selections

    def save(self, selection: PersistedAIModelSelection) -> PersistedAIModelSelection:
        with _STATE_LOCK:
            current = {
                item.capability: item
                for item in self.list()
            }
            current[selection.capability] = selection
            ordered = tuple(
                current[capability]
                for capability in AIModelCapability
                if capability in current
            )
            document = {
                "contract_version": AI_MODEL_SELECTION_STATE_CONTRACT_VERSION,
                "selections": [self._to_dict(item) for item in ordered],
            }
            self._atomic_write(document)
            persisted = {item.capability: item for item in self.list()}
            if persisted.get(selection.capability) != selection:
                raise AIModelSelectionPersistenceError(
                    "AI model selection persistence verification failed."
                )
            return selection

    def _atomic_write(self, document: dict[str, object]) -> None:
        temporary_path: Path | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(document, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self._path)
            temporary_path = None
        except OSError as error:
            raise AIModelSelectionPersistenceError(
                "AI model selection could not be safely persisted."
            ) from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _parse(value: object) -> PersistedAIModelSelection:
        expected = {"capability", "provider", "model_id", "policy_reference", "selected_at"}
        if not isinstance(value, dict) or set(value) != expected:
            raise AIModelSelectionPersistenceError("AI model selection state is invalid.")
        try:
            selected_at = datetime.fromisoformat(value["selected_at"])
            model_id = value["model_id"]
            policy_reference = value["policy_reference"]
            if not isinstance(model_id, str) or not isinstance(policy_reference, str):
                raise ValueError("selection strings are invalid")
            selection = PersistedAIModelSelection(
                capability=AIModelCapability(value["capability"]),
                provider=AIProviderFamily(value["provider"]),
                model_id=model_id,
                policy_reference=policy_reference,
                selected_at=selected_at,
            )
        except (TypeError, ValueError) as error:
            raise AIModelSelectionPersistenceError("AI model selection state is invalid.") from error
        if selected_at.tzinfo is None or not selection.model_id.strip() or not selection.policy_reference.strip():
            raise AIModelSelectionPersistenceError("AI model selection state is invalid.")
        return selection

    @staticmethod
    def _to_dict(selection: PersistedAIModelSelection) -> dict[str, str]:
        return {
            "capability": selection.capability.value,
            "provider": selection.provider.value,
            "model_id": selection.model_id,
            "policy_reference": selection.policy_reference,
            "selected_at": selection.selected_at.isoformat(),
        }


class FileAIModelSelectionAuditSink:
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def append(self, event: dict[str, str | None]) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(event, ensure_ascii=False, sort_keys=True)
            with _AUDIT_LOCK, self._path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(serialized + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as error:
            raise AIModelSelectionPersistenceError(
                "AI model selection audit could not be persisted."
            ) from error


class AIModelGovernanceQueryService:
    """Projects canonical registry state without selecting or executing a model."""

    def __init__(
        self,
        registry: AIModelRegistry | None = None,
        *,
        adapter_bindings: frozenset[AIModelAdapterBinding] = frozenset(),
        execution_bindings: frozenset[AIModelAdapterBinding] = frozenset(),
        selection_store: FileAIModelSelectionStore | None = None,
        default_selections: dict[
            AIModelCapability,
            tuple[AIProviderFamily, str],
        ] | None = None,
    ) -> None:
        self._registry = registry or default_ai_model_registry()
        self._adapter_bindings = adapter_bindings
        self._execution_bindings = execution_bindings
        self._selection_store = selection_store
        self._default_selections = default_selections or {
            AIModelCapability.FINDING_EXPLANATION: (
                AIProviderFamily.OPENAI,
                "gpt-5.6",
            )
        }

    def get_visibility(self) -> AIModelGovernanceVisibility:
        persisted = self._selection_store.list() if self._selection_store is not None else ()
        for selection in persisted:
            self._registry.select(
                selection.capability,
                provider_id=selection.provider.value,
                model_id=selection.model_id,
            )
        active_selections = dict(self._default_selections)
        active_selections.update({
            item.capability: (item.provider, item.model_id)
            for item in persisted
        })
        providers = tuple(
            self._provider_visibility(provider, active_selections)
            for provider in AIProviderFamily
        )
        return AIModelGovernanceVisibility(
            contract_version="1.0",
            capabilities=tuple(capability.value for capability in AIModelCapability),
            providers=providers,
        )

    def _provider_visibility(
        self,
        provider: AIProviderFamily,
        active_selections: dict[AIModelCapability, tuple[AIProviderFamily, str]],
    ) -> AIProviderGovernanceVisibility:
        registrations = tuple(
            self._registration_visibility(registration, active_selections)
            for registration in self._registry.registrations
            if registration.identity.provider is provider
        )
        return AIProviderGovernanceVisibility(
            provider=provider.value,
            governance_status=("registered" if registrations else "foundation_only"),
            registrations=registrations,
        )

    def _registration_visibility(
        self,
        registration: AIModelRegistration,
        active_selections: dict[AIModelCapability, tuple[AIProviderFamily, str]],
    ) -> AIModelRegistrationVisibility:
        capability_visibility = tuple(
            self._capability_visibility(
                registration,
                capability,
                active_selections.get(capability),
            )
            for capability in AIModelCapability
        )
        enabled = registration.status is AIModelRegistrationStatus.ENABLED
        executable = any(item.execution_available for item in capability_visibility)
        adapter_available = any(item.adapter_available for item in capability_visibility)
        governance_status = (
            "disabled"
            if not enabled
            else "executable"
            if executable
            else "adapter_available_configuration_unavailable"
            if adapter_available
            else "governed_not_executable"
        )
        identity = registration.identity
        return AIModelRegistrationVisibility(
            provider=identity.provider_id,
            model_id=identity.model_id,
            api_protocol_family=identity.api_protocol_family.value,
            deployment_class=identity.deployment_class.value,
            policy_reference=registration.governance_policy_reference,
            execution_binding=identity.execution_binding_version,
            status=registration.status.value,
            governance_status=governance_status,
            capabilities=capability_visibility,
        )

    def _capability_visibility(
        self,
        registration: AIModelRegistration,
        capability: AIModelCapability,
        active_selection: tuple[AIProviderFamily, str] | None,
    ) -> AIModelCapabilityVisibility:
        binding = AIModelAdapterBinding(
            provider=registration.identity.provider,
            model_id=registration.identity.model_id,
            capability=capability,
        )
        authorized = capability in registration.enabled_capabilities
        enabled = registration.status is AIModelRegistrationStatus.ENABLED
        adapter_available = authorized and binding in self._adapter_bindings
        execution_available = (
            enabled
            and adapter_available
            and binding in self._execution_bindings
        )
        return AIModelCapabilityVisibility(
            capability=capability.value,
            authorized=authorized,
            adapter_available=adapter_available,
            execution_available=execution_available,
            active=(
                active_selection
                == (registration.identity.provider, registration.identity.model_id)
            ),
        )


class AIModelSelectionService:
    def __init__(
        self,
        registry: AIModelRegistry,
        store: FileAIModelSelectionStore,
        audit_sink: FileAIModelSelectionAuditSink,
        *,
        adapter_bindings: frozenset[AIModelAdapterBinding],
        execution_bindings: frozenset[AIModelAdapterBinding],
        authority: AIModelSelectionWriteAuthority | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._registry = registry
        self._store = store
        self._audit_sink = audit_sink
        self._adapter_bindings = adapter_bindings
        self._execution_bindings = execution_bindings
        self._authority = authority or AIModelSelectionWriteAuthority()
        self._clock = clock

    def change(
        self,
        capability: AIModelCapability,
        provider_id: str,
        model_id: str,
        principal: AuthenticatedPrincipal,
    ) -> AIModelSelectionChangeResult:
        previous = next(
            (item for item in self._store.list() if item.capability is capability),
            None,
        )
        timestamp = self._now()
        try:
            authorization = self._authority.require(principal)
            decision = self._registry.select(
                capability,
                provider_id=provider_id,
                model_id=model_id,
            )
            binding = AIModelAdapterBinding(
                provider=decision.identity.provider,
                model_id=decision.model_id,
                capability=capability,
            )
            if binding not in self._adapter_bindings:
                raise AIModelSelectionUnavailableError(
                    "No governed live adapter is available."
                )
            if binding not in self._execution_bindings:
                raise AIModelSelectionUnavailableError(
                    "The governed model server configuration is unavailable."
                )
            selection = self._selection(decision, timestamp)
            persisted = self._store.save(selection)
            self._audit(
                capability,
                previous,
                persisted,
                decision.selection_policy_reference,
                timestamp,
                "selected",
                "governed_selection_updated",
            )
            return AIModelSelectionChangeResult(persisted, authorization)
        except Exception as error:
            reason = self._safe_reason(error)
            self._audit(
                capability,
                previous,
                None,
                None,
                timestamp,
                "rejected",
                reason,
            )
            raise

    def selection_decision(
        self,
        capability: AIModelCapability,
        *,
        default_provider_id: str,
        default_model_id: str,
    ) -> AIModelSelectionDecision:
        selected = next(
            (item for item in self._store.list() if item.capability is capability),
            None,
        )
        return self._registry.select(
            capability,
            provider_id=(selected.provider.value if selected else default_provider_id),
            model_id=(selected.model_id if selected else default_model_id),
        )

    @staticmethod
    def _selection(
        decision: AIModelSelectionDecision,
        timestamp: datetime,
    ) -> PersistedAIModelSelection:
        return PersistedAIModelSelection(
            capability=decision.requested_capability,
            provider=decision.identity.provider,
            model_id=decision.model_id,
            policy_reference=decision.selection_policy_reference,
            selected_at=timestamp,
        )

    def _audit(
        self,
        capability: AIModelCapability,
        previous: PersistedAIModelSelection | None,
        current: PersistedAIModelSelection | None,
        policy_reference: str | None,
        timestamp: datetime,
        outcome: str,
        reason: str,
    ) -> None:
        self._audit_sink.append(
            {
                "capability": capability.value,
                "previous_provider": previous.provider.value if previous else None,
                "previous_model_id": previous.model_id if previous else None,
                "new_provider": current.provider.value if current else None,
                "new_model_id": current.model_id if current else None,
                "policy_reference": policy_reference,
                "outcome": outcome,
                "reason": reason,
                "timestamp": timestamp.isoformat(),
            }
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise AIModelSelectionPersistenceError(
                "AI model selection clock must be timezone-aware."
            )
        return value

    @staticmethod
    def _safe_reason(error: Exception) -> str:
        if isinstance(error, AIModelSelectionUnavailableError):
            return "execution_unavailable"
        if isinstance(error, AIModelSelectionError):
            return "registry_rejected"
        if isinstance(error, AIModelSelectionPersistenceError):
            return "persistence_failed"
        return "authorization_or_integrity_rejected"


class PersistedAIModelSelectionPolicy:
    """Execution policy backed by the capability-specific persisted selection."""

    def __init__(self, service: AIModelSelectionService) -> None:
        self._service = service

    def resolve(
        self,
        purpose: AIModelEgressPurpose,
    ) -> AIModelSelectionDecision:
        if purpose is not AIModelEgressPurpose.FINDING_EXPLANATION:
            raise AIModelSelectionError("purpose is not supported.")
        return self._service.selection_decision(
            AIModelCapability.FINDING_EXPLANATION,
            default_provider_id="openai",
            default_model_id="gpt-5.6",
        )
