import { readFileSync } from "node:fs";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import ThreatIntelligenceOverviewPage from "./ThreatIntelligenceOverviewPage";

const overviewStyles = readFileSync("src/workspaces/threat-intelligence/pages/ThreatIntelligenceOverviewPage.css", "utf8");

afterEach(cleanup);
const finding = { id: "finding-real", title: "Canonical finding", asset: "asset-real", source: "scanner-real", vendorSeverity: "Provider rating" };
function renderOverview(loadFindings: () => Promise<readonly (typeof finding)[]>) { return render(<MemoryRouter><ThreatIntelligenceOverviewPage loadFindings={loadFindings} /><LocationProbe /></MemoryRouter>); }

describe("Threat Intelligence overview", () => {
    it("keeps the measured page, snapshot, and independent row geometry contracts", () => {
        const pageRule = cssRule(".ti-overview");
        const panelRule = cssRule(".ti-panel");
        const snapshotGridRule = cssRule(".ti-snapshot-grid");
        const snapshotCardRule = cssRule(".ti-snapshot-card");
        const lowerPanelRule = cssRule(".ti-feeds, .ti-recent");

        const [rightInset, , leftInset] = pixelValues(declaration(pageRule, "padding"));
        expect(leftInset).toBeCloseTo(19, 4);
        expect(rightInset).toBeCloseTo(17, 4);
        expect(leftInset).not.toBe(2);
        expect(rightInset).not.toBe(2);

        const snapshotWidths = pixelValues(declaration(snapshotGridRule, "grid-template-columns"));
        const snapshotGap = pixelValues(declaration(snapshotGridRule, "gap"))[0];
        expect(snapshotWidths).toEqual([199, 204, 224, 224, 204]);
        expect(declaration(snapshotGridRule, "grid-template-columns")).not.toContain("repeat(5");
        expect(pixelValues(declaration(snapshotCardRule, "height"))[0]).toBe(105);
        expect(snapshotGap).toBe(13);
        const panelHorizontalPadding = pixelValues(declaration(panelRule, "padding"))[1] * 2;
        const snapshotInnerWidth = 1219 - leftInset - rightInset - panelHorizontalPadding - 2;
        expect(snapshotWidths.reduce((sum, width) => sum + width, 0) + (4 * snapshotGap)).toBeLessThanOrEqual(snapshotInnerWidth);

        const tracks = fractionValues(declaration(pageRule, "grid-template-columns"));
        const middleLeft = tracks[0] + tracks[1] + tracks[2];
        const middleGap = tracks[3];
        const middleRight = tracks[4];
        expect(middleLeft / middleRight).toBeCloseTo(749 / 420, 3);
        expect(middleGap).toBe(14);

        const bottomLeft = tracks[0];
        const bottomGap = tracks[1];
        const bottomRight = tracks[2] + tracks[3] + tracks[4];
        expect([bottomLeft, bottomRight]).toEqual([573, 594]);
        expect(bottomLeft / bottomRight).toBeCloseTo(0.965, 3);
        expect(bottomGap).toBe(16);
        expect(bottomLeft / bottomRight).not.toBeCloseTo(1.78, 1);
        expect(pixelValues(declaration(lowerPanelRule, "height"))[0]).toBe(411);
    });

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

function cssRule(selector: string): string {
    const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const match = overviewStyles.match(new RegExp(`${escapedSelector}\\s*\\{([^}]*)\\}`));
    expect(match, `Missing CSS rule ${selector}`).not.toBeNull();
    return match?.[1] ?? "";
}

function declaration(rule: string, property: string): string {
    const match = rule.match(new RegExp(`${property}\\s*:\\s*([^;]+)`));
    expect(match, `Missing CSS declaration ${property}`).not.toBeNull();
    return match?.[1].trim() ?? "";
}

function pixelValues(value: string): number[] {
    return [...value.matchAll(/([\d.]+)px/g)].map((match) => Number(match[1]));
}

function fractionValues(value: string): number[] {
    return [...value.matchAll(/([\d.]+)fr/g)].map((match) => Number(match[1]));
}
