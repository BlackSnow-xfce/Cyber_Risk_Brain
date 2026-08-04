import type { EngineContext, EngineResult } from "@/engine";

import type { ReasoningSessionStatus } from "./ReasoningSessionStatus";

export interface ReasoningSession {
    id: string;
    entityId: EngineContext["entity"]["id"];
    status: ReasoningSessionStatus;
    startedAt: string;
    completedAt?: string;
    result?: EngineResult;
    error?: string;
}
