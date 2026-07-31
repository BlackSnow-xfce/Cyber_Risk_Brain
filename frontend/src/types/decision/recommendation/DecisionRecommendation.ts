import type { Urgency } from "../enums";

export interface DecisionRecommendation {
    action: string;

    summary: string;

    rationale: string;

    expectedOutcome: string;

    urgency: Urgency;

    estimatedEffort?: string;

    rollbackAvailable: boolean;

    rollbackDescription?: string;

    alternatives: string[];
}