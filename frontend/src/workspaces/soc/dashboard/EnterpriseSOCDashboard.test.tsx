import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import EnterpriseSOCDashboard from "./EnterpriseSOCDashboard";

const findings = [
    { id: "f-1", source: "live", title: "Canonical one", vendorSeverity: "Critical", asset: "a-1" },
    { id: "f-2", source: "live", title: "Canonical two", vendorSeverity: "High", asset: "a-2" },
] as const;

describe("EnterpriseSOCDashboard", () => {
    afterEach(cleanup);
    it("renders the five plus five reference regions and lower split", () => {
        render(<EnterpriseSOCDashboard findings={findings} findingsState="ready" onOpenFindings={vi.fn()} />);
        expect(within(screen.getByRole("region", { name: "Primary dashboard metrics" })).getAllByRole("article")).toHaveLength(5);
        expect(within(screen.getByRole("region", { name: "Secondary dashboard panels" })).getAllByRole("article")).toHaveLength(5);
        expect(screen.getByRole("region", { name: "AI agents workspace" })).toBeInTheDocument();
    });
    it("projects only canonical count and severities while unsupported values stay unavailable", () => {
        render(<EnterpriseSOCDashboard findings={findings} findingsState="ready" onOpenFindings={vi.fn()} />);
        expect(screen.getByText("2")).toBeInTheDocument();
        expect(screen.getByText("Critical")).toBeInTheDocument();
        expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(4);
        expect(screen.getByText("AI agents are not configured")).toBeInTheDocument();
        expect(screen.queryByText(/Max Mustermann|Vulnerability Analyst|92%/)).not.toBeInTheDocument();
    });
    it("keeps the real Findings action operational", () => {
        const onOpenFindings = vi.fn();
        render(<EnterpriseSOCDashboard findings={findings} findingsState="ready" onOpenFindings={onOpenFindings} />);
        fireEvent.click(screen.getByRole("button", { name: "View All Findings" }));
        expect(onOpenFindings).toHaveBeenCalledOnce();
    });
});
