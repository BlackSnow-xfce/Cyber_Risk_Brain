export interface HuntHypothesisReference {
    reference_type: string;
    reference_id: string;
}

export interface LocalOperatorSession {
    principal_id: string;
    display_name: string;
    principal_type: string;
    granted_permissions: string[];
    expires_at: string;
    csrf_token: string;
}

export interface HuntHypothesisCreationInput {
    title: string;
    statement: string;
    rationale: string;
    target_references: HuntHypothesisReference[];
    threat_references: HuntHypothesisReference[];
}

export interface HuntHypothesis {
    hypothesis_id: string;
    title: string;
    statement: string;
    status: string;
    created_at: string;
    created_by: string;
    target_references: HuntHypothesisReference[];
    threat_references: HuntHypothesisReference[];
    rationale: string;
    contract_version: string;
}

export type HuntHypothesisReferenceResolutionStatus =
    | "resolved"
    | "not_found"
    | "source_unavailable"
    | "unsupported";

export interface HuntHypothesisResolvedReference extends HuntHypothesisReference {
    resolution_status: HuntHypothesisReferenceResolutionStatus;
    authoritative_source: string | null;
    resolved_identity: string | null;
    source_reference: string | null;
}

export interface HuntHypothesisReferenceResolution {
    hypothesis_id: string;
    references: HuntHypothesisResolvedReference[];
}
