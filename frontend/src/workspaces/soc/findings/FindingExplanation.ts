export interface FindingExplanationFact {
    fact_id: string;
    value: string;
    source_reference: string | null;
}

export interface FindingExplanationMissingContext {
    name: string;
    state: string;
}

export interface FindingExplanationStatement {
    kind: string;
    text: string;
    basis_fact_ids: readonly string[];
}

export interface FindingExplanationModelOutput {
    summary: FindingExplanationStatement;
    technical_reasoning: readonly FindingExplanationStatement[];
    organizational_relevance: readonly FindingExplanationStatement[];
    uncertainty_statement: FindingExplanationStatement;
}

export interface FindingExplanationResult {
    finding_id: string;
    generation_status: string;
    factual_context: readonly FindingExplanationFact[];
    missing_context: readonly FindingExplanationMissingContext[];
    provider_id: string | null;
    model_id: string | null;
    input_contract_version: string;
    input_digest: string;
    used_fact_ids: readonly string[];
    source_references: readonly string[];
    model_output: FindingExplanationModelOutput | null;
}
