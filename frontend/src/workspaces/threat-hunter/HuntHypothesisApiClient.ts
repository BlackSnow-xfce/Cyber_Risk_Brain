import type {
    HuntHypothesis,
    HuntHypothesisReference,
} from "./HuntHypothesis";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class HuntHypothesisRequestError extends Error {
    constructor(readonly status: number | null) {
        super("Hunt Hypothesis request failed.");
    }
}

export async function getHuntHypotheses(): Promise<HuntHypothesis[]> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/api/hunt-hypotheses`);
    } catch {
        throw new HuntHypothesisRequestError(null);
    }
    if (!response.ok) {
        throw new HuntHypothesisRequestError(response.status);
    }
    const payload: unknown = await response.json();
    if (!Array.isArray(payload) || !payload.every(isHuntHypothesis)) {
        throw new HuntHypothesisRequestError(response.status);
    }
    return payload;
}

function isHuntHypothesis(value: unknown): value is HuntHypothesis {
    if (!isRecord(value)) return false;
    return (
        typeof value.hypothesis_id === "string" &&
        typeof value.title === "string" &&
        typeof value.statement === "string" &&
        typeof value.status === "string" &&
        typeof value.created_at === "string" &&
        typeof value.created_by === "string" &&
        Array.isArray(value.target_references) &&
        value.target_references.every(isHuntHypothesisReference) &&
        Array.isArray(value.threat_references) &&
        value.threat_references.every(isHuntHypothesisReference) &&
        typeof value.rationale === "string" &&
        typeof value.contract_version === "string"
    );
}

function isHuntHypothesisReference(
    value: unknown,
): value is HuntHypothesisReference {
    return (
        isRecord(value) &&
        typeof value.reference_type === "string" &&
        typeof value.reference_id === "string"
    );
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
