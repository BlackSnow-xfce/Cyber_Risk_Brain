import type { DecisionAction } from "./DecisionAction";

export interface DecisionActions {
    actions: DecisionAction[];

    executionSummary?: string;
}