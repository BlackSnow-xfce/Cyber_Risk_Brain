import { afterEach, describe, expect, it, vi } from "vitest";

import {
    createHuntHypothesis,
    getLocalOperatorSession,
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

describe("Local Operator session creation transport", () => {
    it("loads only safe session metadata with credentialed fetch", async () => {
        const session = {
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:create"],
            expires_at: "2026-08-24T15:30:00Z",
            csrf_token: "csrf-token",
        };
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(session), { status: 200 }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(getLocalOperatorSession()).resolves.toEqual(session);
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/operator/session",
            { credentials: "include" },
        );
    });

    it("posts only human-authored fields with credentials and CSRF", async () => {
        const input = {
            title: "Manual hypothesis",
            statement: "Investigate an assumption.",
            rationale: "Human review is warranted.",
            target_references: [{ reference_type: "asset", reference_id: "asset-001" }],
            threat_references: [{ reference_type: "cve", reference_id: "CVE-2004-2687" }],
        };
        const created = {
            ...input,
            hypothesis_id: "hypothesis-created",
            status: "draft",
            created_at: "2026-08-24T15:00:00Z",
            created_by: "product-owner",
            contract_version: "1.0",
        };
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(created), { status: 201 }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(createHuntHypothesis(input, "csrf-token")).resolves.toEqual(created);
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/hunt-hypotheses",
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": "csrf-token",
                },
                body: JSON.stringify(input),
            },
        );
        expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual(input);
    });
});
