import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import type { IncidentCommandCenterResponse } from "../IncidentCommandCenter";
import { IncidentCommandCenterRequestError } from "../IncidentCommandCenterApiClient";
import IncidentCommandCenterPage from "./IncidentCommandCenterPage";

const result: IncidentCommandCenterResponse = {
    contract_version: "1.0",
    incident: {
        incident_id: "incident-real-001",
        lifecycle_status: "investigating",
        source: "controlled-lab",
        source_reference: "lab:incident-real-001",
        title: "Controlled lab incident",
        description: "Read-only context",
        created_at: "2026-08-18T10:00:00Z",
        updated_at: "2026-08-18T11:00:00Z",
        owner: { principal_type: "user", principal_id: "analyst-1" },
        participants: [{ principal: { principal_type: "team", principal_id: "soc" }, role: "analyst" }],
    },
    findings: [{ reference_id: "finding:greenbone:f-1", source: "greenbone", contract_version: null, version_id: null, evidence_snapshot_id: null }],
    assets: [{ reference_id: "asset:asset-lab-1", source: null, contract_version: null, version_id: null, evidence_snapshot_id: null }],
    threat_intelligence: [], evidence: [], decisions: [],
    notes: [{ note_id: "note-1", note_version_id: "note-1:v1", incident_id: "incident-real-001", author: { principal_type: "user", principal_id: "analyst-1" }, content: "Observed lab context", created_at: "2026-08-18T10:30:00Z", version: 1, supersedes_version_id: null, contract_version: "1.0" }],
    activities: [{ activity_id: "activity-1", incident_id: "incident-real-001", activity_type: "opened", actor: { principal_type: "user", principal_id: "analyst-1" }, occurred_at: "2026-08-18T10:05:00Z", sequence: 1, description: "Incident opened", details: [], contract_version: "1.0" }],
    sections: [{ section: "finding", status: "available", reference_ids: ["finding:greenbone:f-1"], source_references: ["greenbone:f-1"], missing_context: [] }],
    completeness: { status: "available", source_type: "incident_command_center_read_model", source_reference: "incident-command-center:1.0:incident-real-001" },
    missing_context: [],
};

function renderPage(loadIncident = vi.fn().mockResolvedValue(result), incidentId = "incident-real-001") {
    return render(<MemoryRouter initialEntries={[`/incident-response/incidents/${incidentId}/command-center`]}><IncidentCommandCenterPage loadIncident={loadIncident} /></MemoryRouter>);
}

describe("IncidentCommandCenterPage", () => {
    it("renders loading and then the canonical context", async () => {
        renderPage();
        expect(screen.getByText("Loading incident command center…")).toBeInTheDocument();
        expect(await screen.findByText("Controlled lab incident")).toBeInTheDocument();
        expect(screen.getByText("finding:greenbone:f-1")).toBeInTheDocument();
        expect(screen.getByText("Observed lab context")).toBeInTheDocument();
        expect(screen.getByText("Incident opened")).toBeInTheDocument();
    });

    it("renders controlled errors", async () => {
        const loadIncident = vi.fn().mockRejectedValue(new IncidentCommandCenterRequestError(404));
        renderPage(loadIncident);
        expect(await screen.findByText("Incident was not found.")).toBeInTheDocument();
    });

    it("shows the no-id state without making a request", () => {
        const loadIncident = vi.fn();
        render(<MemoryRouter initialEntries={["/incident-response"]}><IncidentCommandCenterPage loadIncident={loadIncident} /></MemoryRouter>);
        expect(screen.getByText(/Open this view with an incident ID/)).toBeInTheDocument();
        expect(loadIncident).not.toHaveBeenCalled();
    });

    it("shows empty collections and missing context", async () => {
        const empty = { ...result, findings: [], assets: [], missing_context: ["evidence"] };
        renderPage(vi.fn().mockResolvedValue(empty));
        expect(await screen.findByText("No findings referenced.")).toBeInTheDocument();
        expect(screen.getByText("evidence")).toBeInTheDocument();
    });
});
