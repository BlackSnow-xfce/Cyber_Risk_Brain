import type {
    HuntHypothesis,
    HuntHypothesisCreationInput,
    HuntHypothesisReference,
    HuntHypothesisReferenceResolution,
    LocalOperatorSession,
} from "./HuntHypothesis";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
export const LOCAL_OPERATOR_BOOTSTRAP_URL = `${API_BASE_URL}/api/operator/session/bootstrap`;

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

export async function getLocalOperatorSession(): Promise<LocalOperatorSession | null> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/api/operator/session`, {
            credentials: "include",
        });
    } catch {
        throw new HuntHypothesisRequestError(null);
    }
    if (response.status === 401 || response.status === 503) return null;
    if (!response.ok) throw new HuntHypothesisRequestError(response.status);
    const payload: unknown = await response.json();
    if (!isLocalOperatorSession(payload)) {
        throw new HuntHypothesisRequestError(response.status);
    }
    return payload;
}

export async function createHuntHypothesis(
    input: HuntHypothesisCreationInput,
    csrfToken: string,
): Promise<HuntHypothesis> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/api/hunt-hypotheses`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrfToken,
            },
            body: JSON.stringify(input),
        });
    } catch {
        throw new HuntHypothesisRequestError(null);
    }
    if (!response.ok) throw new HuntHypothesisRequestError(response.status);
    const payload: unknown = await response.json();
    if (!isHuntHypothesis(payload)) {
        throw new HuntHypothesisRequestError(response.status);
    }
    return payload;
}

export async function getHuntHypothesisReferenceResolution(
    hypothesisId: string,
): Promise<HuntHypothesisReferenceResolution> {
    let response: Response;
    try {
        response = await fetch(
            `${API_BASE_URL}/api/hunt-hypotheses/${encodeURIComponent(hypothesisId)}/reference-resolution`,
        );
    } catch {
        throw new HuntHypothesisRequestError(null);
    }
    if (!response.ok) {
        throw new HuntHypothesisRequestError(response.status);
    }
    const payload: unknown = await response.json();
    if (!isReferenceResolution(payload) || payload.hypothesis_id !== hypothesisId) {
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

function isLocalOperatorSession(value: unknown): value is LocalOperatorSession {
    return (
        isRecord(value) &&
        typeof value.principal_id === "string" &&
        typeof value.display_name === "string" &&
        value.principal_type === "human/operator" &&
        Array.isArray(value.granted_permissions) &&
        value.granted_permissions.every((item) => typeof item === "string") &&
        typeof value.expires_at === "string" &&
        typeof value.csrf_token === "string"
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

function isReferenceResolution(
    value: unknown,
): value is HuntHypothesisReferenceResolution {
    return (
        isRecord(value) &&
        typeof value.hypothesis_id === "string" &&
        Array.isArray(value.references) &&
        value.references.every((reference) =>
            isRecord(reference) &&
            isHuntHypothesisReference(reference) &&
            isResolutionStatus(reference.resolution_status) &&
            isNullableString(reference.authoritative_source) &&
            isNullableString(reference.resolved_identity) &&
            isNullableString(reference.source_reference)
        )
    );
}

function isResolutionStatus(value: unknown): boolean {
    return (
        value === "resolved" ||
        value === "not_found" ||
        value === "source_unavailable" ||
        value === "unsupported"
    );
}

function isNullableString(value: unknown): boolean {
    return value === null || typeof value === "string";
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
