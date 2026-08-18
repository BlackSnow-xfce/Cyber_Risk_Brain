export interface IncidentPrincipal {
    principal_type: string;
    principal_id: string;
}

export interface IncidentParticipant {
    principal: IncidentPrincipal;
    role: string;
}

export interface IncidentContext {
    incident_id: string;
    lifecycle_status: string;
    source: string;
    source_reference: string;
    title: string;
    description: string | null;
    created_at: string;
    updated_at: string;
    owner: IncidentPrincipal | null;
    participants: IncidentParticipant[];
}

export interface IncidentReference {
    reference_id: string;
    source: string | null;
    contract_version: string | null;
    version_id: string | null;
    evidence_snapshot_id: string | null;
}

export interface IncidentProjectionSection {
    section: string;
    status: string;
    reference_ids: string[];
    source_references: string[];
    missing_context: string[];
}

export interface IncidentCompleteness {
    status: string;
    source_type: string;
    source_reference: string;
}

export interface IncidentActivityDetail {
    detail_type: string;
    value: string;
}

export interface IncidentActivity {
    activity_id: string;
    incident_id: string;
    activity_type: string;
    actor: IncidentPrincipal;
    occurred_at: string;
    sequence: number;
    description: string;
    details: IncidentActivityDetail[];
    contract_version: string;
}

export interface AnalystNote {
    note_id: string;
    note_version_id: string;
    incident_id: string;
    author: IncidentPrincipal;
    content: string;
    created_at: string;
    version: number;
    supersedes_version_id: string | null;
    contract_version: string;
}

export interface IncidentCommandCenterResponse {
    contract_version: string;
    incident: IncidentContext;
    findings: IncidentReference[];
    assets: IncidentReference[];
    threat_intelligence: IncidentReference[];
    evidence: IncidentReference[];
    decisions: IncidentReference[];
    notes: AnalystNote[];
    activities: IncidentActivity[];
    sections: IncidentProjectionSection[];
    completeness: IncidentCompleteness;
    missing_context: string[];
}
