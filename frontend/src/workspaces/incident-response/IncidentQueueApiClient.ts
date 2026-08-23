import type { IncidentQueueItem } from "./IncidentQueue";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class IncidentQueueRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Incident queue request failed.");
    }
}

export async function getIncidents(): Promise<IncidentQueueItem[]> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/api/incidents`);
    } catch {
        throw new IncidentQueueRequestError(null);
    }
    if (!response.ok) {
        throw new IncidentQueueRequestError(response.status);
    }
    const payload: unknown = await response.json();
    if (!Array.isArray(payload) || !payload.every(isIncidentQueueItem)) {
        throw new IncidentQueueRequestError(response.status);
    }
    return payload;
}

function isIncidentQueueItem(value: unknown): value is IncidentQueueItem {
    if (!isRecord(value)) return false;
    return (
        typeof value.incident_id === "string" &&
        typeof value.lifecycle_status === "string" &&
        typeof value.source === "string" &&
        typeof value.source_reference === "string" &&
        typeof value.title === "string" &&
        typeof value.created_at === "string" &&
        typeof value.updated_at === "string" &&
        (value.owner === null || isPrincipal(value.owner)) &&
        isNumber(value.participant_count) &&
        isNumber(value.finding_count) &&
        isNumber(value.asset_count) &&
        isNumber(value.threat_intelligence_count) &&
        isNumber(value.evidence_count)
    );
}

function isPrincipal(value: unknown): boolean {
    return (
        isRecord(value) &&
        typeof value.principal_type === "string" &&
        typeof value.principal_id === "string"
    );
}

function isNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
