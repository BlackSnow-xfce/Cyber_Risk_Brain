import type { EngineContext } from "./EngineContext";
import type { RuleResult } from "./RuleResult";

export interface Rule {
    id: string;
    name: string;
    description: string;
    priority: number;
    enabled: boolean;
    evaluate: (context: EngineContext) => RuleResult;
}
