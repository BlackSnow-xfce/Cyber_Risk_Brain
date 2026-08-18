export interface ThreatIntelligenceProvenance {
    source_type: string;
    source_reference: string;
}

export interface ThreatIntelligenceFact<T> {
    status: string;
    provenance: ThreatIntelligenceProvenance;
    observed_at: string | null;
    value: T | null;
}

export interface NvdIntelligence {
    summary: string | null;
    published_at: string | null;
    last_modified_at: string | null;
}

export interface CvssInformation {
    version: string;
    base_score: number;
    vector: string;
    severity: string | null;
}

export interface EpssInformation {
    probability: number;
    percentile: number | null;
}

export interface CisaKevInformation {
    known_exploited: boolean;
    date_added: string | null;
    required_action: string | null;
    due_date: string | null;
}

export interface ExploitationEvidence {
    evidence_type: string;
    description: string;
    provenance: ThreatIntelligenceProvenance;
    observed_at: string | null;
}

export interface VulnerabilityThreatIntelligence {
    contract_version: string;
    cve_identifier: string;
    nvd: ThreatIntelligenceFact<NvdIntelligence>;
    cvss: ThreatIntelligenceFact<CvssInformation>;
    epss: ThreatIntelligenceFact<EpssInformation>;
    cisa_kev: ThreatIntelligenceFact<CisaKevInformation>;
    exploitation_evidence: ThreatIntelligenceFact<readonly ExploitationEvidence[]>;
}

export interface FindingThreatIntelligenceRelationship {
    applicability: string;
    cve_identifier: string | null;
    intelligence: VulnerabilityThreatIntelligence | null;
}

export interface FindingThreatIntelligenceEnrichment {
    finding_id: string;
    finding_source: string;
    finding_title: string;
    relationships: readonly FindingThreatIntelligenceRelationship[];
}
