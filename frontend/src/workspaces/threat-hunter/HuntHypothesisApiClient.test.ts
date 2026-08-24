import { afterEach, describe, expect, it, vi } from "vitest";

import {
    getHuntHypothesisReferenceResolution,
    HuntHypothesisRequestError,
} from "./HuntHypothesisApiClient";

const resolution = {
    hypothesis_id: "hypothesis/001",
    references: [
        {
            reference_type: "finding",
            reference_id: "finding-001",
            resolution_status: "resolved",
            authoritative_source: "findings",
            resolved_identity: "finding-001",
            source_reference: "greenbone",
        },
    ],
};

afterEach(() => {
    vi.unstubAllGlobals();
});

describe("getHuntHypothesisReferenceResolution", () => {
    it("requests only the selected hypothesis resolution endpoint", async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(resolution), { status: 200 }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(
            getHuntHypothesisReferenceResolution("hypothesis/001"),
        ).resolves.toEqual(resolution);
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/hunt-hypotheses/hypothesis%2F001/reference-resolution",
        );
    });

    it("rejects unknown resolution states", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue(
                new Response(
                    JSON.stringify({
                        ...resolution,
                        references: [
                            { ...resolution.references[0], resolution_status: "confirmed" },
                        ],
                    }),
                    { status: 200 },
                ),
            ),
        );

        await expect(
            getHuntHypothesisReferenceResolution("hypothesis/001"),
        ).rejects.toEqual(new HuntHypothesisRequestError(200));
    });
});
