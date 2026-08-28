import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "./DashboardPage";
import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";
import type { IncidentCommandCenterResponse } from "@/workspaces/incident-response/IncidentCommandCenter";

const findings = [
    { id: "finding-first", source: "sensor", title: "First", vendorSeverity: "Critical", asset: "asset-a" },
    { id: "finding-selected", source: "sensor", title: "Selected canonical finding", vendorSeverity: "High", asset: "asset-b" },
] as const;
function Probe() { const location = useLocation(); return <output data-testid="location">{location.pathname}{location.search}</output>; }
function renderPage(
    path = "/",
    loadFindings: () => Promise<readonly FindingSummary[]> = vi.fn().mockResolvedValue(findings),
    loadFindingIncidents: (findingId: string) => Promise<readonly FindingIncidentReference[]> = vi.fn().mockResolvedValue([]),
    loadIncident: (incidentId: string) => Promise<IncidentCommandCenterResponse> = vi.fn(),
) {
    render(<MemoryRouter initialEntries={[path]}><DashboardPage loadFindings={loadFindings} loadFindingIncidents={loadFindingIncidents} loadIncident={loadIncident} /><Probe /></MemoryRouter>);
    return { loadFindings, loadFindingIncidents, loadIncident };
}

describe("DashboardPage Rework 7 projection", () => {
    afterEach(cleanup);
    it("loads the canonical collection and aggregates vendor severity", async () => {
        renderPage();
        const primary = await screen.findByRole("region", { name: "Primary dashboard metrics" });
        expect(within(primary).getByText("2")).toBeInTheDocument();
        expect(screen.getByText("Critical")).toBeInTheDocument();
        expect(screen.getByText("High")).toBeInTheDocument();
    });
    it("loads context only for an exact URL findingId", async () => {
        const { loadFindingIncidents } = renderPage("/?findingId=finding-selected");
        expect(await screen.findByText(/Selected canonical finding/)).toBeInTheDocument();
        await waitFor(() => expect(loadFindingIncidents).toHaveBeenCalledWith("finding-selected"));
    });
    it("fails closed for a manipulated findingId", async () => {
        const { loadFindingIncidents } = renderPage("/?findingId=unknown");
        await screen.findByText("Canonical findings collection");
        expect(loadFindingIncidents).not.toHaveBeenCalled();
        expect(screen.queryByText("First")).not.toBeInTheDocument();
    });
    it("preserves dashboard geometry for loading and error states", async () => {
        renderPage("/", () => new Promise(() => undefined));
        expect(screen.getByText("Loading")).toBeInTheDocument();
        cleanup();
        renderPage("/", vi.fn().mockRejectedValue(new Error("offline")));
        expect(await screen.findAllByText("Unavailable")).not.toHaveLength(0);
        expect(screen.getByRole("region", { name: "AI agents workspace" })).toBeInTheDocument();
    });
    it("does not invoke incident, provider or model paths without valid context", async () => {
        const { loadFindingIncidents, loadIncident } = renderPage();
        await screen.findByText("Canonical findings collection");
        expect(loadFindingIncidents).not.toHaveBeenCalled();
        expect(loadIncident).not.toHaveBeenCalled();
    });
    it("routes the real Findings action", async () => {
        renderPage("/?findingId=finding-selected");
        fireEvent.click(await screen.findByRole("button", { name: "View All Findings" }));
        expect(screen.getByTestId("location")).toHaveTextContent("/findings?findingId=finding-selected");
    });
});
