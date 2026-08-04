import {
    RuleEngine,
    type EngineContext,
} from "@/engine";

import type { ReasoningSession } from "./ReasoningSession";

export class ReasoningOrchestrator {
    constructor(private readonly ruleEngine: RuleEngine) {}

    execute(context: EngineContext): ReasoningSession {
        const id = crypto.randomUUID();
        const startedAt = new Date().toISOString();
        const session: ReasoningSession = {
            id,
            entityId: context.entity.id,
            status: "running",
            startedAt,
        };

        try {
            const result = this.ruleEngine.evaluate(context);

            return {
                ...session,
                status: "completed",
                completedAt: new Date().toISOString(),
                result,
            };
        } catch (error) {
            return {
                ...session,
                status: "failed",
                completedAt: new Date().toISOString(),
                error: String(error),
            };
        }
    }
}
