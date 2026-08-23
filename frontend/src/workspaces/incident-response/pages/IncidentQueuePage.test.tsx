import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { IncidentQueueItem } from "../IncidentQueue";
import { getIncidents } from "../IncidentQueueApiClient";
import IncidentQueuePage from "./IncidentQueuePage";

vi.mock("../IncidentQueueApiClient", () => ({
    getIncidents: vi.fn(),
    IncidentQueueRequestError: class IncidentQueueRequestError extends Error {},
}));

const incidents: IncidentQueueItem[] = [
    {
        incident_id: "incident-task0077-distcc-live",
        lifecycle_status: "investigating",
        source: "controlled-lab",
        source_reference: "source:distcc",
        title: "DistCC investigation",
        created_at: "2026-08-01T00:00:00Z",
        updated_at: "2026-08-02T00:00:00Z",
        owner: { principal_type: "user", principal_id: "soc-analyst-task0078" },
        participant_count: 1,
        finding_count: 1,
        asset_count: 1,
        threat_intelligence_count: 1,
        evidence_count: 1,
    },
    {
        incident_id: "incident-other",
        lifecycle_status: "open",
        source: "greenbone",
        source_reference: "source:other",
        title: "Other investigation",
        created_at: "2026-08-01T00:00:00Z",
        updated_at: "2026-08-02T00:00:00Z",
        owner: null,
        participant_count: 0,
        finding_count: 0,
        asset_count: 0,
        threat_intelligence_count: 0,
        evidence_count: 0,
    },
];

describe("IncidentQueuePage", () => {
    afterEach(() => cleanup());

    beforeEach(() => {
        vi.mocked(getIncidents).mockResolvedValue(incidents);
    });

    it("filters canonical incidents and restores the complete queue", async () => {
        render(<MemoryRouter><IncidentQueuePage /></MemoryRouter>);
        await screen.findByText("DistCC investigation");

        expect(screen.getAllByText(/Created/)[0]).toBeInTheDocument();
        expect(screen.getByText(/Participants 1/)).toHaveTextContent(
            "Participants 1 · Findings 1 · Assets 1 · TI 1 · Evidence 1",
        );

        const search = screen.getByRole("textbox", { name: "Search incidents" });
        fireEvent.change(search, { target: { value: "DISTCC" } });
        expect(screen.getByText("DistCC investigation")).toBeInTheDocument();
        expect(screen.queryByText("Other investigation")).not.toBeInTheDocument();

        fireEvent.change(search, { target: { value: "no-match" } });
        expect(screen.getByText(/No incidents match/)).toBeInTheDocument();

        fireEvent.change(search, { target: { value: "" } });
        expect(screen.getByText("Other investigation")).toBeInTheDocument();
    });

    it("preserves the exact incident identity for Command Center navigation", async () => {
        render(<MemoryRouter><IncidentQueuePage /></MemoryRouter>);
        await screen.findByText("DistCC investigation");

        expect(screen.getAllByRole("link", { name: "Open Command Center" })[0]).toHaveAttribute(
            "href",
            "/incident-response/incidents/incident-task0077-distcc-live/command-center",
        );
    });

    it("shows a transparent API error state", async () => {
        vi.mocked(getIncidents).mockRejectedValueOnce(new Error("offline"));

        render(<MemoryRouter><IncidentQueuePage /></MemoryRouter>);

        expect(await screen.findByText("Incident queue could not be loaded.")).toBeInTheDocument();
        expect(screen.queryByText("No persisted incidents are available.")).not.toBeInTheDocument();
    });

    it("shows the explicit empty state for an empty persisted queue", async () => {
        vi.mocked(getIncidents).mockResolvedValueOnce([]);

        render(<MemoryRouter><IncidentQueuePage /></MemoryRouter>);

        expect(await screen.findByText("No persisted incidents are available.")).toBeInTheDocument();
        expect(screen.queryByText("Incident queue could not be loaded.")).not.toBeInTheDocument();
        expect(screen.queryByText(/No incidents match/)).not.toBeInTheDocument();
    });
});
