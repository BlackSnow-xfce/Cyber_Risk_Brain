import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ComponentProps } from "react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { IncidentCommandCenterResponse } from "@/workspaces/incident-response/IncidentCommandCenter";
import DashboardPage from "./DashboardPage";

const findings = [
    { id: "finding-first", source: "sensor-a", title: "First finding", vendorSeverity: "Critical", asset: "asset-a" },
    { id: "finding-selected", source: "sensor-b", title: "Selected canonical finding", vendorSeverity: "High", asset: "asset-b" },
] as const;

const relationship = {
    incident_id: "incident-real-001",
    relationship_id: "relationship-001",
    relationship_role: "investigation_candidate",
    lifecycle_status: "investigating",
} as const;

const commandCenter: IncidentCommandCenterResponse = {
    contract_version: "1.0",
    incident: {
        incident_id: relationship.incident_id,
        lifecycle_status: "investigating",
        source: "incident-store",
        source_reference: "incident:001",
        title: "Canonical incident title",
        description: "Persisted incident description",
        created_at: "2026-08-20T10:00:00Z",
        updated_at: "2026-08-20T11:00:00Z",
        owner: null,
        participants: [],
    },
    findings: [{ reference_id: "finding-selected", source: "finding-store", contract_version: null, version_id: null, evidence_snapshot_id: null }],
    assets: [],
    threat_intelligence: [],
    evidence: [{ reference_id: "evidence-002", source: "evidence-store", contract_version: null, version_id: null, evidence_snapshot_id: "snapshot-2" }],
    decisions: [],
    notes: [],
    activities: [
        { activity_id: "activity-2", incident_id: relationship.incident_id, activity_type: "updated", actor: { principal_type: "user", principal_id: "analyst" }, occurred_at: "2026-08-20T11:00:00Z", sequence: 2, description: "Second persisted activity", details: [], contract_version: "1.0" },
        { activity_id: "activity-1", incident_id: relationship.incident_id, activity_type: "created", actor: { principal_type: "system", principal_id: "api" }, occurred_at: "2026-08-20T10:00:00Z", sequence: 1, description: "First persisted activity", details: [], contract_version: "1.0" },
    ],
    sections: [],
    completeness: { status: "available", source_type: "incident_command_center_read_model", source_reference: "incident-command-center:1.0:incident-real-001" },
    missing_context: [],
};

function LocationProbe() {
    const location = useLocation();
    return <output data-testid="location">{location.pathname}{location.search}</output>;
}

function renderDashboard(path = "/?findingId=finding-selected", overrides: Partial<ComponentProps<typeof DashboardPage>> = {}) {
    const props = {
        loadFindings: vi.fn().mockResolvedValue(findings),
        loadFindingIncidents: vi.fn().mockResolvedValue([relationship]),
        loadIncident: vi.fn().mockResolvedValue(commandCenter),
        ...overrides,
    };
    render(<MemoryRouter initialEntries={[path]}><DashboardPage {...props} /><LocationProbe /></MemoryRouter>);
    return props;
}

describe("SOC dashboard canonical investigation context", () => {
    afterEach(cleanup);

    it("selects only the exact URL findingId and loads only its incident context", async () => {
        const props = renderDashboard();
        expect(await screen.findByRole("heading", { name: "Selected canonical finding" })).toBeInTheDocument();
        expect(screen.queryByText("First finding")).not.toBeInTheDocument();
        await waitFor(() => expect(props.loadFindingIncidents).toHaveBeenCalledTimes(1));
        expect(props.loadFindingIncidents).toHaveBeenCalledWith("finding-selected");
    });

    it("does not present the non-functional findings search control", async () => {
        renderDashboard();
        await screen.findByRole("heading", { name: "Selected canonical finding" });
        expect(screen.queryByLabelText("Search findings")).not.toBeInTheDocument();
    });

    it.each([
        ["missing", "/", "Select a finding to open an investigation dashboard."],
        ["invalid", "/?findingId=unknown", "The requested findingId does not match a loaded canonical finding."],
    ])("shows one targeted %s-context state with the Findings entry point", async (_name, path, detail) => {
        const props = renderDashboard(path);
        expect(await screen.findByText(detail)).toBeInTheDocument();
        expect(screen.getAllByRole("button", { name: "Open Findings" })).toHaveLength(1);
        expect(props.loadFindingIncidents).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: "Open Findings" }));
        expect(screen.getByTestId("location")).toHaveTextContent("/findings");
    });

    it("distinguishes loading, empty and retrieval failure states", async () => {
        const pending = new Promise<readonly never[]>(() => undefined);
        renderDashboard("/", { loadFindings: () => pending });
        expect(screen.getByText("Loading SOC dashboard")).toBeInTheDocument();
        cleanup();
        renderDashboard("/", { loadFindings: vi.fn().mockResolvedValue([]) });
        expect(await screen.findByText("No live findings available.")).toBeInTheDocument();
        cleanup();
        renderDashboard("/", { loadFindings: vi.fn().mockRejectedValue(new Error("offline")) });
        expect(await screen.findByText("Live findings could not be loaded.")).toBeInTheDocument();
    });

    it("projects persisted incident identity, evidence and activities in supplied order", async () => {
        renderDashboard();
        expect(await screen.findByText("Canonical incident title")).toBeInTheDocument();
        expect(screen.getByText("investigation_candidate")).toBeInTheDocument();
        expect(screen.getByText(/evidence-002/)).toBeInTheDocument();
        const activities = within(screen.getByLabelText("Chronological timeline")).getByRole("list").textContent;
        expect(activities?.indexOf("Second persisted activity")).toBeLessThan(activities?.indexOf("First persisted activity") ?? 0);
        expect(screen.getByText("Authoritative analysis is unavailable.")).toBeInTheDocument();
        expect(screen.queryByText(/priority|confidence|business impact|compromised|remediation/i)).not.toBeInTheDocument();
    });

    it("renders exactly five canonical operational instruments and only persisted graph relationships", async () => {
        renderDashboard();
        await screen.findByText("Canonical incident title");
        const metrics = within(screen.getByRole("region", { name: "Operational metrics" })).getAllByRole("article");
        expect(metrics).toHaveLength(5);
        expect(metrics.map((metric) => metric.textContent)).toEqual(expect.arrayContaining([
            expect.stringContaining("finding-selected"),
            expect.stringContaining("High"),
            expect.stringContaining("asset-b"),
            expect.stringContaining("incident-real-001"),
            expect.stringContaining("Loaded"),
        ]));
        const graph = screen.getByRole("img", { name: "Canonical investigation relationships" });
        expect(graph.querySelector('[data-relationship="finding-asset"]')).not.toBeNull();
        expect(graph.querySelector('[data-relationship="finding-incident"]')).not.toBeNull();
        expect(graph).toHaveTextContent("investigation_candidate");
        expect(graph).not.toHaveTextContent("RELATED");
    });

    it("keeps analysis unavailable and exposes four distinct authoritative drill-downs", async () => {
        renderDashboard();
        await screen.findByText("Canonical incident title");
        expect(screen.getByText("Authoritative analysis is unavailable.")).toBeInTheDocument();
        for (const name of ["Open Finding", "Open Threat Intelligence", "Open Incident", "Open Command Center"]) {
            expect(screen.getAllByRole("button", { name })).not.toHaveLength(0);
        }
    });

    it("opens Finding, Threat Intelligence and the prominent Command Center route", async () => {
        renderDashboard();
        await screen.findByText("Canonical incident title");
        fireEvent.click(screen.getByRole("button", { name: "Open Threat Intelligence" }));
        expect(screen.getByTestId("location")).toHaveTextContent("/findings?findingId=finding-selected&focus=threat-intelligence");
        fireEvent.click(screen.getByRole("button", { name: "Open Command Center" }));
        expect(screen.getByTestId("location")).toHaveTextContent("/incident-response/incidents/incident-real-001/command-center");
    });

    it("keeps incident retrieval failure visible and makes no Command Center call", async () => {
        const loadIncident = vi.fn();
        renderDashboard("/?findingId=finding-selected", {
            loadFindingIncidents: vi.fn().mockRejectedValue(new Error("offline")),
            loadIncident,
        });
        expect(await screen.findByText("Finding-to-Incident context could not be loaded.")).toBeInTheDocument();
        expect(loadIncident).not.toHaveBeenCalled();
        expect(screen.queryByRole("button", { name: "Open Command Center" })).not.toBeInTheDocument();
    });

    it("keeps the persisted Command Center path when incident detail retrieval fails", async () => {
        renderDashboard("/?findingId=finding-selected", {
            loadIncident: vi.fn().mockRejectedValue(new Error("offline")),
        });

        expect(await screen.findByText("Incident Command Center context could not be loaded.")).toBeInTheDocument();
        expect(screen.getByText("Canonical incident details are not available in this dashboard.")).toBeInTheDocument();
        expect(screen.queryByText("Canonical incident title")).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Open Command Center" }));
        expect(screen.getByTestId("location")).toHaveTextContent("/incident-response/incidents/incident-real-001/command-center");
    });

    it("refreshes the same URL-authoritative context", async () => {
        const loadFindings = vi.fn().mockResolvedValue(findings);
        renderDashboard("/?findingId=finding-selected", { loadFindings });
        await screen.findByText("Canonical incident title");
        fireEvent.click(await screen.findByRole("button", { name: "Refresh" }));
        await waitFor(() => expect(loadFindings).toHaveBeenCalledTimes(2));
        expect(screen.getByTestId("location")).toHaveTextContent("/?findingId=finding-selected");
    });
});
