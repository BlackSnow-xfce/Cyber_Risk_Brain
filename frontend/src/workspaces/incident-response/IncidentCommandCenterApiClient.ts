import type { IncidentCommandCenterResponse } from "./IncidentCommandCenter";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class IncidentCommandCenterRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Incident command center request failed.");
    }
}

export async function getIncidentCommandCenter(
    incidentId: string,
): Promise<IncidentCommandCenterResponse> {
    let response: Response;

    try {
        response = await fetch(
            `${API_BASE_URL}/api/incidents/${encodeURIComponent(incidentId)}/command-center`,
        );
    } catch {
        throw new IncidentCommandCenterRequestError(null);
    }

    if (!response.ok) {
        throw new IncidentCommandCenterRequestError(response.status);
    }

    const payload: unknown = await response.json();
    if (!isIncidentCommandCenterResponse(payload)) {
        throw new IncidentCommandCenterRequestError(response.status);
    }
    return payload;
}

function isIncidentCommandCenterResponse(
    value: unknown,
): value is IncidentCommandCenterResponse {
    if (!isRecord(value)) return false;
    return (
        typeof value.contract_version === "string" &&
        isIncidentContext(value.incident) &&
        isReferenceList(value.findings) &&
        isReferenceList(value.assets) &&
        isReferenceList(value.threat_intelligence) &&
        isReferenceList(value.evidence) &&
        isReferenceList(value.decisions) &&
        Array.isArray(value.notes) && value.notes.every(isAnalystNote) &&
        Array.isArray(value.activities) && value.activities.every(isActivity) &&
        Array.isArray(value.sections) && value.sections.every(isSection) &&
        isCompleteness(value.completeness) &&
        isStringList(value.missing_context)
    );
}

function isIncidentContext(value: unknown): value is IncidentCommandCenterResponse["incident"] {
    if (!isRecord(value)) return false;
    return (
        typeof value.incident_id === "string" &&
        typeof value.lifecycle_status === "string" &&
        typeof value.source === "string" &&
        typeof value.source_reference === "string" &&
        typeof value.title === "string" &&
        isNullableString(value.description) &&
        typeof value.created_at === "string" &&
        typeof value.updated_at === "string" &&
        (value.owner === null || isPrincipal(value.owner)) &&
        Array.isArray(value.participants) &&
        value.participants.every(isParticipant)
    );
}

function isReferenceList(value: unknown): value is IncidentCommandCenterResponse["findings"] {
    return Array.isArray(value) && value.every(isReference);
}

function isReference(value: unknown): value is IncidentCommandCenterResponse["findings"][number] {
    return (
        isRecord(value) &&
        typeof value.reference_id === "string" &&
        isNullableString(value.source) &&
        isNullableString(value.contract_version) &&
        isNullableString(value.version_id) &&
        isNullableString(value.evidence_snapshot_id)
    );
}

function isPrincipal(value: unknown): value is IncidentCommandCenterResponse["incident"]["owner"] {
    return (
        isRecord(value) &&
        typeof value.principal_type === "string" &&
        typeof value.principal_id === "string"
    );
}

function isParticipant(value: unknown): boolean {
    return isRecord(value) && isPrincipal(value.principal) && typeof value.role === "string";
}

function isAnalystNote(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.note_id === "string" &&
        typeof value.note_version_id === "string" &&
        typeof value.incident_id === "string" &&
        isPrincipal(value.author) &&
        typeof value.content === "string" &&
        typeof value.created_at === "string" &&
        typeof value.version === "number" &&
        isNullableString(value.supersedes_version_id) &&
        typeof value.contract_version === "string"
    );
}

function isActivity(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.activity_id === "string" &&
        typeof value.incident_id === "string" &&
        typeof value.activity_type === "string" &&
        isPrincipal(value.actor) &&
        typeof value.occurred_at === "string" &&
        typeof value.sequence === "number" &&
        typeof value.description === "string" &&
        Array.isArray(value.details) &&
        value.details.every(
            (detail) =>
                isRecord(detail) &&
                typeof detail.detail_type === "string" &&
                typeof detail.value === "string",
        ) &&
        typeof value.contract_version === "string"
    );
}

function isSection(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.section === "string" &&
        typeof value.status === "string" &&
        isStringList(value.reference_ids) &&
        isStringList(value.source_references) &&
        isStringList(value.missing_context)
    );
}

function isCompleteness(value: unknown): value is IncidentCommandCenterResponse["completeness"] {
    return (
        isRecord(value) &&
        typeof value.status === "string" &&
        typeof value.source_type === "string" &&
        typeof value.source_reference === "string"
    );
}

function isStringList(value: unknown): value is string[] {
    return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isNullableString(value: unknown): value is string | null {
    return value === null || typeof value === "string";
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
