import type { DecisionType } from "../enums";

export interface DecisionSummary {
    title: string;

    subtitle?: string;

    description: string;

    category: string;

    tags: string[];

    decisionType: DecisionType;
}