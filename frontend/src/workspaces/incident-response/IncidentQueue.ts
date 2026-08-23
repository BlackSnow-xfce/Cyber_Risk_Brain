export interface IncidentQueuePrincipal {
    principal_type: string;
    principal_id: string;
}

export interface IncidentQueueItem {
    incident_id: string;
    lifecycle_status: string;
    source: string;
    source_reference: string;
    title: string;
    created_at: string;
    updated_at: string;
    owner: IncidentQueuePrincipal | null;
    participant_count: number;
    finding_count: number;
    asset_count: number;
    threat_intelligence_count: number;
    evidence_count: number;
}
