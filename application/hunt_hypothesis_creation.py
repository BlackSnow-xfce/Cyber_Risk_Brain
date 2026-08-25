from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID, uuid4

from application.hunt_hypotheses import HuntHypothesisRepository
from application.local_operator import (
    AuthenticatedPrincipal,
    AuthorizationDecision,
    HuntHypothesisWriteAuthority,
)
from core.threat_hunting import (
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisStatus,
)


class HuntHypothesisCreationValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class HuntHypothesisCreationInput:
    title: str
    statement: str
    rationale: str
    target_references: tuple[HuntHypothesisReference, ...]
    threat_references: tuple[HuntHypothesisReference, ...]


@dataclass(frozen=True, slots=True)
class HuntHypothesisCreationResult:
    hypothesis: HuntHypothesis
    authorization: AuthorizationDecision


class HuntHypothesisCreationService:
    def __init__(
        self,
        repository: HuntHypothesisRepository,
        *,
        authority: HuntHypothesisWriteAuthority | None = None,
        id_generator: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._repository = repository
        self._authority = authority or HuntHypothesisWriteAuthority()
        self._id_generator = id_generator
        self._clock = clock

    def create(
        self,
        request: HuntHypothesisCreationInput,
        principal: AuthenticatedPrincipal,
    ) -> HuntHypothesisCreationResult:
        authorization = self._authority.require(principal)
        try:
            identifier = self._id_generator()
            if not isinstance(identifier, UUID) or identifier.version != 4:
                raise ValueError("A UUIDv4 is required.")
            created_at = self._clock()
            if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
                raise ValueError("A timezone-aware timestamp is required.")
            hypothesis = HuntHypothesis(
                hypothesis_id=f"hypothesis-{identifier}",
                title=request.title,
                statement=request.statement,
                rationale=request.rationale,
                target_references=request.target_references,
                threat_references=request.threat_references,
                created_by=principal.principal_id,
                created_at=created_at,
                status=HuntHypothesisStatus.DRAFT,
            )
        except (TypeError, ValueError) as error:
            raise HuntHypothesisCreationValidationError(
                "Hunt Hypothesis creation input is invalid."
            ) from error
        persisted = self._repository.create(hypothesis)
        return HuntHypothesisCreationResult(
            hypothesis=persisted,
            authorization=authorization,
        )
