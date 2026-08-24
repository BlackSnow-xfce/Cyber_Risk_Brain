export interface HuntHypothesisReference {
    reference_type: string;
    reference_id: string;
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
