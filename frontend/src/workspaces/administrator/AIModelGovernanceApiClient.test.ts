import { afterEach, describe, expect, it, vi } from "vitest";

import {
    AIModelGovernanceRequestError,
    getAIModelGovernance,
    updateAIModelSelection,
} from "./AIModelGovernanceApiClient";

describe("AIModelGovernanceApiClient", () => {
    afterEach(() => vi.unstubAllGlobals());

    it("loads the read-only governance endpoint", async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({
                contract_version: "1.0",
                capabilities: ["finding_explanation"],
                providers: [],
            }),
        });
        vi.stubGlobal("fetch", fetchMock);

        await expect(getAIModelGovernance()).resolves.toMatchObject({ contract_version: "1.0" });
        expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/ai-model-governance");
    });

    it("fails closed for a malformed projection", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({ providers: "not-a-list" }),
        }));

        await expect(getAIModelGovernance()).rejects.toBeInstanceOf(AIModelGovernanceRequestError);
    });

    it("submits only the canonical identity with session credentials and CSRF", async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({
                contract_version: "1.0",
                capabilities: [],
                providers: [],
            }),
        });
        vi.stubGlobal("fetch", fetchMock);

        await updateAIModelSelection("finding_explanation", "openai", "gpt-5.6", "csrf-value");

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/ai-model-governance/selections/finding_explanation",
            expect.objectContaining({
                method: "PUT",
                credentials: "include",
                body: JSON.stringify({ provider: "openai", model_id: "gpt-5.6" }),
            }),
        );
    });
});
