"""Production trust boundary for terminal dependency recovery evidence.

This module deliberately contains no identity-provider or process-inspection
implementation. Those boundaries must be supplied by independently deployed,
authenticated services. Missing any boundary is a hard BLOCKED state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import ProductOwnerGateDependencyAuthorityV1, ProductOwnerGateDependencyRecoveryAuthorityV1
from .terminal_gate_dependency_recovery import (
    GateDependencyRecoveryEvidenceVerifier, VerifiedGateDependencyRecoveryEvidence,
)


class RecoveryEvidenceProvider(Protocol):
    def assess(self, authority: ProductOwnerGateDependencyRecoveryAuthorityV1, *,
               predecessor: ProductOwnerGateDependencyAuthorityV1,
               source: ProductOwnerGateDependencyAuthorityV1) -> VerifiedGateDependencyRecoveryEvidence: ...


@dataclass(frozen=True, slots=True)
class TrustedVerifierReadiness:
    state: str
    reason: str


class ProductionGateDependencyRecoveryVerifier(GateDependencyRecoveryEvidenceVerifier):
    """Delegates to one authenticated, independently deployed evidence boundary.

    The provider is intentionally mandatory and is not loaded from Git,
    ordinary environment variables, or untrusted contract data.
    """

    def __init__(self, provider: RecoveryEvidenceProvider | None = None):
        self.provider = provider

    def readiness(self) -> TrustedVerifierReadiness:
        if self.provider is None:
            return TrustedVerifierReadiness("BLOCKED", "TRUSTED_VERIFIER_UNAVAILABLE")
        return TrustedVerifierReadiness("READY", "trusted evidence provider configured")

    def verify(self, authority, *, predecessor, source):
        if self.provider is None:
            raise PermissionError("TRUSTED_VERIFIER_UNAVAILABLE")
        evidence = self.provider.assess(authority, predecessor=predecessor, source=source)
        if not isinstance(evidence, VerifiedGateDependencyRecoveryEvidence):
            raise PermissionError("untrusted recovery evidence provider response")
        return evidence
