import { readFileSync } from "node:fs";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { IncidentQueueItem } from "../IncidentQueue";
import IncidentResponseOverviewPage from "./IncidentResponseOverviewPage";

const styles = readFileSync("src/workspaces/incident-response/pages/IncidentResponseOverviewPage.css", "utf8");
const baseIncident: IncidentQueueItem = {
    incident_id: "IR / canonical?one",
    lifecycle_status: "open",
    source: "canonical-source",
    source_reference: "reference",
    title: "Canonical active incident",
    created_at: "2026-08-20T10:00:00Z",
    updated_at: "2026-08-21T11:00:00Z",
    owner: null,
    participant_count: 0,
    finding_count: 0,
    asset_count: 0,
    threat_intelligence_count: 0,
    evidence_count: 0,
};

afterEach(cleanup);

function renderOverview(loadIncidents: () => Promise<IncidentQueueItem[]>) {
    return render(<MemoryRouter><IncidentResponseOverviewPage loadIncidents={loadIncidents} /></MemoryRouter>);
}

describe("Incident Response overview", () => {
    it("implements the measured page hierarchy and geometry contract", () => {
        expect(declaration(".incident-overview", "padding")).toBe("0 20px 0 15px");
        expect(declaration(".incident-snapshot", "height")).toBe("200px");
        expect(declaration(".incident-snapshot__grid", "gap")).toBe("13px");
        expect(declaration(".snapshot-instrument", "height")).toBe("131px");
        expect(declaration(".incident-overview__grid", "grid-template-columns")).toContain("613fr");
        expect(declaration(".incident-overview__grid", "grid-template-columns")).toContain("596fr");
        expect(declaration(".incident-overview__grid", "gap")).toBe("14px");
        expect(declaration(".incident-overview__grid--middle>.incident-panel", "height")).toBe("373px");
        expect(declaration(".incident-overview__grid--lower>.incident-panel", "height")).toBe("325px");
        expect(declaration(".incident-panel", "border")).toBe("1px solid var(--border)");
        expect(declaration(".incident-panel", "border-radius")).toBe("8px");
    });

    it("renders five ordered snapshot instruments and truthful unavailable regions", async () => {
        renderOverview(() => Promise.resolve([]));
        await screen.findByText("No persisted incidents are available.");
        const instruments = screen.getAllByRole("article");
        expect(instruments).toHaveLength(5);
        expect(instruments.map((item) => item.querySelector("h3")?.textContent)).toEqual([
            "Active Incidents", "Critical Incidents", "MTTR", "Contained Incidents", "Open Tasks",
        ]);
        expect(screen.getAllByText("Unavailable")).toHaveLength(5);
        expect(screen.getAllByText("Not connected")).toHaveLength(2);
        for (const heading of ["Response Status", "Response Playbooks", "Recent Activity"]) {
            expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
        }
        expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    it("distinguishes loading, error, empty queue, and no-active states", async () => {
        renderOverview(() => new Promise(() => undefined));
        expect(screen.getByText("Loading incidents...")).toBeInTheDocument();
        cleanup();
        renderOverview(() => Promise.reject(new Error("offline")));
        expect(await screen.findByRole("alert")).toHaveTextContent("Incident queue could not be loaded.");
        cleanup();
        renderOverview(() => Promise.resolve([]));
        expect(await screen.findByText("No persisted incidents are available.")).toBeInTheDocument();
        cleanup();
        renderOverview(() => Promise.resolve([{ ...baseIncident, lifecycle_status: "resolved" }]));
        expect(await screen.findByText("No active incidents are available.")).toBeInTheDocument();
    });

    it("loads once, filters exact active statuses, searches canonical fields, and preserves encoded identity", async () => {
        const incidents = [
            baseIncident,
            { ...baseIncident, incident_id: "investigating", title: "Investigating incident", lifecycle_status: "investigating" },
            { ...baseIncident, incident_id: "resolved", title: "Resolved incident", lifecycle_status: "resolved" },
            { ...baseIncident, incident_id: "closed", title: "Closed incident", lifecycle_status: "closed" },
            { ...baseIncident, incident_id: "unknown", title: "Unknown incident", lifecycle_status: "ACTIVE" },
        ];
        const loader = vi.fn().mockResolvedValue(incidents);
        renderOverview(loader);
        expect(await screen.findByText("Canonical active incident")).toBeInTheDocument();
        expect(loader).toHaveBeenCalledOnce();
        expect(screen.getByText("Investigating incident")).toBeInTheDocument();
        expect(screen.queryByText("Resolved incident")).not.toBeInTheDocument();
        expect(screen.queryByText("Closed incident")).not.toBeInTheDocument();
        expect(screen.queryByText("Unknown incident")).not.toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Canonical active incident/ })).toHaveAttribute("href", "/incident-response/incidents/IR%20%2F%20canonical%3Fone/command-center");
        fireEvent.change(screen.getByRole("textbox", { name: "Search active incidents" }), { target: { value: "INVESTIGATING" } });
        expect(screen.queryByText("Canonical active incident")).not.toBeInTheDocument();
        expect(screen.getByText("Investigating incident")).toBeInTheDocument();
    });

    it("contains no inferred incident semantics or illustrative mockup rows", async () => {
        renderOverview(() => Promise.resolve([baseIncident]));
        await screen.findByText("Canonical active incident");
        for (const fabricated of ["Critical count", "Containment rate", "Response percentage", "Playbook row", "Recent timeline"]) {
            expect(screen.queryByText(fabricated)).not.toBeInTheDocument();
        }
    });
});

function declaration(selector: string, property: string): string {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const rule = styles.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`))?.[1] ?? "";
    const value = rule.match(new RegExp(`${property}\\s*:\\s*([^;]+)`))?.[1];
    expect(value, `Missing ${property} in ${selector}`).toBeDefined();
    return value?.trim() ?? "";
}
