import {
    RuleEngine,
    type EngineContext,
} from "@/engine";

import type { ReasoningSession } from "./ReasoningSession";

export class ReasoningOrchestrator {
    constructor(
        private readonly ruleEngine: RuleEngine,
        private readonly createSessionId: () => string = createReasoningSessionId,
    ) {}

    execute(context: EngineContext): ReasoningSession {
        let id: string | null = null;
        let startedAt: string | null = null;

        try {
            id = this.createSessionId();
            startedAt = new Date().toISOString();
            const session: ReasoningSession = {
                id,
                entityId: context.entity.id,
                status: "running",
                startedAt,
            };
            const result = this.ruleEngine.evaluate(context);

            return {
                ...session,
                status: "completed",
                completedAt: new Date().toISOString(),
                result,
            };
        } catch (error) {
            return {
                id: id ?? createLocalSessionId(),
                entityId: context.entity.id,
                status: "failed",
                startedAt: startedAt ?? new Date().toISOString(),
                completedAt: new Date().toISOString(),
                error: "Reasoning execution could not be completed.",
            };
        }
    }
}

let localSessionSequence = 0;

function createReasoningSessionId(): string {
    const randomUUID = globalThis.crypto?.randomUUID;
    if (typeof randomUUID === "function") {
        return randomUUID.call(globalThis.crypto);
    }
    return createLocalSessionId();
}

function createLocalSessionId(): string {
    localSessionSequence += 1;
    return `reasoning-session-${Date.now().toString(36)}-${localSessionSequence.toString(36)}`;
}
