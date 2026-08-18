from collections.abc import Callable
from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from application import (
    AssetContextConfigurationError,
    AssetContextQueryService,
    FindingExplanationModelOutput,
    FindingExplanationResult,
    FindingExplanationStatement,
    FindingExplanationUseCase,
    FindingNotFoundError,
    FindingExplanationService,
    FindingSelectionError,
    IncidentCommandCenterIncidentNotFoundError,
    IncidentCommandCenterQueryService,
    IncidentContextConfigurationError,
    IncidentContextDataError,
    FileIncidentContextRepository,
    FindingThreatIntelligenceEnrichment,
    FindingThreatIntelligenceUseCase,
    FindingsConfigurationError,
    FindingsQueryService,
    RiskReadinessService,
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceDataError,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceNotFoundError,
    ThreatIntelligenceQueryService,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
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
from settings import ASSET_CONTEXT_PATH, GREENBONE_REPORT_PATH, INCIDENT_CONTEXT_PATH

app = FastAPI(
    title="Cyber Risk Brain",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


engine = PredatorEngine()


class FindingResponse(BaseModel):
    id: str
    source: str
    title: str
    vendorSeverity: str
    asset: str


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


class IncidentReferenceResponse(BaseModel):
    reference_id: str
    source: str | None = None
    contract_version: str | None = None
    version_id: str | None = None
    evidence_snapshot_id: str | None = None


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


def get_finding_explanation_use_case() -> FindingExplanationUseCase:
    return FindingExplanationUseCase(
        FindingsQueryService(GREENBONE_REPORT_PATH),
        AssetContextQueryService(ASSET_CONTEXT_PATH),
        RiskReadinessService(),
        FindingExplanationService(
            OpenAIFindingExplanationModel.from_settings()
        ),
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


def get_incident_command_center_query_service() -> IncidentCommandCenterQueryService:
    return IncidentCommandCenterQueryService()


def get_security_incident_context_reader() -> Callable[
    [str], SecurityIncidentContext | None
]:
    return FileIncidentContextRepository(INCIDENT_CONTEXT_PATH).get


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
