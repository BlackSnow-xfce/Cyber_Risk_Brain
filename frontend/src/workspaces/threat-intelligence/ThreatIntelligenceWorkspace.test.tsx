import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceContext } from "@/context/WorkspaceContext";
import { WorkspaceId } from "@/types/workspace";
import { workspaceRegistry } from "@/workspaces";
import { getWorkspaceNavigation } from "@/workspaces/registry/WorkspaceNavigation";

import ThreatIntelligenceWorkspace from "./ThreatIntelligenceWorkspace";
import ThreatIntelligenceEnvironmentPage from "./pages/ThreatIntelligenceEnvironmentPage";
import ThreatIntelligenceExplorerPage from "./pages/ThreatIntelligenceExplorerPage";
import ThreatIntelligenceOverviewPage from "./pages/ThreatIntelligenceOverviewPage";

afterEach(cleanup);

describe("Threat Intelligence workspace", () => {
    it("is registered with the existing workspace and navigation architecture", () => {
        expect(
            workspaceRegistry.find(
                (workspace) => workspace.id === WorkspaceId.THREAT_INTELLIGENCE,
            ),
        ).toMatchObject({ name: "Threat Intelligence", enabled: true });
        expect(
            getWorkspaceNavigation(WorkspaceId.THREAT_INTELLIGENCE).map(
                (item) => item.label,
            ),
        ).toEqual(["Overview", "Explorer", "Our Environment"]);
    });

    it("routes overview and explorer through the isolated workspace", () => {
        const { rerender } = renderWorkspace(null);
        expect(screen.getByText("Threat Intelligence Overview")).toBeInTheDocument();

        rerender(workspace("explorer"));
        expect(screen.getByText("Threat Intelligence Explorer")).toBeInTheDocument();
    });

    it("renders every overview category without fabricated intelligence", () => {
        render(<ThreatIntelligenceOverviewPage />);

        for (const category of [
            "Active Threats",
            "Known Exploited Vulnerabilities",
            "High EPSS Vulnerabilities",
            "Emerging Threats",
            "Threat Intelligence Sources",
            "Environment Relevance",
        ]) {
            expect(screen.getByText(category)).toBeInTheDocument();
        }
        expect(screen.getAllByText("Unavailable")).toHaveLength(3);
        expect(screen.getAllByText("No data")).toHaveLength(2);
        expect(screen.getByText("Not evaluated")).toBeInTheDocument();
    });

    it("marks unsupported explorer object types as unavailable", () => {
        render(<ThreatIntelligenceExplorerPage />);

        for (const type of [
            "IOC",
            "IP",
            "Domain",
            "Hash",
            "Threat Actor",
            "Malware",
            "Campaign",
        ]) {
            expect(screen.getByText(type)).toBeInTheDocument();
        }
        expect(screen.getAllByText("Capability unavailable")).toHaveLength(7);
        expect(screen.getByText("CVE lookup")).toBeInTheDocument();
    });

    it("shows existing live-finding fields without deriving TI relevance", async () => {
        const loadFindings = vi.fn().mockResolvedValue([
            {
                id: "finding-001",
                source: "greenbone",
                title: "Controlled live finding",
                vendorSeverity: "Medium",
                asset: "192.0.2.10",
            },
        ]);

        render(<ThreatIntelligenceEnvironmentPage loadFindings={loadFindings} />);

        expect(await screen.findByText("Controlled live finding")).toBeInTheDocument();
        expect(loadFindings).toHaveBeenCalledOnce();
        expect(screen.getByText("Source greenbone")).toBeInTheDocument();
        expect(screen.getByText("Asset 192.0.2.10")).toBeInTheDocument();
        expect(screen.getByText("Vendor severity Medium")).toBeInTheDocument();
        expect(screen.getByText("TI relevance: Not evaluated")).toBeInTheDocument();
        expect(screen.getByText("TI evidence: Not evaluated")).toBeInTheDocument();
        expect(screen.getByText("Completeness: Not evaluated")).toBeInTheDocument();
    });

    it("handles unavailable and empty internal finding sources", async () => {
        render(
            <ThreatIntelligenceEnvironmentPage
                loadFindings={() => Promise.reject(new Error("unavailable"))}
            />,
        );
        expect(
            await screen.findByText("Internal findings are currently unavailable."),
        ).toBeInTheDocument();

        cleanup();
        render(
            <ThreatIntelligenceEnvironmentPage
                loadFindings={() => Promise.resolve([])}
            />,
        );
        expect(
            await screen.findByText("No internal findings are available."),
        ).toBeInTheDocument();
    });
});

function renderWorkspace(activeNavigationItemId: string | null) {
    return render(workspace(activeNavigationItemId));
}

function workspace(activeNavigationItemId: string | null) {
    return (
        <WorkspaceContext.Provider
            value={{
                workspace: WorkspaceId.THREAT_INTELLIGENCE,
                setWorkspace: vi.fn(),
                activeNavigationItemId,
                setActiveNavigationItemId: vi.fn(),
            }}
        >
            <ThreatIntelligenceWorkspace />
        </WorkspaceContext.Provider>
    );
}
