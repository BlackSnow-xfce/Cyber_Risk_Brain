import type { DecisionState } from "../enums";

export interface DecisionStatus {
    state: DecisionState;

    previousState?: DecisionState;

    reason?: string;

    changedBy?: string;

    changedAt: string;
}