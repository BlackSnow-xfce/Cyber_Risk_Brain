export interface ExplainabilityFactor {
    id: string;

    label: string;

    contribution: number;

    weight: number;

    direction: "positive" | "negative";

    evidenceIds: string[];
}