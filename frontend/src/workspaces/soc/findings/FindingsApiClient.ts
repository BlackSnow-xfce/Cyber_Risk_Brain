import type {
    FindingExplanationModelOutput,
    FindingExplanationResult,
    FindingExplanationStatement,
} from "./FindingExplanation";
import type { FindingSummary } from "./FindingSummary";
import type { FindingRiskContext, FindingRiskInput } from "./FindingRiskContext";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getFindings(): Promise<readonly FindingSummary[]> {
    const response = await fetch(`${API_BASE_URL}/api/findings`);

    if (!response.ok) {
        throw new Error(`Findings request failed with status ${response.status}.`);
    }

    const payload: unknown = await response.json();

    if (!isFindingSummaryList(payload)) {
        throw new Error("Findings response does not match the API contract.");
    }

    return payload;
}

export class FindingExplanationRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Finding explanation request failed.");
    }
}

export class FindingRiskContextRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Finding risk context request failed.");
    }
}

export async function getFindingRiskContext(
    findingId: string,
): Promise<FindingRiskContext> {
    let response: Response;
    try {
        response = await fetch(
            `${API_BASE_URL}/api/findings/${encodeURIComponent(findingId)}/risk-context`,
        );
    } catch {
        throw new FindingRiskContextRequestError(null);
    }
    if (!response.ok) {
        throw new FindingRiskContextRequestError(response.status);
    }
    const payload: unknown = await response.json();
    if (!isFindingRiskContext(payload)) {
        throw new FindingRiskContextRequestError(response.status);
    }
    return payload;
}

export async function generateFindingExplanation(
    findingId: string,
): Promise<FindingExplanationResult> {
    let response: Response;

    try {
        response = await fetch(
            `${API_BASE_URL}/api/findings/${encodeURIComponent(findingId)}/explanation`,
            { method: "POST" },
        );
    } catch {
        throw new FindingExplanationRequestError(null);
    }

    if (!response.ok) {
        throw new FindingExplanationRequestError(response.status);
    }

    const payload: unknown = await response.json();

    if (!isFindingExplanationResult(payload)) {
        throw new FindingExplanationRequestError(response.status);
    }

    return payload;
}

function isFindingSummaryList(
    value: unknown,
): value is readonly FindingSummary[] {
    return Array.isArray(value) && value.every(isFindingSummary);
}

function isFindingSummary(value: unknown): value is FindingSummary {
    if (typeof value !== "object" || value === null) {
        return false;
    }

    const finding = value as Record<string, unknown>;

    return (
        typeof finding.id === "string" &&
        typeof finding.source === "string" &&
        typeof finding.title === "string" &&
        typeof finding.vendorSeverity === "string" &&
        typeof finding.asset === "string"
    );
}

function isFindingExplanationResult(
    value: unknown,
): value is FindingExplanationResult {
    if (!isRecord(value)) {
        return false;
    }

    return (
        typeof value.finding_id === "string" &&
        typeof value.generation_status === "string" &&
        Array.isArray(value.factual_context) &&
        value.factual_context.every(isFact) &&
        Array.isArray(value.missing_context) &&
        value.missing_context.every(isMissingContext) &&
        isNullableString(value.provider_id) &&
        isNullableString(value.model_id) &&
        typeof value.input_contract_version === "string" &&
        typeof value.input_digest === "string" &&
        isStringArray(value.used_fact_ids) &&
        isStringArray(value.source_references) &&
        (value.model_output === null || isModelOutput(value.model_output))
    );
}

function isFact(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.fact_id === "string" &&
        typeof value.value === "string" &&
        isNullableString(value.source_reference)
    );
}

function isMissingContext(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.name === "string" &&
        typeof value.state === "string"
    );
}

function isModelOutput(value: unknown): value is FindingExplanationModelOutput {
    return (
        isRecord(value) &&
        isStatement(value.summary) &&
        Array.isArray(value.technical_reasoning) &&
        value.technical_reasoning.every(isStatement) &&
        Array.isArray(value.organizational_relevance) &&
        value.organizational_relevance.every(isStatement) &&
        isStatement(value.uncertainty_statement)
    );
}

function isStatement(value: unknown): value is FindingExplanationStatement {
    return (
        isRecord(value) &&
        typeof value.kind === "string" &&
        typeof value.text === "string" &&
        isStringArray(value.basis_fact_ids)
    );
}

function isStringArray(value: unknown): value is readonly string[] {
    return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isNullableString(value: unknown): value is string | null {
    return value === null || typeof value === "string";
}

function isFindingRiskContext(value: unknown): value is FindingRiskContext {
    if (!isRecord(value) || !isRecord(value.asset_context) ||
        !isRecord(value.threat_intelligence) || !isRecord(value.correlation) ||
        !isRecord(value.assessment) || !isRecord(value.evidence_readiness)) {
        return false;
    }
    const asset = value.asset_context;
    const assessment = value.assessment;
    const readiness = value.evidence_readiness;
    const resolved = asset.status === "resolved";
    const assetFieldsValid = resolved
        ? [asset.observed_identifier_type, asset.observed_identifier_value, asset.canonical_asset_id, asset.criticality, asset.source_reference]
            .every((item) => typeof item === "string" && item.length > 0)
        : [asset.canonical_asset_id, asset.criticality, asset.source_reference]
            .every((item) => item === null);
    const riskInputs = Array.isArray(value.risk_inputs) && value.risk_inputs.every(isRiskInput);
    const insufficient = assessment.status === "INSUFFICIENT_CONTEXT";
    return typeof value.finding_id === "string" && value.finding_id.length > 0 &&
        Array.isArray(value.source_facts) && value.source_facts.every(isSourceFact) &&
        ["resolved", "not_found", "missing_identifier"].includes(String(asset.status)) && assetFieldsValid &&
        typeof value.threat_intelligence.finding_id === "string" &&
        value.threat_intelligence.finding_id === value.finding_id &&
        typeof value.threat_intelligence.finding_source === "string" &&
        typeof value.threat_intelligence.finding_title === "string" &&
        Array.isArray(value.threat_intelligence.relationships) &&
        value.threat_intelligence.relationships.every(isThreatIntelligenceRelationship) &&
        typeof value.correlation.completeness_status === "string" &&
        typeof value.correlation.source_type === "string" &&
        typeof value.correlation.source_reference === "string" &&
        Array.isArray(value.evidence) && value.evidence.every(isEvidence) && riskInputs &&
        hasRequiredRiskInputs(value.risk_inputs) &&
        ["ASSESSED", "INSUFFICIENT_CONTEXT"].includes(String(assessment.status)) &&
        Array.isArray(assessment.available_inputs) && assessment.available_inputs.every(isRiskInput) &&
        Array.isArray(assessment.missing_inputs) && assessment.missing_inputs.every(isRiskInput) &&
        (typeof assessment.score === "number" || assessment.score === null) &&
        ["READY", "INSUFFICIENT_EVIDENCE"].includes(String(readiness.status)) &&
        typeof readiness.reason === "string" &&
        isStringArray(readiness.considered_evidence_ids) &&
        isStringArray(readiness.referenced_input_references) &&
        isStringArray(readiness.missing_requirements) &&
        typeof readiness.completeness_status === "string" &&
        typeof readiness.source_type === "string" && typeof readiness.source_reference === "string" &&
        isNullableString(value.refusal_reason) && value.priority === null &&
        value.business_impact === null && value.decision === null &&
        Array.isArray(value.recommendations) && value.recommendations.length === 0 &&
        (!insufficient || (assessment.score === null && value.refusal_reason !== null &&
            assessment.missing_inputs.length > 0));
}

function hasRequiredRiskInputs(value: unknown): boolean {
    const required = ["business_criticality", "exposure", "detection_available",
        "threat_intelligence_match", "mitre_tactic"];
    return Array.isArray(value) && value.every(isRiskInput) &&
        value.length === required.length &&
        required.every((name) => value.filter((item) => item.name === name).length === 1);
}

function isThreatIntelligenceRelationship(value: unknown): boolean {
    if (!isRecord(value) || typeof value.applicability !== "string" ||
        !isNullableString(value.cve_identifier)) return false;
    if (value.intelligence === null) return true;
    if (!isRecord(value.intelligence)) return false;
    const intelligence = value.intelligence;
    return typeof intelligence.contract_version === "string" &&
        typeof intelligence.cve_identifier === "string" &&
        [intelligence.nvd, intelligence.cvss, intelligence.epss,
            intelligence.cisa_kev, intelligence.exploitation_evidence]
            .every(isThreatIntelligenceFact);
}

function isThreatIntelligenceFact(value: unknown): boolean {
    return isRecord(value) && typeof value.status === "string" &&
        isNullableString(value.observed_at) && isRecord(value.provenance) &&
        typeof value.provenance.source_type === "string" &&
        typeof value.provenance.source_reference === "string" &&
        Object.hasOwn(value, "value");
}

function isSourceFact(value: unknown): boolean {
    return isRecord(value) && typeof value.name === "string" && value.name.length > 0 &&
        typeof value.value === "string" && typeof value.source_reference === "string" &&
        value.source_reference.length > 0;
}

function isRiskInput(value: unknown): value is FindingRiskInput {
    if (!isRecord(value) || typeof value.name !== "string" ||
        !["AUTHORITATIVE", "UNKNOWN", "NOT_EVALUATED"].includes(String(value.state))) {
        return false;
    }
    return value.state === "AUTHORITATIVE"
        ? (typeof value.value === "string" || typeof value.value === "boolean") &&
            typeof value.source === "string" && value.source.length > 0
        : value.value === null && value.source === null;
}

function isEvidence(value: unknown): boolean {
    return isRecord(value) && [value.identifier, value.kind, value.evidence_type,
        value.contract_version, value.source_type, value.source_reference]
        .every((item) => typeof item === "string" && item.length > 0) &&
        isStringArray(value.input_references);
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
