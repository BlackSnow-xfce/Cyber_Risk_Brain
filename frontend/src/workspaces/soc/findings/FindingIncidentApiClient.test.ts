import { afterEach, describe, expect, it, vi } from "vitest";

import {
    FindingIncidentRequestError,
    getFindingIncidents,
} from "./FindingIncidentApiClient";

describe("FindingIncidentApiClient", () => {
    afterEach(() => vi.restoreAllMocks());

    it("uses the finding incident query endpoint", async () => {
        const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
            new Response(
                JSON.stringify([
                    {
                        incident_id: "incident-001",
                        relationship_id: "relationship-001",
                        relationship_role: "investigation_candidate",
                        lifecycle_status: "investigating",
                    },
                ]),
                { status: 200 },
            ),
        );

        await getFindingIncidents("finding/1");

        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining("/api/findings/finding%2F1/incidents"),
        );
    });

    it("preserves controlled HTTP errors", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue(
            new Response("", { status: 503 }),
        );

        await expect(getFindingIncidents("finding-1")).rejects.toEqual(
            new FindingIncidentRequestError(503),
        );
    });
});
