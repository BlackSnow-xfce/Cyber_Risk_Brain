import {
    defaultRulePackRegistry,
    RuleEngine,
} from "@/engine";

import { ReasoningOrchestrator } from "./ReasoningOrchestrator";

export const defaultReasoningOrchestrator =
    new ReasoningOrchestrator(
        new RuleEngine(defaultRulePackRegistry),
    );
