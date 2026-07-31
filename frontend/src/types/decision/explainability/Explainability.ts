import type { ExplainabilityFactor } from "./ExplainabilityFactor";
import type { ExplainabilityRule } from "./ExplainabilityRule";

export interface Explainability {
    summary: string;

    reasoning: string;

    factors: ExplainabilityFactor[];

    rules: ExplainabilityRule[];

    assumptions: string[];

    uncertainties: string[];

    counterfactuals: string[];
}