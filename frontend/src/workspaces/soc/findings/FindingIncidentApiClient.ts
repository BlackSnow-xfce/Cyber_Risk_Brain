const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface FindingIncidentReference {
    incident_id: string;
    relationship_id: string;
    relationship_role: string;
    lifecycle_status: string;
}

export class FindingIncidentRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Finding incident context request failed.");
    }
}

export async function getFindingIncidents(
    findingId: string,
): Promise<readonly FindingIncidentReference[]> {
    let response: Response;
    try {
        response = await fetch(
            `${API_BASE_URL}/api/findings/${encodeURIComponent(findingId)}/incidents`,
        );
    } catch {
        throw new FindingIncidentRequestError(null);
    }

    if (!response.ok) {
        throw new FindingIncidentRequestError(response.status);
    }

    const payload: unknown = await response.json();
    if (!isReferenceList(payload)) {
        throw new FindingIncidentRequestError(response.status);
    }
    return payload;
}

function isReferenceList(
    value: unknown,
): value is FindingIncidentReference[] {
    return (
        Array.isArray(value) &&
        value.every(
            (item) =>
                isRecord(item) &&
                typeof item.incident_id === "string" &&
                typeof item.relationship_id === "string" &&
                typeof item.relationship_role === "string" &&
                typeof item.lifecycle_status === "string",
        )
    );
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
