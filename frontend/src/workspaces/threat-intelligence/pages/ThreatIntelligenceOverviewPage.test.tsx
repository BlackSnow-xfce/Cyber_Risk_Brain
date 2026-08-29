import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import ThreatIntelligenceOverviewPage from "./ThreatIntelligenceOverviewPage";

afterEach(cleanup);
const finding = { id: "finding-real", title: "Canonical finding", asset: "asset-real", source: "scanner-real", vendorSeverity: "Provider rating" };
function renderOverview(loadFindings: () => Promise<readonly (typeof finding)[]>) { return render(<MemoryRouter><ThreatIntelligenceOverviewPage loadFindings={loadFindings} /><LocationProbe /></MemoryRouter>); }

describe("Threat Intelligence overview", () => {
    it("renders the measured hierarchy and five truthful snapshot instruments", async () => {
        renderOverview(() => Promise.resolve([finding]));
        expect(screen.getByRole("heading", { name: "Intelligence Snapshot" })).toBeInTheDocument();
        for (const label of ["Relevant Findings", "Active Campaigns", "Threat Actors", "New IOCs", "High Risk CVEs"]) expect(screen.getByText(label)).toBeInTheDocument();
        expect(await screen.findByText("1")).toBeInTheDocument();
        expect(screen.getAllByText("Not connected")).toHaveLength(4);
        expect(screen.getAllByText("Unavailable")).toHaveLength(3);
        for (const panel of ["Our Environment", "Threat Landscape", "Intelligence Feeds", "Recent Intelligence"]) expect(screen.getByRole("heading", { name: panel })).toBeInTheDocument();
    });

    it("keeps loading, retrieval error, and successful empty state distinct", async () => {
        renderOverview(() => new Promise(() => undefined));
        expect(screen.getByText("Loading")).toBeInTheDocument();
        expect(screen.queryByText("0")).not.toBeInTheDocument();
        cleanup();
        renderOverview(() => Promise.reject(new Error("unavailable")));
        expect(await screen.findByText("Internal findings are currently unavailable.")).toBeInTheDocument();
        expect(screen.queryByText("0")).not.toBeInTheDocument();
        cleanup();
        renderOverview(() => Promise.resolve([]));
        expect(await screen.findByText("0")).toBeInTheDocument();
        expect(screen.getByText("No internal findings are available.")).toBeInTheDocument();
    });

    it("reuses canonical search and exact finding navigation with one request", async () => {
        const loadFindings = vi.fn().mockResolvedValue([finding]);
        renderOverview(loadFindings);
        const search = await screen.findByRole("textbox", { name: "Search findings" });
        expect(loadFindings).toHaveBeenCalledOnce();
        expect(screen.getByText("Canonical finding")).toBeInTheDocument();
        fireEvent.change(search, { target: { value: "no match" } });
        expect(screen.getByText("No findings match the current search.")).toBeInTheDocument();
        fireEvent.change(search, { target: { value: "PROVIDER" } });
        fireEvent.click(screen.getByRole("button", { name: "Open finding-scoped Threat Intelligence" }));
        expect(screen.getByTestId("location")).toHaveTextContent("/findings?findingId=finding-real&focus=threat-intelligence");
    });

    it("contains no illustrative intelligence values or rows", async () => {
        renderOverview(() => Promise.resolve([]));
        await screen.findByText("0");
        for (const fabricated of ["52", "18", "23", "143", "31", "BlackBasta", "MISP Threat Feed"]) expect(screen.queryByText(fabricated)).not.toBeInTheDocument();
    });
});

function LocationProbe() { const location = useLocation(); return <output data-testid="location">{location.pathname}{location.search}</output>; }
