import { afterEach, describe, expect, it, vi } from "vitest";

import { generateFindingExplanation } from "./FindingsApiClient";

const responsePayload = {
    finding_id: "finding/id",
    generation_status: "GENERATED",
    factual_context: [],
    missing_context: [],
    provider_id: "openai",
    model_id: "gpt-5.6-terra",
    input_contract_version: "1.0",
    input_digest: "digest",
    used_fact_ids: [],
    source_references: [],
    model_output: {
        summary: {
            kind: "GENERAL_SECURITY_REASONING",
            text: "Summary",
            basis_fact_ids: [],
        },
        technical_reasoning: [],
        organizational_relevance: [],
        uncertainty_statement: {
            kind: "GENERAL_SECURITY_REASONING",
            text: "Uncertainty",
            basis_fact_ids: [],
        },
    },
};

afterEach(() => {
    vi.unstubAllGlobals();
});

describe("generateFindingExplanation", () => {
    it("posts to the selected finding explanation endpoint", async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(responsePayload), {
                status: 200,
                headers: { "Content-Type": "application/json" },
            }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(generateFindingExplanation("finding/id")).resolves.toEqual(
            responsePayload,
        );
        expect(fetchMock).toHaveBeenCalledOnce();
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/findings/finding%2Fid/explanation",
            { method: "POST" },
        );
    });
});
