import type {
    CisaKevInformation,
    CvssInformation,
    EpssInformation,
    ExploitationEvidence,
    FindingThreatIntelligenceEnrichment,
    NvdIntelligence,
    ThreatIntelligenceFact,
    ThreatIntelligenceProvenance,
    VulnerabilityThreatIntelligence,
} from "./ThreatIntelligence";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ThreatIntelligenceRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Threat intelligence request failed.");
    }
}

export async function getVulnerabilityThreatIntelligence(
    cveIdentifier: string,
): Promise<VulnerabilityThreatIntelligence> {
    let response: Response;

    try {
        response = await fetch(
            `${API_BASE_URL}/api/threat-intelligence/vulnerabilities/${encodeURIComponent(cveIdentifier)}`,
        );
    } catch {
        throw new ThreatIntelligenceRequestError(null);
    }

    if (!response.ok) {
        throw new ThreatIntelligenceRequestError(response.status);
    }

    const payload: unknown = await response.json();
    if (!isVulnerabilityThreatIntelligence(payload)) {
        throw new ThreatIntelligenceRequestError(response.status);
    }
    return payload;
}

export async function getFindingThreatIntelligence(
    findingId: string,
): Promise<FindingThreatIntelligenceEnrichment> {
    let response: Response;

    try {
        response = await fetch(
            `${API_BASE_URL}/api/findings/${encodeURIComponent(findingId)}/threat-intelligence`,
        );
    } catch {
        throw new ThreatIntelligenceRequestError(null);
    }

    if (!response.ok) {
        throw new ThreatIntelligenceRequestError(response.status);
    }

    const payload: unknown = await response.json();
    if (!isFindingThreatIntelligenceEnrichment(payload)) {
        throw new ThreatIntelligenceRequestError(response.status);
    }
    return payload;
}

function isVulnerabilityThreatIntelligence(
    value: unknown,
): value is VulnerabilityThreatIntelligence {
    if (!isRecord(value)) return false;
    return (
        typeof value.contract_version === "string" &&
        typeof value.cve_identifier === "string" &&
        isFact(value.nvd, isNvdIntelligence) &&
        isFact(value.cvss, isCvssInformation) &&
        isFact(value.epss, isEpssInformation) &&
        isFact(value.cisa_kev, isCisaKevInformation) &&
        isFact(value.exploitation_evidence, isExploitationEvidenceList)
    );
}

function isFindingThreatIntelligenceEnrichment(
    value: unknown,
): value is FindingThreatIntelligenceEnrichment {
    return (
        isRecord(value) &&
        typeof value.finding_id === "string" &&
        typeof value.finding_source === "string" &&
        typeof value.finding_title === "string" &&
        Array.isArray(value.relationships) &&
        value.relationships.every(isFindingThreatIntelligenceRelationship)
    );
}

function isFindingThreatIntelligenceRelationship(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.applicability === "string" &&
        isNullableString(value.cve_identifier) &&
        (value.intelligence === null ||
            isVulnerabilityThreatIntelligence(value.intelligence))
    );
}

function isFact<T>(
    value: unknown,
    isValue: (candidate: unknown) => candidate is T,
): value is ThreatIntelligenceFact<T> {
    return (
        isRecord(value) &&
        typeof value.status === "string" &&
        isProvenance(value.provenance) &&
        isNullableString(value.observed_at) &&
        (value.value === null || isValue(value.value))
    );
}

function isNvdIntelligence(value: unknown): value is NvdIntelligence {
    return (
        isRecord(value) &&
        isNullableString(value.summary) &&
        isNullableString(value.published_at) &&
        isNullableString(value.last_modified_at)
    );
}

function isCvssInformation(value: unknown): value is CvssInformation {
    return (
        isRecord(value) &&
        typeof value.version === "string" &&
        typeof value.base_score === "number" &&
        Number.isFinite(value.base_score) &&
        typeof value.vector === "string" &&
        isNullableString(value.severity)
    );
}

function isEpssInformation(value: unknown): value is EpssInformation {
    return (
        isRecord(value) &&
        typeof value.probability === "number" &&
        Number.isFinite(value.probability) &&
        (value.percentile === null ||
            (typeof value.percentile === "number" &&
                Number.isFinite(value.percentile)))
    );
}

function isCisaKevInformation(value: unknown): value is CisaKevInformation {
    return (
        isRecord(value) &&
        typeof value.known_exploited === "boolean" &&
        isNullableString(value.date_added) &&
        isNullableString(value.required_action) &&
        isNullableString(value.due_date)
    );
}

function isExploitationEvidenceList(
    value: unknown,
): value is readonly ExploitationEvidence[] {
    return Array.isArray(value) && value.every(isExploitationEvidence);
}

function isExploitationEvidence(value: unknown): value is ExploitationEvidence {
    return (
        isRecord(value) &&
        typeof value.evidence_type === "string" &&
        typeof value.description === "string" &&
        isProvenance(value.provenance) &&
        isNullableString(value.observed_at)
    );
}

function isProvenance(value: unknown): value is ThreatIntelligenceProvenance {
    return (
        isRecord(value) &&
        typeof value.source_type === "string" &&
        typeof value.source_reference === "string"
    );
}

function isNullableString(value: unknown): value is string | null {
    return value === null || typeof value === "string";
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
