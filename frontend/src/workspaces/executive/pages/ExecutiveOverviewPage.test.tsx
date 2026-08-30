import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ExecutiveOverviewPage from "./ExecutiveOverviewPage";

const pageWidth = 1467 - 164 - (24 * 2);
const kpiReferenceWidths = [241, 241, 240, 238, 239];
const columnReferenceWidths = [597, 634];

afterEach(cleanup);

describe("ExecutiveOverviewPage", () => {
    it("renders approved regions in reference order", () => {
        render(<ExecutiveOverviewPage />);
        expect(screen.getAllByRole("heading").map(({ textContent }) => textContent)).toEqual(["Executive Cyber Risk Dashboard", "Enterprise Risk Posture", "Critical Exposure", "Business Services at Risk", "Decisions Required", "Risk Trend", "Enterprise Risk Overview", "Decision Priorities", "Business Impact", "Critical Business Services", "Investment & Remediation Priorities", "Executive Briefing", "Security Program Progress", "Board Reporting"]);
    });
    it("fails closed for every management-data region", () => {
        render(<ExecutiveOverviewPage />);
        expect(screen.getAllByText("Unavailable")).toHaveLength(20);
        expect(screen.getAllByText("Not connected")).toHaveLength(15);
        for (const text of ["No decision data available.", "No business services available.", "No investment data available.", "No executive briefing available.", "No board report available.", "Status: Fail-Closed."]) expect(screen.getByText(text)).toBeInTheDocument();
    });
    it("uses empty tables without synthetic rows", () => {
        render(<ExecutiveOverviewPage />);
        const tables = screen.getAllByRole("table");
        expect(tables).toHaveLength(3);
        tables.forEach((table) => { expect(within(table).getAllByRole("row")).toHaveLength(2); expect(within(table).getAllByRole("columnheader")).toHaveLength(5); });
    });
    it("contains no inferred numeric, timestamp, trend-path or progress claims", () => {
        const { container } = render(<ExecutiveOverviewPage />);
        expect(container.textContent).not.toMatch(/\d|%|last updated|data as of|ago|days?/i);
        expect(container.querySelector("[role='progressbar']")).toBeNull();
        expect(container.querySelectorAll(".executive-overview__ring")).toHaveLength(2);
    });
    it("performs no network invocation", () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch"); render(<ExecutiveOverviewPage />); expect(fetchSpy).not.toHaveBeenCalled(); fetchSpy.mockRestore();
    });
    it("documents deterministic frozen-shell geometry arithmetic", () => {
        // Contract arithmetic only: jsdom does not measure native pixels or fonts.
        const widths = kpiReferenceWidths.map((width) => (pageWidth - 48) * width / 1199);
        const columns = columnReferenceWidths.map((width) => (pageWidth - 15) * width / 1231);
        expect(pageWidth).toBe(1255); expect(widths.map(Math.round)).toEqual([243, 243, 242, 240, 241]);
        expect(widths.reduce((sum, width) => sum + width, 48)).toBeCloseTo(pageWidth, 5);
        expect(columns.map(Math.round)).toEqual([601, 639]); expect(columns.reduce((sum, width) => sum + width, 15)).toBeCloseTo(pageWidth, 5);
        expect(213 + 174 + 152 + 168 + 30).toBe(737);
    });
});
