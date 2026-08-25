import type {
    AIModelCapabilityVisibility,
    AIModelGovernanceVisibility,
    AIModelRegistrationVisibility,
    GovernanceOperatorSession,
} from "./AIModelGovernance";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class AIModelGovernanceRequestError extends Error {
    constructor(readonly status: number | null) {
        super("AI Model Governance request failed.");
    }
}

export async function getAIModelGovernance(): Promise<AIModelGovernanceVisibility> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/api/ai-model-governance`);
    } catch {
        throw new AIModelGovernanceRequestError(null);
    }
    if (!response.ok) throw new AIModelGovernanceRequestError(response.status);
    const payload: unknown = await response.json();
    if (!isGovernanceVisibility(payload)) {
        throw new AIModelGovernanceRequestError(response.status);
    }
    return payload;
}

export async function getGovernanceOperatorSession(): Promise<GovernanceOperatorSession | null> {
    const response = await fetch(`${API_BASE_URL}/api/operator/session`, {
        credentials: "include",
    });
    if (response.status === 401 || response.status === 503) return null;
    if (!response.ok) throw new AIModelGovernanceRequestError(response.status);
    const payload: unknown = await response.json();
    if (!isRecord(payload)
        || !Array.isArray(payload.granted_permissions)
        || !payload.granted_permissions.every((item) => typeof item === "string")
        || typeof payload.csrf_token !== "string") {
        throw new AIModelGovernanceRequestError(response.status);
    }
    return {
        granted_permissions: payload.granted_permissions,
        csrf_token: payload.csrf_token,
    };
}

export async function updateAIModelSelection(
    capability: string,
    provider: string,
    modelId: string,
    csrfToken: string,
): Promise<AIModelGovernanceVisibility> {
    const response = await fetch(
        `${API_BASE_URL}/api/ai-model-governance/selections/${encodeURIComponent(capability)}`,
        {
            method: "PUT",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrfToken,
            },
            body: JSON.stringify({ provider, model_id: modelId }),
        },
    );
    if (!response.ok) throw new AIModelGovernanceRequestError(response.status);
    const payload: unknown = await response.json();
    if (!isGovernanceVisibility(payload)) {
        throw new AIModelGovernanceRequestError(response.status);
    }
    return payload;
}

function isGovernanceVisibility(value: unknown): value is AIModelGovernanceVisibility {
    return isRecord(value)
        && typeof value.contract_version === "string"
        && Array.isArray(value.capabilities)
        && value.capabilities.every((item) => typeof item === "string")
        && Array.isArray(value.providers)
        && value.providers.every((provider) =>
            isRecord(provider)
            && typeof provider.provider === "string"
            && (provider.governance_status === "registered"
                || provider.governance_status === "foundation_only")
            && Array.isArray(provider.registrations)
            && provider.registrations.every(isRegistration),
        );
}

function isRegistration(value: unknown): value is AIModelRegistrationVisibility {
    return isRecord(value)
        && typeof value.provider === "string"
        && typeof value.model_id === "string"
        && typeof value.api_protocol_family === "string"
        && typeof value.deployment_class === "string"
        && typeof value.policy_reference === "string"
        && typeof value.execution_binding === "string"
        && (value.status === "enabled" || value.status === "disabled")
        && typeof value.governance_status === "string"
        && Array.isArray(value.capabilities)
        && value.capabilities.every(isCapability);
}

function isCapability(value: unknown): value is AIModelCapabilityVisibility {
    return isRecord(value)
        && typeof value.capability === "string"
        && typeof value.authorized === "boolean"
        && typeof value.adapter_available === "boolean"
        && typeof value.execution_available === "boolean"
        && typeof value.active === "boolean";
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
