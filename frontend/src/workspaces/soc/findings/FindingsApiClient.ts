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
        !isRecord(value.assessment) || !isRecord(value.evidence_readiness) ||
        !isRecord(value.business_context) ||
        !isRecord(value.business_impact_readiness) ||
        !isRecord(value.service_impact_profile) ||
        !isRecord(value.technical_effect) ||
        !isRecord(value.business_impact_classification_readiness)) {
        return false;
    }
    const asset = value.asset_context;
    const assessment = value.assessment;
    const readiness = value.evidence_readiness;
    const business = value.business_context;
    const impactReadiness = value.business_impact_readiness;
    const profile = value.service_impact_profile;
    const technicalEffect = value.technical_effect;
    const classificationReadiness = value.business_impact_classification_readiness;
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
        isNullableString(value.refusal_reason) && isRiskPriority(value.priority) &&
        ["RESOLVED", "NOT_FOUND", "MISSING_CANONICAL_ASSET"].includes(String(business.status)) &&
        isBusinessContextStateValid(business) &&
        ["READY", "UNAVAILABLE"].includes(String(impactReadiness.status)) &&
        impactReadiness.finding_id === value.finding_id &&
        typeof impactReadiness.reason === "string" &&
        Array.isArray(impactReadiness.facts) && impactReadiness.facts.every(isSourceFact) &&
        isStringArray(impactReadiness.missing_requirements) &&
        isStringArray(impactReadiness.source_references) &&
        typeof impactReadiness.completeness_status === "string" &&
        impactReadiness.source_type === "business_impact_readiness" &&
        impactReadiness.source_reference ===
            `business-impact-readiness:${String(impactReadiness.status).toLowerCase()}:${value.finding_id}` &&
        isBusinessSnapshotConsistent(business, impactReadiness) &&
        isServiceImpactProfile(profile, business) &&
        isTechnicalEffectProjection(technicalEffect, value.finding_id, value.threat_intelligence.relationships) &&
        isClassificationReadiness(classificationReadiness, value.finding_id, impactReadiness, profile, technicalEffect) &&
        (impactReadiness.status !== "READY" ||
            (business.status === "RESOLVED" && impactReadiness.missing_requirements.length === 0 &&
                impactReadiness.completeness_status === "available" &&
                hasCompleteBusinessFacts(impactReadiness.facts, impactReadiness.source_references))) &&
        (impactReadiness.status !== "UNAVAILABLE" ||
            (impactReadiness.missing_requirements.length > 0 &&
                impactReadiness.completeness_status !== "available")) &&
        value.business_impact === null && value.decision === null &&
        Array.isArray(value.recommendations) && value.recommendations.length === 0 &&
        (!insufficient || (assessment.score === null && value.refusal_reason !== null &&
            assessment.missing_inputs.length > 0));
}

const BUSINESS_IMPORTANCE = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const TECHNICAL_EFFECT_LEVEL = ["NONE", "LOW", "HIGH"];

function isServiceImpactProfile(profile: Record<string, unknown>, business: Record<string, unknown>): boolean {
    const fields = [profile.canonical_asset_id, profile.business_service,
        profile.confidentiality_importance, profile.integrity_importance,
        profile.availability_importance, profile.source_reference];
    if (!["RESOLVED", "NOT_FOUND", "MISSING_CANONICAL_ASSET"].includes(String(profile.status))) return false;
    if (profile.status !== "RESOLVED") return fields.every((item) => item === null);
    return typeof profile.canonical_asset_id === "string" && profile.canonical_asset_id === business.canonical_asset_id &&
        typeof profile.business_service === "string" && profile.business_service === business.business_service &&
        [profile.confidentiality_importance, profile.integrity_importance, profile.availability_importance]
            .every((item) => BUSINESS_IMPORTANCE.includes(String(item))) &&
        typeof profile.source_reference === "string" && profile.source_reference.length > 0;
}

function isTechnicalEffect(value: unknown, findingId: unknown): boolean {
    return isRecord(value) && value.finding_id === findingId && typeof value.cve_identifier === "string" &&
        /^CVE-\d{4}-\d{4,}$/.test(value.cve_identifier) && ["3.0", "3.1"].includes(String(value.cvss_version)) &&
        typeof value.cvss_vector === "string" && value.cvss_vector.startsWith(`CVSS:${String(value.cvss_version)}/`) &&
        [value.confidentiality, value.integrity, value.availability]
            .every((item) => TECHNICAL_EFFECT_LEVEL.includes(String(item))) &&
        value.source_type === "nvd" &&
        typeof value.source_reference === "string" && value.source_reference.length > 0 &&
        typeof value.observed_at === "string" && hasTimezone(value.observed_at) &&
        technicalLevels(value.cvss_version, value.cvss_vector)?.join(":") ===
            [value.confidentiality, value.integrity, value.availability].join(":");
}

function isTechnicalEffectProjection(value: Record<string, unknown>, findingId: unknown, relationships: unknown): boolean {
    if (value.finding_id !== findingId || !["AVAILABLE", "UNAVAILABLE"].includes(String(value.status)) ||
        !Array.isArray(value.effects) || !value.effects.every((effect) => isTechnicalEffect(effect, findingId)) ||
        !value.effects.every((effect) => isEffectSourceBound(effect, relationships)) ||
        !isStringArray(value.missing_requirements) || value.source_type !== "finding_technical_effect" ||
        value.source_reference !== `finding-technical-effect:${String(value.status).toLowerCase()}:${String(findingId)}`) return false;
    const cves = value.effects.map((effect) => (effect as Record<string, unknown>).cve_identifier);
    if (cves.length !== new Set(cves).size) return false;
    return value.status === "AVAILABLE"
        ? value.effects.length > 0 && value.missing_requirements.length === 0 && value.completeness_status === "available"
        : value.missing_requirements.length > 0 && value.completeness_status !== "available";
}

function hasTimezone(value: string): boolean {
    return /(?:Z|[+-]\d{2}:\d{2})$/.test(value) && !Number.isNaN(Date.parse(value));
}

const CVSS_VALUES: Readonly<Record<string, readonly string[]>> = {
    AV: ["N", "A", "L", "P"], AC: ["L", "H"], PR: ["N", "L", "H"],
    UI: ["N", "R"], S: ["U", "C"], C: ["N", "L", "H"],
    I: ["N", "L", "H"], A: ["N", "L", "H"],
};

function technicalLevels(version: unknown, vector: unknown): readonly string[] | null {
    if (!["3.0", "3.1"].includes(String(version)) || typeof vector !== "string" ||
        !vector.startsWith(`CVSS:${String(version)}/`)) return null;
    const metrics: Record<string, string> = {};
    for (const token of vector.split("/").slice(1)) {
        const parts = token.split(":");
        if (parts.length !== 2 || !(parts[0] in CVSS_VALUES) || parts[0] in metrics ||
            !CVSS_VALUES[parts[0]].includes(parts[1])) return null;
        metrics[parts[0]] = parts[1];
    }
    if (Object.keys(metrics).length !== Object.keys(CVSS_VALUES).length) return null;
    const map: Readonly<Record<string, string>> = { N: "NONE", L: "LOW", H: "HIGH" };
    return [map[metrics.C], map[metrics.I], map[metrics.A]];
}

function isEffectSourceBound(effect: unknown, relationships: unknown): boolean {
    if (!isRecord(effect) || !Array.isArray(relationships)) return false;
    const matches = relationships.filter((relationship) => {
        if (!isRecord(relationship) || relationship.applicability !== "applicable" ||
            relationship.cve_identifier !== effect.cve_identifier || !isRecord(relationship.intelligence) ||
            relationship.intelligence.cve_identifier !== effect.cve_identifier || !isRecord(relationship.intelligence.cvss)) return false;
        const cvss = relationship.intelligence.cvss;
        if (cvss.status !== "available" || !isRecord(cvss.value) || !isRecord(cvss.provenance)) return false;
        return cvss.value.version === effect.cvss_version && cvss.value.vector === effect.cvss_vector &&
            cvss.provenance.source_type === effect.source_type &&
            cvss.provenance.source_reference === effect.source_reference && cvss.observed_at === effect.observed_at;
    });
    return matches.length === 1;
}

function isClassificationReadiness(
    value: Record<string, unknown>, findingId: unknown, businessReadiness: Record<string, unknown>,
    profile: Record<string, unknown>, technical: Record<string, unknown>,
): boolean {
    if (value.finding_id !== findingId || !["READY", "UNAVAILABLE"].includes(String(value.status)) ||
        typeof value.reason !== "string" || !Array.isArray(value.business_facts) ||
        !value.business_facts.every(isSourceFact) || !Array.isArray(value.service_impact_facts) ||
        !value.service_impact_facts.every(isSourceFact) || !Array.isArray(value.technical_effects) ||
        !value.technical_effects.every((effect) => isTechnicalEffect(effect, findingId)) ||
        !isStringArray(value.missing_requirements) || !isStringArray(value.source_references) ||
        value.source_type !== "business_impact_classification_readiness" ||
        value.source_reference !== `business-impact-classification-readiness:${String(value.status).toLowerCase()}:${String(findingId)}`) return false;
    const exactTransportMatches = JSON.stringify(value.business_facts) === JSON.stringify(businessReadiness.facts) &&
        JSON.stringify(value.technical_effects) === JSON.stringify(technical.effects);
    const partialTransportMatches = value.business_facts.every((fact) =>
        Array.isArray(businessReadiness.facts) && businessReadiness.facts.some((candidate) =>
            JSON.stringify(candidate) === JSON.stringify(fact))) &&
        value.technical_effects.every((effect) => Array.isArray(technical.effects) &&
            technical.effects.some((candidate) => JSON.stringify(candidate) === JSON.stringify(effect)));
    const profileSources = value.service_impact_facts.every((fact) => isRecord(fact) && fact.source_reference === profile.source_reference);
    const sourceReferences = value.source_references as readonly string[];
    const allSourcesKnown = [...value.business_facts, ...value.service_impact_facts, ...value.technical_effects]
        .every((fact) => isRecord(fact) && typeof fact.source_reference === "string" && sourceReferences.includes(fact.source_reference));
    const serviceFactsMatch = value.status !== "READY" || hasExactServiceImpactFacts(profile, value.service_impact_facts);
    if (!(value.status === "READY" ? exactTransportMatches : partialTransportMatches) || !profileSources || !allSourcesKnown || !serviceFactsMatch) return false;
    return value.status === "READY"
        ? profile.status === "RESOLVED" && technical.status === "AVAILABLE" && businessReadiness.status === "READY" &&
            value.service_impact_facts.length === 5 && value.missing_requirements.length === 0 && value.completeness_status === "available"
        : value.missing_requirements.length > 0 && value.completeness_status !== "available";
}

function hasExactServiceImpactFacts(profile: Record<string, unknown>, facts: unknown[]): boolean {
    const expected = {
        canonical_asset_id: profile.canonical_asset_id,
        business_service: profile.business_service,
        confidentiality_importance: profile.confidentiality_importance,
        integrity_importance: profile.integrity_importance,
        availability_importance: profile.availability_importance,
    };
    if (facts.length !== Object.keys(expected).length) return false;
    return Object.entries(expected).every(([name, value]) => {
        const matches = facts.filter((fact) => isRecord(fact) && fact.name === name);
        const fact = matches[0];
        return matches.length === 1 && isRecord(fact) && fact.value === value && fact.source_reference === profile.source_reference;
    });
}

function isBusinessContextStateValid(value: Record<string, unknown>): boolean {
    const fields = [value.canonical_asset_id, value.business_service, value.environment,
        value.service_criticality, value.source_reference];
    if (!Array.isArray(value.facts) || !value.facts.every(isSourceFact)) return false;
    return value.status === "RESOLVED"
        ? fields.every((item) => typeof item === "string" && item.length > 0) &&
            ["PRODUCTION", "PRE_PRODUCTION", "DEVELOPMENT", "TEST"].includes(String(value.environment)) &&
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"].includes(String(value.service_criticality)) &&
            hasExactBusinessFacts(value, value.facts)
        : fields.every((item) => item === null) && value.facts.length === 0;
}

const BUSINESS_FACT_NAMES = [
    "canonical_asset_id",
    "business_service",
    "environment",
    "service_criticality",
] as const;

function isBusinessSnapshotConsistent(
    business: Record<string, unknown>,
    readiness: Record<string, unknown>,
): boolean {
    if (!Array.isArray(readiness.facts)) return false;
    if (!isStringArray(readiness.source_references) ||
        !factsReferenceKnownSources(readiness.facts, readiness.source_references)) {
        return false;
    }
    if (business.status === "RESOLVED") {
        if (!hasExactBusinessFacts(business, business.facts)) return false;
        return readiness.status === "READY"
            ? hasExactBusinessFacts(business, readiness.facts)
            : hasConsistentPartialBusinessFacts(business, readiness.facts);
    }
    return readiness.status === "UNAVAILABLE" &&
        hasValidUniqueBusinessFacts(readiness.facts);
}

function hasExactBusinessFacts(
    business: Record<string, unknown>,
    facts: unknown,
): boolean {
    if (!Array.isArray(facts) || facts.length !== BUSINESS_FACT_NAMES.length) {
        return false;
    }
    return hasValidUniqueBusinessFacts(facts) && BUSINESS_FACT_NAMES.every((name) => {
        const matches = facts.filter((fact) => isRecord(fact) && fact.name === name);
        return matches.length === 1 && isFactEqualToBusiness(matches[0], business, name);
    });
}

function hasConsistentPartialBusinessFacts(
    business: Record<string, unknown>,
    facts: unknown[],
): boolean {
    return hasValidUniqueBusinessFacts(facts) && facts.every((fact) =>
        isRecord(fact) && BUSINESS_FACT_NAMES.includes(
            fact.name as (typeof BUSINESS_FACT_NAMES)[number],
        ) && isFactEqualToBusiness(
            fact,
            business,
            fact.name as (typeof BUSINESS_FACT_NAMES)[number],
        ));
}

function hasValidUniqueBusinessFacts(facts: unknown[]): boolean {
    if (!facts.every(isBusinessFactSemanticallyValid)) return false;
    const names = facts.map((fact) => (fact as Record<string, unknown>).name);
    return names.length === new Set(names).size;
}

function isBusinessFactSemanticallyValid(value: unknown): boolean {
    if (!isSourceFact(value) || !BUSINESS_FACT_NAMES.includes(
        value.name as (typeof BUSINESS_FACT_NAMES)[number],
    )) {
        return false;
    }
    if (value.name === "environment") {
        return ["PRODUCTION", "PRE_PRODUCTION", "DEVELOPMENT", "TEST"]
            .includes(value.value);
    }
    if (value.name === "service_criticality") {
        return ["CRITICAL", "HIGH", "MEDIUM", "LOW"].includes(value.value);
    }
    return value.value.length > 0;
}

function factsReferenceKnownSources(
    facts: unknown[],
    sourceReferences: readonly string[],
): boolean {
    return facts.every((fact) => isRecord(fact) &&
        typeof fact.source_reference === "string" &&
        sourceReferences.includes(fact.source_reference));
}

function isFactEqualToBusiness(
    fact: unknown,
    business: Record<string, unknown>,
    name: (typeof BUSINESS_FACT_NAMES)[number],
): boolean {
    return isRecord(fact) && fact.name === name && fact.value === business[name] &&
        fact.source_reference === business.source_reference;
}

function hasCompleteBusinessFacts(facts: unknown[], sourceReferences: readonly string[]): boolean {
    const required = ["canonical_asset_id", "business_service", "environment", "service_criticality"];
    return facts.length === required.length && required.every((name) =>
        facts.filter((fact) => isRecord(fact) && fact.name === name &&
            typeof fact.source_reference === "string" &&
            sourceReferences.includes(fact.source_reference)).length === 1);
}

function isRiskPriority(value: unknown): boolean {
    if (!isRecord(value) || !["PRIORITIZED", "UNAVAILABLE"].includes(String(value.status)) ||
        typeof value.reason !== "string" || !isStringArray(value.considered_evidence_ids) ||
        !isStringArray(value.referenced_input_references) ||
        !isStringArray(value.missing_requirements) || typeof value.completeness_status !== "string" ||
        typeof value.source_type !== "string" || typeof value.source_reference !== "string") return false;
    return value.status === "PRIORITIZED"
        ? ["critical", "high", "medium", "low", "informational"].includes(String(value.band)) &&
            typeof value.score === "number" && value.missing_requirements.length === 0
        : value.band === null && value.score === null;
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

function isSourceFact(value: unknown): value is {
    name: string;
    value: string;
    source_reference: string;
} {
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
