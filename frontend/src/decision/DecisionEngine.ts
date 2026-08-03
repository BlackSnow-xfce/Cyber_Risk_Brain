import type { Decision } from "./Decision";
import type { DecisionContext } from "./DecisionContext";

export interface DecisionEngine {
    decide: (context: DecisionContext) => Promise<Decision>;
}
