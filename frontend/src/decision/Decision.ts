import type { DecisionOutcome } from "./DecisionOutcome";
import type { DecisionPriority } from "./DecisionPriority";
import type { DecisionState } from "./DecisionState";
import type { DecisionType } from "./DecisionType";

export interface Decision {
    id: string;
    entityId: string;
    type: DecisionType;
    priority: DecisionPriority;
    state: DecisionState;
    outcome: DecisionOutcome;
    confidence: number;
    createdAt: string;
}
