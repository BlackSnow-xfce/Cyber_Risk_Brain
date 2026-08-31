from collections.abc import Callable
from datetime import date, datetime
import threading
from typing import Literal
from urllib.parse import parse_qs

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict

from application import (
    AIModelAdapterBinding,
    AIModelGovernanceQueryService,
    AIModelGovernanceVisibility,
    AIModelSelectionPersistenceError,
    AIModelSelectionService,
    AIModelSelectionUnavailableError,
    AssetContextConfigurationError,
    AssetContextQueryService,
    FindingAssetContextUseCase,
    FindingExplanationModelOutput,
    FindingExplanationResult,
    FindingExplanationStatement,
    FindingExplanationUseCase,
    FindingRiskContext,
    FindingRiskContextUseCase,
    build_finding_explanation_authorization,
    FindingNotFoundError,
    FindingExplanationService,
    FindingSelectionError,
    IncidentCommandCenterIncidentNotFoundError,
    IncidentCommandCenterQueryService,
    IncidentReferenceResolutionService,
    IncidentContextConfigurationError,
    IncidentContextDataError,
    FileIncidentContextRepository,
    IncidentQueueQueryService,
    FindingThreatIntelligenceEnrichment,
    FindingThreatIntelligenceUseCase,
    FindingIncidentQueryService,
    FindingsConfigurationError,
    FindingsQueryService,
    FileHuntHypothesisRepository,
    FileHuntHypothesisActivationAuditSink,
    HuntHypothesisConfigurationError,
    HuntHypothesisConflictError,
    HuntHypothesisCreationInput,
    HuntHypothesisCreationService,
    HuntHypothesisCreationValidationError,
    HuntHypothesisDataError,
    HuntHypothesisPersistenceError,
    HuntHypothesisRepositoryNotFoundError,
    HuntHypothesisStateConflictError,
    HuntHypothesisActivationAuditError,
    HuntHypothesisActivationInput,
    HuntHypothesisActivationService,
    HuntHypothesisActivationAttemptAuditor,
    HuntHypothesisActivationValidationError,
    safe_hypothesis_audit_id,
    HuntHypothesisQueryService,
    HuntHypothesisNotFoundError,
    HuntHypothesisReferenceIntegrityError,
    HuntHypothesisReferenceResolutionResult,
    HuntHypothesisReferenceResolutionService,
    AuthenticatedPrincipal,
    HuntHypothesisWriteAuthority,
    LocalOperatorAuthenticationError,
    LocalOperatorAuthenticator,
    LocalOperatorAuthorizationError,
    LocalOperatorConfigurationIntegrityError,
    LocalOperatorConfigurationUnavailableError,
    configured_local_operator_origins,
    LOCAL_OPERATOR_BACKEND_HOST,
    LocalOperatorBrowserSession,
    LocalOperatorSessionAuthenticationError,
    LocalOperatorSessionConfiguration,
    LocalOperatorSessionCsrfError,
    LocalOperatorSessionStore,
    RiskReadinessService,
    RiskAssessmentReadinessService,
    SecurityObservationCorrelationApplicationService,
    FileAIModelSelectionAuditSink,
    FileAIModelSelectionStore,
    PersistedAIModelSelectionPolicy,
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceDataError,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceNotFoundError,
    ThreatIntelligenceQueryService,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.ai_model_selection import (
    AIModelCapability,
    AIProviderFamily,
    SUPPORTED_MODEL_ID,
    default_ai_model_registry,
)
from core.explainability import ExplanationProvenance
from core.incident_response import (
    AnalystNote,
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentActivity,
    IncidentPrincipalReference,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)
from core.predator_engine import PredatorEngine
from core.decision.models import Evidence
from core.security_observation import SecurityObservationCorrelationService
from core.threat_hunting import (
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)
from core.threat_intelligence import (
    CisaKevInformation,
    CvssInformation,
    EpssInformation,
    ExploitationEvidence,
    FindingThreatIntelligence,
    IntelligenceFact,
    NvdIntelligence,
    VulnerabilityThreatIntelligence,
)
from infrastructure import (
    CisaKevThreatIntelligenceReader,
    CompositeThreatIntelligenceReader,
    EpssThreatIntelligenceReader,
    NvdThreatIntelligenceReader,
    OpenAIFindingExplanationModel,
)
from settings import (
    AI_FINDING_EXPLANATION_ALLOWED_IDS,
    AI_MODEL_SELECTION_AUDIT_PATH,
    AI_MODEL_SELECTION_STATE_PATH,
    ASSET_CONTEXT_PATH,
    GREENBONE_REPORT_PATH,
    INCIDENT_CONTEXT_PATH,
    HUNT_HYPOTHESIS_REPOSITORY_PATH,
    HUNT_HYPOTHESIS_ACTIVATION_AUDIT_PATH,
    LOCAL_OPERATOR_ALLOWED_ORIGINS,
    LOCAL_OPERATOR_DISPLAY_NAME,
    LOCAL_OPERATOR_MODE_ENABLED,
    LOCAL_OPERATOR_PERMISSIONS,
    LOCAL_OPERATOR_PRINCIPAL_ID,
    LOCAL_OPERATOR_TOKEN,
    LOCAL_OPERATOR_SESSION_COOKIE_NAME,
    LOCAL_OPERATOR_SESSION_COOKIE_SECURE,
    LOCAL_OPERATOR_SESSION_ENABLED,
    LOCAL_OPERATOR_SESSION_LIFETIME_SECONDS,
    OPENAI_API_KEY,
    OPENAI_FINDING_EXPLANATION_MODEL,
)

app = FastAPI(
    title="Cyber Risk Brain",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        configured_local_operator_origins(LOCAL_OPERATOR_ALLOWED_ORIGINS)
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

engine = PredatorEngine()


class FindingResponse(BaseModel):
    id: str
    source: str
    title: str
    vendorSeverity: str
    asset: str


class FindingRiskSourceFactResponse(BaseModel):
    name: str
    value: str
    source_reference: str


class FindingRiskAssetContextResponse(BaseModel):
    status: str
    observed_identifier_type: str | None
    observed_identifier_value: str | None
    canonical_asset_id: str | None
    criticality: str | None
    source_reference: str | None


class FindingRiskEvidenceResponse(BaseModel):
    identifier: str
    kind: str
    evidence_type: str
    contract_version: str
    source_type: str
    source_reference: str
    input_references: list[str]


class FindingRiskInputResponse(BaseModel):
    name: str
    state: str
    value: str | bool | None
    source: str | None


class FindingRiskAssessmentResponse(BaseModel):
    status: str
    available_inputs: list[FindingRiskInputResponse]
    missing_inputs: list[FindingRiskInputResponse]
    score: int | None


class FindingEvidenceReadinessResponse(BaseModel):
    status: str
    reason: str
    considered_evidence_ids: list[str]
    referenced_input_references: list[str]
    missing_requirements: list[str]
    completeness_status: str
    source_type: str
    source_reference: str


class FindingCorrelationResponse(BaseModel):
    completeness_status: str
    source_type: str
    source_reference: str


class HuntHypothesisReferenceResponse(BaseModel):
    reference_type: str
    reference_id: str


class HuntHypothesisResponse(BaseModel):
    hypothesis_id: str
    title: str
    statement: str
    status: str
    created_at: datetime
    created_by: str
    target_references: list[HuntHypothesisReferenceResponse]
    threat_references: list[HuntHypothesisReferenceResponse]
    rationale: str
    contract_version: str


class HuntHypothesisTargetReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_type: Literal["asset", "service", "finding"]
    reference_id: str


class HuntHypothesisThreatReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_type: Literal["cve", "threat_intelligence", "technique", "tactic"]
    reference_id: str


class HuntHypothesisCreationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    statement: str
    rationale: str
    target_references: list[HuntHypothesisTargetReferenceRequest]
    threat_references: list[HuntHypothesisThreatReferenceRequest]


class HuntHypothesisActivationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_status: Literal["draft"]


class HuntHypothesisResolvedReferenceResponse(BaseModel):
    reference_type: str
    reference_id: str
    resolution_status: str
    authoritative_source: str | None
    resolved_identity: str | None
    source_reference: str | None


class HuntHypothesisReferenceResolutionResponse(BaseModel):
    hypothesis_id: str
    references: list[HuntHypothesisResolvedReferenceResponse]


class LocalOperatorResponse(BaseModel):
    principal_id: str
    display_name: str
    principal_type: str
    granted_permissions: list[str]


class LocalOperatorSessionResponse(LocalOperatorResponse):
    expires_at: datetime
    csrf_token: str


class AIModelCapabilityVisibilityResponse(BaseModel):
    capability: str
    authorized: bool
    adapter_available: bool
    execution_available: bool
    active: bool


class AIModelRegistrationVisibilityResponse(BaseModel):
    provider: str
    model_id: str
    api_protocol_family: str
    deployment_class: str
    policy_reference: str
    execution_binding: str
    status: str
    governance_status: str
    capabilities: list[AIModelCapabilityVisibilityResponse]


class AIProviderGovernanceVisibilityResponse(BaseModel):
    provider: str
    governance_status: str
    registrations: list[AIModelRegistrationVisibilityResponse]


class AIModelGovernanceVisibilityResponse(BaseModel):
    contract_version: str
    capabilities: list[str]
    providers: list[AIProviderGovernanceVisibilityResponse]


class AIModelSelectionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_id: str


class FindingExplanationFactResponse(BaseModel):
    fact_id: str
    value: str
    source_reference: str | None


class FindingExplanationMissingContextResponse(BaseModel):
    name: str
    state: str


class FindingExplanationStatementResponse(BaseModel):
    kind: str
    text: str
    basis_fact_ids: list[str]


class FindingExplanationModelOutputResponse(BaseModel):
    summary: FindingExplanationStatementResponse
    technical_reasoning: list[FindingExplanationStatementResponse]
    organizational_relevance: list[FindingExplanationStatementResponse]
    uncertainty_statement: FindingExplanationStatementResponse


class FindingExplanationResponse(BaseModel):
    finding_id: str
    generation_status: str
    factual_context: list[FindingExplanationFactResponse]
    missing_context: list[FindingExplanationMissingContextResponse]
    provider_id: str | None
    model_id: str | None
    execution_binding_version: str | None
    selection_purpose: str | None
    selection_policy_reference: str | None
    input_contract_version: str
    input_digest: str
    used_fact_ids: list[str]
    source_references: list[str]
    model_output: FindingExplanationModelOutputResponse | None


class ThreatIntelligenceProvenanceResponse(BaseModel):
    source_type: str
    source_reference: str


class ThreatIntelligenceFactResponse(BaseModel):
    status: str
    provenance: ThreatIntelligenceProvenanceResponse
    observed_at: datetime | None


class NvdIntelligenceValueResponse(BaseModel):
    summary: str | None
    published_at: datetime | None
    last_modified_at: datetime | None


class NvdIntelligenceFactResponse(ThreatIntelligenceFactResponse):
    value: NvdIntelligenceValueResponse | None


class CvssInformationValueResponse(BaseModel):
    version: str
    base_score: float
    vector: str
    severity: str | None


class CvssInformationFactResponse(ThreatIntelligenceFactResponse):
    value: CvssInformationValueResponse | None


class EpssInformationValueResponse(BaseModel):
    probability: float
    percentile: float | None


class EpssInformationFactResponse(ThreatIntelligenceFactResponse):
    value: EpssInformationValueResponse | None


class CisaKevInformationValueResponse(BaseModel):
    known_exploited: bool
    date_added: date | None
    required_action: str | None
    due_date: date | None


class CisaKevInformationFactResponse(ThreatIntelligenceFactResponse):
    value: CisaKevInformationValueResponse | None


class ExploitationEvidenceResponse(BaseModel):
    evidence_type: str
    description: str
    provenance: ThreatIntelligenceProvenanceResponse
    observed_at: datetime | None


class ExploitationEvidenceFactResponse(ThreatIntelligenceFactResponse):
    value: list[ExploitationEvidenceResponse] | None


class VulnerabilityThreatIntelligenceResponse(BaseModel):
    contract_version: str
    cve_identifier: str
    nvd: NvdIntelligenceFactResponse
    cvss: CvssInformationFactResponse
    epss: EpssInformationFactResponse
    cisa_kev: CisaKevInformationFactResponse
    exploitation_evidence: ExploitationEvidenceFactResponse


class FindingThreatIntelligenceRelationshipResponse(BaseModel):
    applicability: str
    cve_identifier: str | None
    intelligence: VulnerabilityThreatIntelligenceResponse | None


class FindingThreatIntelligenceEnrichmentResponse(BaseModel):
    finding_id: str
    finding_source: str
    finding_title: str
    relationships: list[FindingThreatIntelligenceRelationshipResponse]


class FindingRiskContextResponse(BaseModel):
    finding_id: str
    source_facts: list[FindingRiskSourceFactResponse]
    asset_context: FindingRiskAssetContextResponse
    threat_intelligence: FindingThreatIntelligenceEnrichmentResponse
    correlation: FindingCorrelationResponse
    evidence: list[FindingRiskEvidenceResponse]
    risk_inputs: list[FindingRiskInputResponse]
    assessment: FindingRiskAssessmentResponse
    evidence_readiness: FindingEvidenceReadinessResponse
    refusal_reason: str | None
    priority: None
    business_impact: None
    decision: None
    recommendations: list[None]


class IncidentPrincipalResponse(BaseModel):
    principal_type: str
    principal_id: str


class IncidentParticipantResponse(BaseModel):
    principal: IncidentPrincipalResponse
    role: str


class IncidentContextResponse(BaseModel):
    incident_id: str
    lifecycle_status: str
    source: str
    source_reference: str
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    owner: IncidentPrincipalResponse | None
    participants: list[IncidentParticipantResponse]


class IncidentQueueItemResponse(BaseModel):
    incident_id: str
    lifecycle_status: str
    source: str
    source_reference: str
    title: str
    created_at: datetime
    updated_at: datetime
    owner: IncidentPrincipalResponse | None
    participant_count: int
    finding_count: int
    asset_count: int
    threat_intelligence_count: int
    evidence_count: int


class IncidentReferenceResponse(BaseModel):
    reference_id: str
    source: str | None = None
    contract_version: str | None = None
    version_id: str | None = None
    evidence_snapshot_id: str | None = None


class FindingIncidentReferenceResponse(BaseModel):
    incident_id: str
    relationship_id: str
    relationship_role: str
    lifecycle_status: str


class IncidentProjectionSectionResponse(BaseModel):
    section: str
    status: str
    reference_ids: list[str]
    source_references: list[str]
    missing_context: list[str]


class IncidentCompletenessResponse(BaseModel):
    status: str
    source_type: str
    source_reference: str


class IncidentActivityDetailResponse(BaseModel):
    detail_type: str
    value: str


class IncidentActivityResponse(BaseModel):
    activity_id: str
    incident_id: str
    activity_type: str
    actor: IncidentPrincipalResponse
    occurred_at: datetime
    sequence: int
    description: str
    details: list[IncidentActivityDetailResponse]
    contract_version: str


class AnalystNoteResponse(BaseModel):
    note_id: str
    note_version_id: str
    incident_id: str
    author: IncidentPrincipalResponse
    content: str
    created_at: datetime
    version: int
    supersedes_version_id: str | None
    contract_version: str


class IncidentCommandCenterResponse(BaseModel):
    contract_version: str
    incident: IncidentContextResponse
    findings: list[IncidentReferenceResponse]
    assets: list[IncidentReferenceResponse]
    threat_intelligence: list[IncidentReferenceResponse]
    evidence: list[IncidentReferenceResponse]
    decisions: list[IncidentReferenceResponse]
    notes: list[AnalystNoteResponse]
    activities: list[IncidentActivityResponse]
    sections: list[IncidentProjectionSectionResponse]
    completeness: IncidentCompletenessResponse
    missing_context: list[str]


def get_findings_query_service() -> FindingsQueryService:
    return FindingsQueryService(GREENBONE_REPORT_PATH)


def get_hunt_hypothesis_query_service() -> HuntHypothesisQueryService:
    return HuntHypothesisQueryService(
        FileHuntHypothesisRepository(HUNT_HYPOTHESIS_REPOSITORY_PATH)
    )


def get_hunt_hypothesis_creation_service() -> HuntHypothesisCreationService:
    return HuntHypothesisCreationService(
        FileHuntHypothesisRepository(HUNT_HYPOTHESIS_REPOSITORY_PATH)
    )


def get_hunt_hypothesis_activation_service() -> HuntHypothesisActivationService:
    return HuntHypothesisActivationService(
        FileHuntHypothesisRepository(HUNT_HYPOTHESIS_REPOSITORY_PATH),
        FileHuntHypothesisActivationAuditSink(
            HUNT_HYPOTHESIS_ACTIVATION_AUDIT_PATH
        ),
    )


def get_hunt_hypothesis_activation_attempt_auditor(
) -> HuntHypothesisActivationAttemptAuditor:
    return HuntHypothesisActivationAttemptAuditor(
        FileHuntHypothesisActivationAuditSink(
            HUNT_HYPOTHESIS_ACTIVATION_AUDIT_PATH
        )
    )


def get_local_operator_authenticator() -> LocalOperatorAuthenticator:
    try:
        return LocalOperatorAuthenticator.from_values(
            mode_enabled=LOCAL_OPERATOR_MODE_ENABLED,
            principal_id=LOCAL_OPERATOR_PRINCIPAL_ID,
            display_name=LOCAL_OPERATOR_DISPLAY_NAME,
            token=LOCAL_OPERATOR_TOKEN,
            permissions=LOCAL_OPERATOR_PERMISSIONS,
            allowed_origins=LOCAL_OPERATOR_ALLOWED_ORIGINS,
        )
    except LocalOperatorConfigurationUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail="Local Operator mode is not configured.",
        ) from error
    except LocalOperatorConfigurationIntegrityError as error:
        raise HTTPException(
            status_code=500,
            detail="Local Operator configuration is invalid.",
        ) from error


_local_operator_session_store: LocalOperatorSessionStore | None = None
_local_operator_session_store_lock = threading.Lock()


def get_local_operator_session_store() -> LocalOperatorSessionStore:
    global _local_operator_session_store
    if _local_operator_session_store is not None:
        return _local_operator_session_store
    with _local_operator_session_store_lock:
        if _local_operator_session_store is not None:
            return _local_operator_session_store
        try:
            configuration = LocalOperatorSessionConfiguration.from_values(
                enabled=LOCAL_OPERATOR_SESSION_ENABLED,
                lifetime_seconds=LOCAL_OPERATOR_SESSION_LIFETIME_SECONDS,
                cookie_secure=LOCAL_OPERATOR_SESSION_COOKIE_SECURE,
                cookie_name=LOCAL_OPERATOR_SESSION_COOKIE_NAME,
                allowed_origins=configured_local_operator_origins(
                    LOCAL_OPERATOR_ALLOWED_ORIGINS
                ),
            )
            _local_operator_session_store = LocalOperatorSessionStore(configuration)
            return _local_operator_session_store
        except LocalOperatorConfigurationUnavailableError as error:
            raise HTTPException(
                status_code=503,
                detail="Local Operator browser sessions are not configured.",
            ) from error
        except LocalOperatorConfigurationIntegrityError as error:
            raise HTTPException(
                status_code=500,
                detail="Local Operator browser session configuration is invalid.",
            ) from error


def _configured_session_principal(
    authenticator: LocalOperatorAuthenticator,
) -> AuthenticatedPrincipal:
    return authenticator.configured_principal()


def _session_cookie_candidates(
    request: Request, store: LocalOperatorSessionStore
) -> tuple[str, ...]:
    cookie_name = store.configuration.cookie_name
    candidates: list[str] = []
    for cookie_header in request.headers.getlist("cookie"):
        for item in cookie_header.split(";"):
            name, separator, value = item.strip().partition("=")
            if separator and name == cookie_name and value:
                candidates.append(value)
    return tuple(candidates)


def _require_loopback_bootstrap(request: Request) -> None:
    client_host = request.client.host if request.client is not None else None
    if client_host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="Bootstrap access is forbidden.")
    if request.headers.get("host") != LOCAL_OPERATOR_BACKEND_HOST:
        raise HTTPException(status_code=403, detail="Bootstrap access is forbidden.")


def get_browser_session_principal(
    request: Request,
    authenticator: LocalOperatorAuthenticator = Depends(
        get_local_operator_authenticator
    ),
    store: LocalOperatorSessionStore = Depends(get_local_operator_session_store),
) -> tuple[AuthenticatedPrincipal, LocalOperatorBrowserSession, str]:
    principal = _configured_session_principal(authenticator)
    candidates = _session_cookie_candidates(request, store)
    try:
        session_id, session = store.resolve_candidates(
            candidates, principal
        )
    except LocalOperatorSessionAuthenticationError as error:
        raise HTTPException(
            status_code=401,
            detail="Local Operator browser session authentication failed.",
        ) from error
    return principal, session, session_id


def get_creation_principal(
    request: Request,
    authorization: str | None = Header(default=None),
    origin: str | None = Header(default=None),
    csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    authenticator: LocalOperatorAuthenticator = Depends(
        get_local_operator_authenticator
    ),
) -> AuthenticatedPrincipal:
    if authorization is not None:
        try:
            return authenticator.authenticate(authorization)
        except LocalOperatorAuthenticationError as error:
            raise HTTPException(
                status_code=401,
                detail="Local Operator authentication failed.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
    if not request.headers.get("cookie"):
        raise HTTPException(
            status_code=401,
            detail="Local Operator authentication failed.",
        )
    store = get_local_operator_session_store()
    principal = _configured_session_principal(authenticator)
    try:
        session_id, _ = store.resolve_candidates(
            _session_cookie_candidates(request, store), principal
        )
        store.require_mutation(
            session_id,
            principal,
            origin=origin,
            csrf_token=csrf_token,
        )
    except LocalOperatorSessionAuthenticationError as error:
        raise HTTPException(
            status_code=401,
            detail="Local Operator browser session authentication failed.",
        ) from error
    except LocalOperatorSessionCsrfError as error:
        raise HTTPException(
            status_code=403,
            detail="Local Operator request verification failed.",
        ) from error
    return principal


def get_activation_principal(
    request: Request,
    origin: str | None = Header(default=None),
    csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    authenticator: LocalOperatorAuthenticator = Depends(
        get_local_operator_authenticator
    ),
    auditor: HuntHypothesisActivationAttemptAuditor = Depends(
        get_hunt_hypothesis_activation_attempt_auditor
    ),
) -> AuthenticatedPrincipal:
    request.state.activation_auditor = auditor
    if not request.headers.get("cookie"):
        _audit_activation_http_rejection(
            auditor,
            hypothesis_id=request.path_params.get("hypothesis_id"),
            principal_id=None,
            reason="authentication_required",
        )
        raise HTTPException(
            status_code=401,
            detail="Local Operator browser session authentication failed.",
        )
    store = get_local_operator_session_store()
    principal = _configured_session_principal(authenticator)
    try:
        session_id, _ = store.resolve_candidates(
            _session_cookie_candidates(request, store), principal
        )
        store.require_mutation(
            session_id,
            principal,
            origin=origin,
            csrf_token=csrf_token,
        )
    except LocalOperatorSessionAuthenticationError as error:
        _audit_activation_http_rejection(
            auditor,
            hypothesis_id=request.path_params.get("hypothesis_id"),
            principal_id=None,
            reason="session_authentication_failed",
        )
        raise HTTPException(
            status_code=401,
            detail="Local Operator browser session authentication failed.",
        ) from error
    except LocalOperatorSessionCsrfError as error:
        _audit_activation_http_rejection(
            auditor,
            hypothesis_id=request.path_params.get("hypothesis_id"),
            principal_id=principal.principal_id,
            reason="request_verification_failed",
            authorization_outcome="not_evaluated",
        )
        raise HTTPException(
            status_code=403,
            detail="Local Operator request verification failed.",
        ) from error
    request.state.activation_principal_id = principal.principal_id
    return principal


def _audit_activation_http_rejection(
    auditor: HuntHypothesisActivationAttemptAuditor,
    *,
    hypothesis_id: str | None,
    principal_id: str | None,
    reason: str,
    authorization_outcome: str = "not_evaluated",
) -> None:
    try:
        auditor.reject(
            hypothesis_id=safe_hypothesis_audit_id(hypothesis_id),
            principal_id=principal_id,
            reason=reason,
            expected_status=None,
            authorization_outcome=authorization_outcome,
        )
    except HuntHypothesisActivationAuditError as error:
        raise HTTPException(
            status_code=503,
            detail="Hunt Hypothesis activation is unavailable.",
        ) from error


@app.exception_handler(RequestValidationError)
async def audit_activation_request_validation_failure(
    request: Request,
    error: RequestValidationError,
):
    if (
        request.method == "POST"
        and request.url.path.startswith("/api/hunt-hypotheses/")
        and request.url.path.endswith("/activation")
    ):
        try:
            auditor = getattr(request.state, "activation_auditor", None)
            if auditor is None:
                auditor = get_hunt_hypothesis_activation_attempt_auditor()
            auditor.reject(
                hypothesis_id=safe_hypothesis_audit_id(
                    request.path_params.get("hypothesis_id")
                ),
                principal_id=getattr(
                    request.state, "activation_principal_id", None
                ),
                reason="invalid_request_schema",
                authorization_outcome="not_evaluated",
            )
        except HuntHypothesisActivationAuditError:
            return JSONResponse(
                status_code=503,
                content={"detail": "Hunt Hypothesis activation is unavailable."},
            )
    return await request_validation_exception_handler(request, error)


def get_authenticated_local_operator(
    authorization: str | None = Header(default=None),
    authenticator: LocalOperatorAuthenticator = Depends(
        get_local_operator_authenticator
    ),
) -> AuthenticatedPrincipal:
    try:
        return authenticator.authenticate(authorization)
    except LocalOperatorAuthenticationError as error:
        raise HTTPException(
            status_code=401,
            detail="Local Operator authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_hunt_hypothesis_create_authority(
    principal: AuthenticatedPrincipal = Depends(get_authenticated_local_operator),
) -> AuthenticatedPrincipal:
    try:
        HuntHypothesisWriteAuthority().require(principal)
    except LocalOperatorAuthorizationError as error:
        raise HTTPException(
            status_code=403,
            detail="The authenticated operator is not authorized.",
        ) from error
    return principal


def get_hunt_hypothesis_reference_resolution_service(
) -> HuntHypothesisReferenceResolutionService:
    return HuntHypothesisReferenceResolutionService(
        hypotheses=get_hunt_hypothesis_query_service(),
        findings=FindingsQueryService(GREENBONE_REPORT_PATH),
        assets=AssetContextQueryService(ASSET_CONTEXT_PATH),
        threat_intelligence=get_threat_intelligence_query_service(),
    )


def _hunt_hypothesis_reference_response(
    reference: HuntHypothesisReference,
) -> HuntHypothesisReferenceResponse:
    return HuntHypothesisReferenceResponse(
        reference_type=reference.reference_type.value,
        reference_id=reference.reference_id,
    )


def _hunt_hypothesis_response(
    hypothesis: HuntHypothesis,
) -> HuntHypothesisResponse:
    return HuntHypothesisResponse(
        hypothesis_id=hypothesis.hypothesis_id,
        title=hypothesis.title,
        statement=hypothesis.statement,
        status=hypothesis.status.value,
        created_at=hypothesis.created_at,
        created_by=hypothesis.created_by,
        target_references=[
            _hunt_hypothesis_reference_response(reference)
            for reference in hypothesis.target_references
        ],
        threat_references=[
            _hunt_hypothesis_reference_response(reference)
            for reference in hypothesis.threat_references
        ],
        rationale=hypothesis.rationale,
        contract_version=hypothesis.contract_version,
    )


def _hunt_hypothesis_reference_resolution_response(
    result: HuntHypothesisReferenceResolutionResult,
) -> HuntHypothesisReferenceResolutionResponse:
    return HuntHypothesisReferenceResolutionResponse(
        hypothesis_id=result.hypothesis_id,
        references=[
            HuntHypothesisResolvedReferenceResponse(
                reference_type=item.reference_type.value,
                reference_id=item.reference_id,
                resolution_status=item.resolution_status.value,
                authoritative_source=item.authoritative_source,
                resolved_identity=item.resolved_identity,
                source_reference=item.source_reference,
            )
            for item in result.references
        ],
    )


def get_finding_explanation_use_case() -> FindingExplanationUseCase:
    allowed_finding_ids = frozenset(
        item.strip()
        for item in (AI_FINDING_EXPLANATION_ALLOWED_IDS or "").split(",")
        if item.strip()
    )
    return FindingExplanationUseCase(
        FindingsQueryService(GREENBONE_REPORT_PATH),
        AssetContextQueryService(ASSET_CONTEXT_PATH),
        RiskReadinessService(),
        FindingExplanationService(
            OpenAIFindingExplanationModel.from_settings(),
            model_selection_policy=PersistedAIModelSelectionPolicy(
                get_ai_model_selection_service()
            ),
        ),
        authorization_scope_factory=lambda finding_id: (
            build_finding_explanation_authorization(
                finding_id,
                allowed_finding_ids,
            )
        ),
    )


def _ai_model_bindings() -> tuple[
    frozenset[AIModelAdapterBinding],
    frozenset[AIModelAdapterBinding],
]:
    openai_binding = AIModelAdapterBinding(
        provider=AIProviderFamily.OPENAI,
        model_id=SUPPORTED_MODEL_ID,
        capability=AIModelCapability.FINDING_EXPLANATION,
    )
    execution_bindings = (
        frozenset({openai_binding})
        if isinstance(OPENAI_API_KEY, str)
        and bool(OPENAI_API_KEY.strip())
        and OPENAI_FINDING_EXPLANATION_MODEL == SUPPORTED_MODEL_ID
        else frozenset()
    )
    return frozenset({openai_binding}), execution_bindings


def get_ai_model_selection_store() -> FileAIModelSelectionStore:
    return FileAIModelSelectionStore(AI_MODEL_SELECTION_STATE_PATH)


def get_ai_model_selection_service() -> AIModelSelectionService:
    adapter_bindings, execution_bindings = _ai_model_bindings()
    return AIModelSelectionService(
        default_ai_model_registry(),
        get_ai_model_selection_store(),
        FileAIModelSelectionAuditSink(AI_MODEL_SELECTION_AUDIT_PATH),
        adapter_bindings=adapter_bindings,
        execution_bindings=execution_bindings,
    )


def get_ai_model_governance_query_service() -> AIModelGovernanceQueryService:
    adapter_bindings, execution_bindings = _ai_model_bindings()
    return AIModelGovernanceQueryService(
        adapter_bindings=adapter_bindings,
        execution_bindings=execution_bindings,
        selection_store=get_ai_model_selection_store(),
    )


def get_composite_threat_intelligence_reader() -> (
    CompositeThreatIntelligenceReader
):
    return CompositeThreatIntelligenceReader(
        nvd_reader=NvdThreatIntelligenceReader.from_settings(),
        epss_reader=EpssThreatIntelligenceReader.from_settings(),
        cisa_kev_reader=CisaKevThreatIntelligenceReader.from_settings(),
    )


def get_threat_intelligence_query_service() -> ThreatIntelligenceQueryService:
    return ThreatIntelligenceQueryService(
        reader=get_composite_threat_intelligence_reader()
    )


def get_finding_threat_intelligence_use_case() -> (
    FindingThreatIntelligenceUseCase
):
    return FindingThreatIntelligenceUseCase(
        findings=FindingsQueryService(GREENBONE_REPORT_PATH),
        reader=get_composite_threat_intelligence_reader(),
    )


def get_finding_risk_context_use_case() -> FindingRiskContextUseCase:
    findings = FindingsQueryService(GREENBONE_REPORT_PATH)
    asset_context = FindingAssetContextUseCase(
        findings=findings,
        asset_contexts=AssetContextQueryService(ASSET_CONTEXT_PATH),
    )
    threat_intelligence = FindingThreatIntelligenceUseCase(
        findings=findings,
        reader=get_composite_threat_intelligence_reader(),
    )
    correlation = SecurityObservationCorrelationApplicationService(
        finding_threat_intelligence=threat_intelligence,
        finding_asset_context=asset_context,
        correlation=SecurityObservationCorrelationService(),
    )
    return FindingRiskContextUseCase(
        findings=findings,
        asset_context=asset_context,
        threat_intelligence=threat_intelligence,
        correlation=correlation,
        risk_readiness=RiskReadinessService(),
        evidence_readiness=RiskAssessmentReadinessService(),
    )


def get_incident_command_center_query_service() -> IncidentCommandCenterQueryService:
    return IncidentCommandCenterQueryService(
        reference_resolver=IncidentReferenceResolutionService(
            findings=FindingsQueryService(GREENBONE_REPORT_PATH),
            assets=AssetContextQueryService(ASSET_CONTEXT_PATH),
            threat_intelligence=get_threat_intelligence_query_service(),
        )
    )


def get_security_incident_context_reader() -> Callable[
    [str], SecurityIncidentContext | None
]:
    return FileIncidentContextRepository(INCIDENT_CONTEXT_PATH).get


def get_incident_queue_query_service() -> IncidentQueueQueryService:
    return IncidentQueueQueryService(
        FileIncidentContextRepository(INCIDENT_CONTEXT_PATH)
    )


def get_finding_incident_query_service() -> FindingIncidentQueryService:
    return FindingIncidentQueryService(
        FileIncidentContextRepository(INCIDENT_CONTEXT_PATH)
    )


def _principal_response(
    principal: IncidentPrincipalReference,
) -> IncidentPrincipalResponse:
    return IncidentPrincipalResponse(
        principal_type=principal.principal_type.value,
        principal_id=principal.principal_id,
    )


def _incident_context_response(
    incident: SecurityIncidentContext,
) -> IncidentContextResponse:
    return IncidentContextResponse(
        incident_id=incident.incident_id,
        lifecycle_status=incident.lifecycle_status.value,
        source=incident.source,
        source_reference=incident.source_reference,
        title=incident.title,
        description=incident.description,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        owner=(
            _principal_response(incident.owner)
            if incident.owner is not None
            else None
        ),
        participants=[
            IncidentParticipantResponse(
                principal=_principal_response(participant.principal),
                role=participant.role.value,
            )
            for participant in incident.participants
        ],
    )


def _incident_queue_item_response(item) -> IncidentQueueItemResponse:
    incident = item.incident
    return IncidentQueueItemResponse(
        incident_id=incident.incident_id,
        lifecycle_status=incident.lifecycle_status.value,
        source=incident.source,
        source_reference=incident.source_reference,
        title=incident.title,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        owner=(
            _principal_response(incident.owner)
            if incident.owner is not None
            else None
        ),
        participant_count=item.participant_count,
        finding_count=item.finding_count,
        asset_count=item.asset_count,
        threat_intelligence_count=item.threat_intelligence_count,
        evidence_count=item.evidence_count,
    )


def _reference_response(reference: object) -> IncidentReferenceResponse:
    if isinstance(reference, FindingReference):
        return IncidentReferenceResponse(
            reference_id=reference.finding_id,
            source=reference.source,
        )
    if isinstance(reference, CanonicalAssetReference):
        return IncidentReferenceResponse(reference_id=reference.canonical_asset_id)
    if isinstance(reference, ThreatIntelligenceReference):
        return IncidentReferenceResponse(
            reference_id=reference.reference_id,
            contract_version=reference.contract_version,
        )
    if isinstance(reference, EvidenceReference):
        return IncidentReferenceResponse(
            reference_id=reference.evidence_id,
            contract_version=reference.contract_version,
        )
    if isinstance(reference, DecisionVersionReference):
        return IncidentReferenceResponse(
            reference_id=reference.decision_id,
            version_id=reference.version_id,
            evidence_snapshot_id=reference.evidence_snapshot_id,
        )
    raise ValueError("Unsupported incident reference.")


def _activity_response(activity: IncidentActivity) -> IncidentActivityResponse:
    return IncidentActivityResponse(
        activity_id=activity.activity_id,
        incident_id=activity.incident_id,
        activity_type=activity.activity_type.value,
        actor=_principal_response(activity.actor),
        occurred_at=activity.occurred_at,
        sequence=activity.sequence,
        description=activity.description,
        details=[
            IncidentActivityDetailResponse(
                detail_type=detail.detail_type.value,
                value=detail.value,
            )
            for detail in activity.details
        ],
        contract_version=activity.contract_version,
    )


def _note_response(note: AnalystNote) -> AnalystNoteResponse:
    return AnalystNoteResponse(
        note_id=note.note_id,
        note_version_id=note.note_version_id,
        incident_id=note.incident_id,
        author=_principal_response(note.author),
        content=note.content,
        created_at=note.created_at,
        version=note.version,
        supersedes_version_id=note.supersedes_version_id,
        contract_version=note.contract_version,
    )


def _incident_command_center_response(
    projection,
) -> IncidentCommandCenterResponse:
    return IncidentCommandCenterResponse(
        contract_version=projection.contract_version,
        incident=_incident_context_response(projection.incident),
        findings=[_reference_response(item) for item in projection.findings],
        assets=[_reference_response(item) for item in projection.assets],
        threat_intelligence=[
            _reference_response(item) for item in projection.threat_intelligence
        ],
        evidence=[_reference_response(item) for item in projection.evidence],
        decisions=[_reference_response(item) for item in projection.decisions],
        notes=[_note_response(item) for item in projection.notes],
        activities=[_activity_response(item) for item in projection.activities],
        sections=[
            IncidentProjectionSectionResponse(
                section=section.section.value,
                status=section.status.value,
                reference_ids=list(section.reference_ids),
                source_references=list(section.source_references),
                missing_context=list(section.missing_context),
            )
            for section in projection.sections
        ],
        completeness=IncidentCompletenessResponse(
            status=projection.completeness.status.value,
            source_type=projection.completeness.provenance.source_type,
            source_reference=projection.completeness.provenance.source_reference,
        ),
        missing_context=list(projection.missing_context),
    )


def _ti_provenance_response(
    provenance: ExplanationProvenance,
) -> ThreatIntelligenceProvenanceResponse:
    return ThreatIntelligenceProvenanceResponse(
        source_type=provenance.source_type,
        source_reference=provenance.source_reference,
    )


def _ti_fact_fields(fact: IntelligenceFact[object]) -> dict[str, object]:
    return {
        "status": fact.completeness.status.value,
        "provenance": _ti_provenance_response(fact.provenance),
        "observed_at": fact.observed_at,
    }


def _nvd_fact_response(
    fact: IntelligenceFact[NvdIntelligence],
) -> NvdIntelligenceFactResponse:
    value = fact.value
    return NvdIntelligenceFactResponse(
        **_ti_fact_fields(fact),
        value=(
            NvdIntelligenceValueResponse(
                summary=value.summary,
                published_at=value.published_at,
                last_modified_at=value.last_modified_at,
            )
            if value is not None
            else None
        ),
    )


def _cvss_fact_response(
    fact: IntelligenceFact[CvssInformation],
) -> CvssInformationFactResponse:
    value = fact.value
    return CvssInformationFactResponse(
        **_ti_fact_fields(fact),
        value=(
            CvssInformationValueResponse(
                version=value.version,
                base_score=value.base_score,
                vector=value.vector,
                severity=value.severity,
            )
            if value is not None
            else None
        ),
    )


def _epss_fact_response(
    fact: IntelligenceFact[EpssInformation],
) -> EpssInformationFactResponse:
    value = fact.value
    return EpssInformationFactResponse(
        **_ti_fact_fields(fact),
        value=(
            EpssInformationValueResponse(
                probability=value.probability,
                percentile=value.percentile,
            )
            if value is not None
            else None
        ),
    )


def _cisa_kev_fact_response(
    fact: IntelligenceFact[CisaKevInformation],
) -> CisaKevInformationFactResponse:
    value = fact.value
    return CisaKevInformationFactResponse(
        **_ti_fact_fields(fact),
        value=(
            CisaKevInformationValueResponse(
                known_exploited=value.known_exploited,
                date_added=value.date_added,
                required_action=value.required_action,
                due_date=value.due_date,
            )
            if value is not None
            else None
        ),
    )


def _exploitation_evidence_response(
    evidence: ExploitationEvidence,
) -> ExploitationEvidenceResponse:
    return ExploitationEvidenceResponse(
        evidence_type=evidence.evidence_type,
        description=evidence.description,
        provenance=_ti_provenance_response(evidence.provenance),
        observed_at=evidence.observed_at,
    )


def _exploitation_evidence_fact_response(
    fact: IntelligenceFact[tuple[ExploitationEvidence, ...]],
) -> ExploitationEvidenceFactResponse:
    return ExploitationEvidenceFactResponse(
        **_ti_fact_fields(fact),
        value=(
            [_exploitation_evidence_response(item) for item in fact.value]
            if fact.value is not None
            else None
        ),
    )


def _threat_intelligence_response(
    intelligence: VulnerabilityThreatIntelligence,
) -> VulnerabilityThreatIntelligenceResponse:
    return VulnerabilityThreatIntelligenceResponse(
        contract_version=intelligence.contract_version,
        cve_identifier=intelligence.cve_identifier.value,
        nvd=_nvd_fact_response(intelligence.nvd),
        cvss=_cvss_fact_response(intelligence.cvss),
        epss=_epss_fact_response(intelligence.epss),
        cisa_kev=_cisa_kev_fact_response(intelligence.cisa_kev),
        exploitation_evidence=_exploitation_evidence_fact_response(
            intelligence.exploitation_evidence
        ),
    )


def _finding_threat_intelligence_relationship_response(
    relationship: FindingThreatIntelligence,
) -> FindingThreatIntelligenceRelationshipResponse:
    vulnerability = relationship.vulnerability
    return FindingThreatIntelligenceRelationshipResponse(
        applicability=relationship.applicability.value,
        cve_identifier=(
            vulnerability.cve_identifier.value
            if vulnerability is not None
            else None
        ),
        intelligence=(
            _threat_intelligence_response(vulnerability)
            if vulnerability is not None
            else None
        ),
    )


def _finding_threat_intelligence_enrichment_response(
    enrichment: FindingThreatIntelligenceEnrichment,
) -> FindingThreatIntelligenceEnrichmentResponse:
    return FindingThreatIntelligenceEnrichmentResponse(
        finding_id=enrichment.finding_id,
        finding_source=enrichment.finding_source,
        finding_title=enrichment.finding_title,
        relationships=[
            _finding_threat_intelligence_relationship_response(relationship)
            for relationship in enrichment.relationships
        ],
    )


def _finding_risk_context_response(
    context: FindingRiskContext,
) -> FindingRiskContextResponse:
    resolution = context.asset_context
    observed = resolution.observed_identifier
    asset = resolution.asset_context
    risk_values = (
        ("business_criticality", context.risk_inputs.business_criticality),
        ("exposure", context.risk_inputs.exposure),
        ("detection_available", context.risk_inputs.detection_available),
        (
            "threat_intelligence_match",
            context.risk_inputs.threat_intelligence_match,
        ),
        ("mitre_tactic", context.risk_inputs.mitre_tactic),
    )
    readiness = context.evidence_readiness
    completeness = context.correlation.completeness
    return FindingRiskContextResponse(
        finding_id=context.finding_id,
        source_facts=[
            FindingRiskSourceFactResponse(
                name=fact.name,
                value=fact.value,
                source_reference=fact.source_reference,
            )
            for fact in context.source_facts
        ],
        asset_context=FindingRiskAssetContextResponse(
            status=resolution.status.value,
            observed_identifier_type=(
                observed.identifier_type.value if observed is not None else None
            ),
            observed_identifier_value=(observed.value if observed is not None else None),
            canonical_asset_id=(asset.canonical_asset_id if asset is not None else None),
            criticality=(asset.criticality.value if asset is not None else None),
            source_reference=(asset.source_reference if asset is not None else None),
        ),
        threat_intelligence=_finding_threat_intelligence_enrichment_response(
            context.threat_intelligence
        ),
        correlation=FindingCorrelationResponse(
            completeness_status=completeness.status.value,
            source_type=completeness.provenance.source_type,
            source_reference=completeness.provenance.source_reference,
        ),
        evidence=[_canonical_evidence_response(item) for item in context.evidence],
        risk_inputs=[
            FindingRiskInputResponse(
                name=name,
                state=value.state.value,
                value=(
                    value.value.value
                    if hasattr(value.value, "value")
                    else value.value
                ),
                source=value.source,
            )
            for name, value in risk_values
        ],
        assessment=FindingRiskAssessmentResponse(
            status=context.assessment.status.value,
            available_inputs=[
                FindingRiskInputResponse(
                    name=item.name,
                    state="AUTHORITATIVE",
                    value=item.value,
                    source=item.source,
                )
                for item in context.assessment.available_inputs
            ],
            missing_inputs=[
                FindingRiskInputResponse(
                    name=item.name,
                    state=item.state.value,
                    value=None,
                    source=None,
                )
                for item in context.assessment.missing_inputs
            ],
            score=context.assessment.score,
        ),
        evidence_readiness=FindingEvidenceReadinessResponse(
            status=readiness.status.value,
            reason=readiness.reason,
            considered_evidence_ids=list(readiness.considered_evidence_ids),
            referenced_input_references=list(readiness.referenced_input_references),
            missing_requirements=list(readiness.missing_requirements),
            completeness_status=readiness.completeness.status.value,
            source_type=readiness.completeness.provenance.source_type,
            source_reference=readiness.completeness.provenance.source_reference,
        ),
        refusal_reason=context.refusal_reason,
        priority=None,
        business_impact=None,
        decision=None,
        recommendations=[],
    )


def _canonical_evidence_response(
    evidence: Evidence,
) -> FindingRiskEvidenceResponse:
    if (
        evidence.identifier is None
        or evidence.kind is None
        or evidence.contract_version is None
        or evidence.provenance is None
    ):
        raise ValueError("Risk context contains incomplete canonical evidence.")
    return FindingRiskEvidenceResponse(
        identifier=evidence.identifier,
        kind=evidence.kind.value,
        evidence_type=evidence.evidence_type.value,
        contract_version=evidence.contract_version,
        source_type=evidence.provenance.source_type,
        source_reference=evidence.provenance.source_reference,
        input_references=list(evidence.provenance.input_references),
    )


def _statement_response(
    statement: FindingExplanationStatement,
) -> FindingExplanationStatementResponse:
    return FindingExplanationStatementResponse(
        kind=statement.kind.value,
        text=statement.text,
        basis_fact_ids=list(statement.basis_fact_ids),
    )


def _model_output_response(
    output: FindingExplanationModelOutput | None,
) -> FindingExplanationModelOutputResponse | None:
    if output is None:
        return None
    return FindingExplanationModelOutputResponse(
        summary=_statement_response(output.summary),
        technical_reasoning=[
            _statement_response(statement)
            for statement in output.technical_reasoning
        ],
        organizational_relevance=[
            _statement_response(statement)
            for statement in output.organizational_relevance
        ],
        uncertainty_statement=_statement_response(
            output.uncertainty_statement
        ),
    )


def _explanation_response(
    result: FindingExplanationResult,
) -> FindingExplanationResponse:
    return FindingExplanationResponse(
        finding_id=result.finding_id,
        generation_status=result.generation_status.value,
        factual_context=[
            FindingExplanationFactResponse(
                fact_id=fact.fact_id,
                value=fact.value,
                source_reference=fact.source_reference,
            )
            for fact in result.factual_context
        ],
        missing_context=[
            FindingExplanationMissingContextResponse(
                name=item.name,
                state=item.state.value,
            )
            for item in result.missing_context
        ],
        provider_id=result.provider_id,
        model_id=result.model_id,
        execution_binding_version=(
            result.selection_decision.execution_binding_version
            if result.selection_decision is not None
            else None
        ),
        selection_purpose=(
            result.selection_decision.purpose.value
            if result.selection_decision is not None
            else None
        ),
        selection_policy_reference=(
            result.selection_decision.selection_policy_reference
            if result.selection_decision is not None
            else None
        ),
        input_contract_version=result.input_contract_version,
        input_digest=result.input_digest,
        used_fact_ids=list(result.used_fact_ids),
        source_references=list(result.source_references),
        model_output=_model_output_response(result.model_output),
    )


@app.get("/")
def root():
    return {
        "status": "Cyber Risk Brain Online",
        "engine": "PredatorAI v2",
    }


@app.get("/api/analyze")
def analyze():

    return engine.run()


@app.get(
    "/api/ai-model-governance",
    response_model=AIModelGovernanceVisibilityResponse,
)
def ai_model_governance(
    service: AIModelGovernanceQueryService = Depends(
        get_ai_model_governance_query_service
    ),
) -> AIModelGovernanceVisibility:
    try:
        return service.get_visibility()
    except AIModelSelectionPersistenceError as error:
        raise HTTPException(
            status_code=500,
            detail="Governed model selection state is invalid.",
        ) from error


@app.put(
    "/api/ai-model-governance/selections/{capability}",
    response_model=AIModelGovernanceVisibilityResponse,
)
def update_ai_model_selection(
    capability: str,
    request: AIModelSelectionUpdateRequest,
    principal: AuthenticatedPrincipal = Depends(get_creation_principal),
    service: AIModelSelectionService = Depends(get_ai_model_selection_service),
    query: AIModelGovernanceQueryService = Depends(
        get_ai_model_governance_query_service
    ),
) -> AIModelGovernanceVisibility:
    try:
        governed_capability = AIModelCapability(capability)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Governed capability was not found.") from error
    try:
        service.change(
            governed_capability,
            request.provider,
            request.model_id,
            principal,
        )
    except LocalOperatorAuthorizationError as error:
        raise HTTPException(
            status_code=403,
            detail="The authenticated operator is not authorized.",
        ) from error
    except AIModelSelectionUnavailableError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except AIModelSelectionError as error:
        raise HTTPException(
            status_code=409,
            detail="The requested model selection is not governed.",
        ) from error
    except AIModelSelectionPersistenceError as error:
        raise HTTPException(
            status_code=503,
            detail="Governed model selection could not be persisted.",
        ) from error
    return query.get_visibility()


@app.get("/api/operator/me", response_model=LocalOperatorResponse)
def local_operator_me(
    principal: AuthenticatedPrincipal = Depends(get_authenticated_local_operator),
) -> LocalOperatorResponse:
    return LocalOperatorResponse(
        principal_id=principal.principal_id,
        display_name=principal.display_name,
        principal_type=principal.principal_type,
        granted_permissions=sorted(principal.permissions),
    )


_BOOTSTRAP_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>PredatorAI Local Operator</title></head>
<body>
<main>
<h1>PredatorAI Local Operator</h1>
<p>Authenticate this local browser session.</p>
<form method="post" action="/api/operator/session/bootstrap">
<label>Local Operator credential
<input type="password" name="credential" required autocomplete="current-password">
</label>
<button type="submit">Authenticate</button>
</form>
</main>
</body>
</html>"""


def _bootstrap_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "Content-Security-Policy": (
            "default-src 'none'; form-action 'self'; frame-ancestors 'none'; "
            "base-uri 'none'"
        ),
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
    }


@app.get("/api/operator/session/bootstrap", response_class=HTMLResponse)
def local_operator_session_bootstrap(request: Request) -> HTMLResponse:
    _require_loopback_bootstrap(request)
    return HTMLResponse(_BOOTSTRAP_HTML, headers=_bootstrap_headers())


@app.post("/api/operator/session/bootstrap")
async def create_local_operator_session(
    request: Request,
    authenticator: LocalOperatorAuthenticator = Depends(
        get_local_operator_authenticator
    ),
    store: LocalOperatorSessionStore = Depends(get_local_operator_session_store),
):
    _require_loopback_bootstrap(request)
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip()
    content_length = request.headers.get("content-length")
    if content_type != "application/x-www-form-urlencoded":
        raise HTTPException(status_code=415, detail="Unsupported content type.")
    if content_length is None or not content_length.isdigit() or int(content_length) > 4096:
        raise HTTPException(status_code=400, detail="Invalid bootstrap request.")
    body = await request.body()
    if len(body) > 4096:
        raise HTTPException(status_code=400, detail="Invalid bootstrap request.")
    try:
        fields = parse_qs(
            body.decode("utf-8"),
            keep_blank_values=True,
            strict_parsing=True,
        )
        if set(fields) != {"credential"} or len(fields["credential"]) != 1:
            raise ValueError("Invalid form fields.")
        credential = fields["credential"][0]
        principal = authenticator.authenticate(f"Bearer {credential}")
    except (UnicodeError, ValueError, LocalOperatorAuthenticationError):
        return PlainTextResponse(
            "Local Operator authentication failed.",
            status_code=401,
            headers=_bootstrap_headers(),
        )
    created = store.create(principal)
    response = RedirectResponse(
        f"{store.configuration.frontend_origin}/threat-hunting/hypotheses",
        status_code=303,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )
    response.set_cookie(
        key=store.configuration.cookie_name,
        value=created.session_id,
        max_age=store.configuration.lifetime_seconds,
        expires=created.expires_at,
        path="/",
        secure=store.configuration.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return response


@app.get("/api/operator/session", response_model=LocalOperatorSessionResponse)
def local_operator_session(
    request: Request,
    authenticated: tuple[
        AuthenticatedPrincipal, LocalOperatorBrowserSession, str
    ] = Depends(get_browser_session_principal),
    store: LocalOperatorSessionStore = Depends(get_local_operator_session_store),
) -> LocalOperatorSessionResponse:
    principal, _, session_id = authenticated
    session, csrf_token = store.issue_csrf(session_id, principal)
    return LocalOperatorSessionResponse(
        principal_id=principal.principal_id,
        display_name=principal.display_name,
        principal_type=principal.principal_type,
        granted_permissions=sorted(principal.permissions),
        expires_at=session.expires_at,
        csrf_token=csrf_token,
    )


@app.post("/api/operator/session/logout", status_code=204)
def logout_local_operator_session(
    request: Request,
    origin: str | None = Header(default=None),
    csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    authenticator: LocalOperatorAuthenticator = Depends(
        get_local_operator_authenticator
    ),
    store: LocalOperatorSessionStore = Depends(get_local_operator_session_store),
):
    principal = _configured_session_principal(authenticator)
    try:
        session_id, _ = store.resolve_candidates(
            _session_cookie_candidates(request, store), principal
        )
        store.require_mutation(
            session_id,
            principal,
            origin=origin,
            csrf_token=csrf_token,
        )
    except LocalOperatorSessionAuthenticationError as error:
        raise HTTPException(status_code=401, detail="Invalid browser session.") from error
    except LocalOperatorSessionCsrfError as error:
        raise HTTPException(status_code=403, detail="Request verification failed.") from error
    store.revoke(session_id)
    response = PlainTextResponse("", status_code=204)
    response.delete_cookie(
        store.configuration.cookie_name,
        path="/",
        secure=store.configuration.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return response


@app.get("/api/findings", response_model=list[FindingResponse])
def findings(
    service: FindingsQueryService = Depends(
        get_findings_query_service
    ),
) -> list[FindingResponse]:
    try:
        universal_findings = service.get_findings()
    except FindingsConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Configured Greenbone report could not be loaded.",
        ) from error

    return [
        FindingResponse(
            id=finding.id,
            source=finding.source,
            title=finding.title,
            vendorSeverity=finding.vendor_severity,
            asset=finding.asset,
        )
        for finding in universal_findings
    ]


@app.get(
    "/api/hunt-hypotheses",
    response_model=list[HuntHypothesisResponse],
)
def hunt_hypotheses(
    service: HuntHypothesisQueryService = Depends(
        get_hunt_hypothesis_query_service
    ),
) -> list[HuntHypothesisResponse]:
    try:
        return [_hunt_hypothesis_response(item) for item in service.list()]
    except HuntHypothesisConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except HuntHypothesisDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Hunt Hypothesis repository contains invalid data.",
        ) from error


@app.post(
    "/api/hunt-hypotheses",
    response_model=HuntHypothesisResponse,
    status_code=201,
)
def create_hunt_hypothesis(
    request: HuntHypothesisCreationRequest,
    principal: AuthenticatedPrincipal = Depends(get_creation_principal),
    service: HuntHypothesisCreationService = Depends(
        get_hunt_hypothesis_creation_service
    ),
) -> HuntHypothesisResponse:
    try:
        creation_input = HuntHypothesisCreationInput(
            title=request.title,
            statement=request.statement,
            rationale=request.rationale,
            target_references=tuple(
                HuntHypothesisReference(
                    reference_type=HuntHypothesisReferenceType(item.reference_type),
                    reference_id=item.reference_id,
                )
                for item in request.target_references
            ),
            threat_references=tuple(
                HuntHypothesisReference(
                    reference_type=HuntHypothesisReferenceType(item.reference_type),
                    reference_id=item.reference_id,
                )
                for item in request.threat_references
            ),
        )
        result = service.create(creation_input, principal)
        return _hunt_hypothesis_response(result.hypothesis)
    except LocalOperatorAuthorizationError as error:
        raise HTTPException(
            status_code=403,
            detail="The authenticated operator is not authorized.",
        ) from error
    except HuntHypothesisConflictError as error:
        raise HTTPException(
            status_code=409,
            detail="Hunt Hypothesis identity already exists.",
        ) from error
    except (HuntHypothesisConfigurationError, HuntHypothesisPersistenceError) as error:
        raise HTTPException(
            status_code=503,
            detail="Hunt Hypothesis repository is unavailable.",
        ) from error
    except HuntHypothesisDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Hunt Hypothesis repository contains invalid data.",
        ) from error
    except (HuntHypothesisCreationValidationError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail="Hunt Hypothesis creation input is invalid.",
        ) from error


@app.post(
    "/api/hunt-hypotheses/{hypothesis_id}/activation",
    response_model=HuntHypothesisResponse,
)
def activate_hunt_hypothesis(
    hypothesis_id: str,
    request: HuntHypothesisActivationRequest,
    principal: AuthenticatedPrincipal = Depends(get_activation_principal),
    service: HuntHypothesisActivationService = Depends(
        get_hunt_hypothesis_activation_service
    ),
) -> HuntHypothesisResponse:
    try:
        result = service.activate(
            HuntHypothesisActivationInput(
                hypothesis_id=hypothesis_id,
                expected_status=HuntHypothesisStatus(request.expected_status),
            ),
            principal,
        )
        return _hunt_hypothesis_response(result.hypothesis)
    except LocalOperatorAuthorizationError as error:
        raise HTTPException(
            status_code=403,
            detail="The authenticated operator is not authorized.",
        ) from error
    except HuntHypothesisRepositoryNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Hunt Hypothesis was not found.",
        ) from error
    except HuntHypothesisStateConflictError as error:
        raise HTTPException(
            status_code=409,
            detail="Hunt Hypothesis state no longer permits activation.",
        ) from error
    except HuntHypothesisActivationValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="Hunt Hypothesis activation input is invalid.",
        ) from error
    except (
        HuntHypothesisConfigurationError,
        HuntHypothesisPersistenceError,
        HuntHypothesisActivationAuditError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail="Hunt Hypothesis activation is unavailable.",
        ) from error
    except HuntHypothesisDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Hunt Hypothesis repository contains invalid data.",
        ) from error


@app.get(
    "/api/hunt-hypotheses/{hypothesis_id}/reference-resolution",
    response_model=HuntHypothesisReferenceResolutionResponse,
)
def hunt_hypothesis_reference_resolution(
    hypothesis_id: str,
    service: HuntHypothesisReferenceResolutionService = Depends(
        get_hunt_hypothesis_reference_resolution_service
    ),
) -> HuntHypothesisReferenceResolutionResponse:
    try:
        return _hunt_hypothesis_reference_resolution_response(
            service.resolve(hypothesis_id)
        )
    except HuntHypothesisNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Hunt Hypothesis was not found."
        ) from error
    except HuntHypothesisConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (HuntHypothesisDataError, HuntHypothesisReferenceIntegrityError) as error:
        raise HTTPException(
            status_code=500,
            detail="Hunt Hypothesis reference resolution failed integrity checks.",
        ) from error


@app.get(
    "/api/findings/{finding_id}/incidents",
    response_model=list[FindingIncidentReferenceResponse],
)
def finding_incidents(
    finding_id: str,
    service: FindingIncidentQueryService = Depends(
        get_finding_incident_query_service
    ),
) -> list[FindingIncidentReferenceResponse]:
    try:
        references = service.find_incidents(finding_id)
    except IncidentContextConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except IncidentContextDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Incident context source contains invalid data.",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return [
        FindingIncidentReferenceResponse(
            incident_id=reference.incident_id,
            relationship_id=reference.relationship_id,
            relationship_role=reference.relationship_role.value,
            lifecycle_status=reference.lifecycle_status.value,
        )
        for reference in references
    ]


@app.get(
    "/api/threat-intelligence/vulnerabilities/{cve_identifier}",
    response_model=VulnerabilityThreatIntelligenceResponse,
)
def vulnerability_threat_intelligence(
    cve_identifier: str,
    service: ThreatIntelligenceQueryService = Depends(
        get_threat_intelligence_query_service
    ),
) -> VulnerabilityThreatIntelligenceResponse:
    try:
        intelligence = service.get_by_cve(cve_identifier)
    except ThreatIntelligenceConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ThreatIntelligenceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ThreatIntelligenceTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except ThreatIntelligenceSourceUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ThreatIntelligenceInvalidResponseError as error:
        raise HTTPException(
            status_code=502,
            detail="NVD source returned an invalid response.",
        ) from error
    except ThreatIntelligenceDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Threat intelligence source returned invalid data.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail="CVE identifier is invalid.",
        ) from error

    return _threat_intelligence_response(intelligence)


@app.get(
    "/api/findings/{finding_id}/threat-intelligence",
    response_model=FindingThreatIntelligenceEnrichmentResponse,
)
def finding_threat_intelligence(
    finding_id: str,
    use_case: FindingThreatIntelligenceUseCase = Depends(
        get_finding_threat_intelligence_use_case
    ),
) -> FindingThreatIntelligenceEnrichmentResponse:
    try:
        enrichment = use_case.enrich(finding_id)
    except FindingNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Finding was not found.",
        ) from error
    except FindingsConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ThreatIntelligenceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ThreatIntelligenceTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except ThreatIntelligenceSourceUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ThreatIntelligenceInvalidResponseError as error:
        raise HTTPException(
            status_code=502,
            detail="Threat intelligence source returned an invalid response.",
        ) from error
    except (ThreatIntelligenceDataError, FindingSelectionError) as error:
        raise HTTPException(
            status_code=500,
            detail="Finding threat intelligence could not be resolved.",
        ) from error
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Configured finding source could not be loaded.",
        ) from error

    return _finding_threat_intelligence_enrichment_response(enrichment)


@app.get(
    "/api/findings/{finding_id}/risk-context",
    response_model=FindingRiskContextResponse,
)
def finding_risk_context(
    finding_id: str,
    use_case: FindingRiskContextUseCase = Depends(
        get_finding_risk_context_use_case
    ),
) -> FindingRiskContextResponse:
    try:
        return _finding_risk_context_response(use_case.project(finding_id))
    except FindingNotFoundError as error:
        raise HTTPException(status_code=404, detail="Finding was not found.") from error
    except (
        FindingsConfigurationError,
        AssetContextConfigurationError,
        ThreatIntelligenceConfigurationError,
    ) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ThreatIntelligenceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ThreatIntelligenceTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except ThreatIntelligenceSourceUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ThreatIntelligenceInvalidResponseError as error:
        raise HTTPException(
            status_code=502,
            detail="Threat intelligence source returned an invalid response.",
        ) from error
    except (ThreatIntelligenceDataError, FindingSelectionError) as error:
        raise HTTPException(
            status_code=500,
            detail="Finding risk context could not be resolved.",
        ) from error
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Configured risk-context source contains invalid data.",
        ) from error


@app.get(
    "/api/incidents/{incident_id}/command-center",
    response_model=IncidentCommandCenterResponse,
)
def incident_command_center(
    incident_id: str,
    service: IncidentCommandCenterQueryService = Depends(
        get_incident_command_center_query_service
    ),
    context_reader: Callable[[str], SecurityIncidentContext | None] = Depends(
        get_security_incident_context_reader
    ),
) -> IncidentCommandCenterResponse:
    if not incident_id.strip():
        raise HTTPException(
            status_code=422,
            detail="Incident ID must not be empty.",
        )
    try:
        projection = service.project(context_reader(incident_id))
    except IncidentCommandCenterIncidentNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Incident was not found.",
        ) from error
    except IncidentContextConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except IncidentContextDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Incident context source contains invalid data.",
        ) from error
    except (LookupError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Incident command-center projection could not be loaded.",
        ) from error

    return _incident_command_center_response(projection)


@app.get(
    "/api/incidents",
    response_model=list[IncidentQueueItemResponse],
)
def incidents(
    service: IncidentQueueQueryService = Depends(get_incident_queue_query_service),
) -> list[IncidentQueueItemResponse]:
    try:
        return [_incident_queue_item_response(item) for item in service.list()]
    except IncidentContextConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except IncidentContextDataError as error:
        raise HTTPException(
            status_code=500,
            detail="Incident context source contains invalid data.",
        ) from error


@app.post(
    "/api/findings/{finding_id}/explanation",
    response_model=FindingExplanationResponse,
)
def explain_finding(
    finding_id: str,
    use_case: FindingExplanationUseCase = Depends(
        get_finding_explanation_use_case
    ),
) -> FindingExplanationResponse:
    try:
        result = use_case.explain(finding_id)
    except FindingNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Finding was not found.",
        ) from error
    except (
        FindingsConfigurationError,
        AssetContextConfigurationError,
    ) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (
        OSError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=500,
            detail="Configured finding context could not be loaded.",
        ) from error

    return _explanation_response(result)


@app.get("/api/decisions")
def decisions():

    return engine.run().get(
        "decisions",
        [],
    )


@app.get("/api/reasoning")
def reasoning():

    return engine.run().get(
        "reasoning_results",
        [],
    )


@app.get("/api/story-bundles")
def story_bundles():

    return engine.run().get(
        "story_bundles",
        [],
    )


@app.get("/api/reports")
def reports():

    return engine.run().get(
        "reports",
        [],
    )


@app.get("/api/graph-summary")
def graph_summary():

    return engine.run().get(
        "graph_summary",
        {},
    )


@app.get("/api/team-risk")
def team_risk():

    return engine.run().get(
        "team_risk",
        {},
    )
