export interface DecisionOutcome {
    summary: string;
    rationale: string;
    supportingReasoningIds: readonly string[];
}
