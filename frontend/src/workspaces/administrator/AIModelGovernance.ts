export interface AIModelCapabilityVisibility {
    capability: string;
    authorized: boolean;
    adapter_available: boolean;
    execution_available: boolean;
    active: boolean;
}

export interface GovernanceOperatorSession {
    granted_permissions: string[];
    csrf_token: string;
}

export interface AIModelRegistrationVisibility {
    provider: string;
    model_id: string;
    api_protocol_family: string;
    deployment_class: string;
    policy_reference: string;
    execution_binding: string;
    status: "enabled" | "disabled";
    governance_status: string;
    capabilities: AIModelCapabilityVisibility[];
}

export interface AIProviderGovernanceVisibility {
    provider: string;
    governance_status: "registered" | "foundation_only";
    registrations: AIModelRegistrationVisibility[];
}

export interface AIModelGovernanceVisibility {
    contract_version: string;
    capabilities: string[];
    providers: AIProviderGovernanceVisibility[];
}
