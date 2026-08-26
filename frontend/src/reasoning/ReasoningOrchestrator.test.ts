import { afterEach, describe, expect, it, vi } from "vitest";

import { RuleEngine, type EngineContext } from "@/engine";

import { ReasoningOrchestrator } from "./ReasoningOrchestrator";

const context: EngineContext = {
    entity: {
        id: "finding-test-001",
        title: "Test finding",
        description: "Non-sensitive test context",
        severity: "Low",
        status: "Open",
        riskScore: 1,
        confidence: { score: 0.1, evidenceCount: 0, dataQuality: 0.1, reason: "Test" },
        explainability: {
            reason: "Test",
            confidence: { score: 0.1, evidenceCount: 0, dataQuality: 0.1, reason: "Test" },
            businessImpact: "None",
            mitre: [],
            kev: null,
            epss: null,
            attackPath: [],
        },
        evidence: [],
        correlations: [],
    },
    knowledge: [],
    knowledgeBindings: [],
    evidence: [],
    correlations: [],
};

describe("ReasoningOrchestrator session identity", () => {
    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("uses a local non-authoritative ID when randomUUID is unavailable", () => {
        vi.stubGlobal("crypto", {});
        const session = new ReasoningOrchestrator(new RuleEngine({ rules: [] }))
            .execute(context);

        expect(session.status).toBe("completed");
        expect(session.id).toMatch(/^reasoning-session-/);
    });

    it("returns a controlled failed session when ID generation fails", () => {
        const session = new ReasoningOrchestrator(
            new RuleEngine({ rules: [] }),
            () => {
                throw new Error("ID generation failed");
            },
        ).execute(context);

        expect(session.status).toBe("failed");
        expect(session.error).toBe("Reasoning execution could not be completed.");
        expect(session.error).not.toContain("ID generation failed");
    });
});
