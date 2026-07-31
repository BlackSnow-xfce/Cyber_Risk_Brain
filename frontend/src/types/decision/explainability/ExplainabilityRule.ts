export interface ExplainabilityRule {
    id: string;

    name: string;

    version: string;

    matched: boolean;

    contribution: number;

    description: string;
}