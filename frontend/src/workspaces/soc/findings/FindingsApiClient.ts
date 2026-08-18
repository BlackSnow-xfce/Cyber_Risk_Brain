import type {
    FindingExplanationModelOutput,
    FindingExplanationResult,
    FindingExplanationStatement,
} from "./FindingExplanation";
import type { FindingSummary } from "./FindingSummary";

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

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
