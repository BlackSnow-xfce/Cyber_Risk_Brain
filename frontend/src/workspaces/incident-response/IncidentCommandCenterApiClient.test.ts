import { describe, expect, it, vi } from "vitest";

import { getIncidentCommandCenter, IncidentCommandCenterRequestError } from "./IncidentCommandCenterApiClient";

const payload = {
    contract_version: "1.0",
    incident: {
        incident_id: "incident-real-001",
        lifecycle_status: "investigating",
        source: "lab",
        source_reference: "lab:incident-real-001",
        title: "Controlled lab incident",
        description: null,
        created_at: "2026-08-18T10:00:00Z",
        updated_at: "2026-08-18T10:00:00Z",
        owner: null,
        participants: [],
    },
    findings: [], assets: [], threat_intelligence: [], evidence: [], decisions: [],
    notes: [], activities: [], sections: [],
    completeness: { status: "no_data", source_type: "read", source_reference: "read:1" },
    missing_context: [],
};

describe("IncidentCommandCenterApiClient", () => {
    it("requests exactly the selected incident endpoint", async () => {
        const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload });
        vi.stubGlobal("fetch", fetchMock);

        await getIncidentCommandCenter("incident-real-001");

        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining("/api/incidents/incident-real-001/command-center"),
        );
    });

    it.each([404, 503, 500])("preserves HTTP status %s", async (status) => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status }));
        await expect(getIncidentCommandCenter("incident-real-001")).rejects.toMatchObject(
            new IncidentCommandCenterRequestError(status),
        );
    });
});
