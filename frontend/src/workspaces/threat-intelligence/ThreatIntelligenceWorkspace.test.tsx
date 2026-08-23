import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
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
        renderWorkspace(null, "/threat-intelligence");
        expect(screen.getByText("Threat Intelligence Overview")).toBeInTheDocument();

        cleanup();
        render(<MemoryRouter initialEntries={["/threat-intelligence/explorer"]}>{workspace("explorer")}</MemoryRouter>);
        expect(screen.getByText("Threat Intelligence Explorer")).toBeInTheDocument();
    });

    it("treats the workspace root as the authoritative overview after history navigation", () => {
        renderWorkspace("explorer", "/threat-intelligence");
        expect(screen.getByText("Threat Intelligence Overview")).toBeInTheDocument();
    });

    it("renders every overview category without fabricated intelligence", () => {
        render(<ThreatIntelligenceOverviewPage loadFindings={() => Promise.resolve([])} />);

        for (const category of [
            "Findings in environment",
            "CVE / vulnerability intelligence",
            "NVD / CVSS / EPSS / CISA KEV",
            "Provenance and completeness",
            "Environment Relevance",
        ]) {
            expect(screen.getByText(category)).toBeInTheDocument();
        }
        expect(screen.getByText("On demand")).toBeInTheDocument();
        expect(screen.getByText("Source-backed")).toBeInTheDocument();
        expect(screen.getByText("Preserved")).toBeInTheDocument();
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

        render(<MemoryRouter><ThreatIntelligenceEnvironmentPage loadFindings={loadFindings} /></MemoryRouter>);

        expect(await screen.findByText("Controlled live finding")).toBeInTheDocument();
        expect(loadFindings).toHaveBeenCalledOnce();
        expect(screen.getByText("Source greenbone")).toBeInTheDocument();
        expect(screen.getByText("Asset 192.0.2.10")).toBeInTheDocument();
        expect(screen.getByText("Vendor severity Medium")).toBeInTheDocument();
        expect(screen.getByText("TI relevance: Not evaluated")).toBeInTheDocument();
        expect(screen.getByText("TI evidence: Not evaluated")).toBeInTheDocument();
        expect(screen.getByText("Completeness: Not evaluated")).toBeInTheDocument();
    });

    it("filters findings immediately and preserves canonical TI navigation", async () => {
        const findings = [
            { id: "distcc-001", source: "greenbone", title: "DistCC vulnerability", vendorSeverity: "Critical", asset: "172.18.0.19" },
            { id: "ssh-002", source: "scanner", title: "OpenSSH finding", vendorSeverity: "Medium", asset: "10.0.0.4" },
        ];
        render(<MemoryRouter><ThreatIntelligenceEnvironmentPage loadFindings={() => Promise.resolve(findings)} /><LocationProbe /></MemoryRouter>);
        const search = await screen.findByRole("textbox", { name: "Search findings" });
        expect(screen.getByText("OpenSSH finding")).toBeInTheDocument();
        fireEvent.change(search, { target: { value: "DIST" } });
        expect(screen.getByText("DistCC vulnerability")).toBeInTheDocument();
        expect(screen.queryByText("OpenSSH finding")).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Open finding-scoped Threat Intelligence" }));
        expect(screen.getByTestId("location")).toHaveTextContent("findingId=distcc-001&focus=threat-intelligence");
        fireEvent.change(search, { target: { value: "no-match" } });
        expect(screen.getByText("No findings match the current search.")).toBeInTheDocument();
        fireEvent.change(search, { target: { value: "" } });
        await waitFor(() => expect(screen.getByText("OpenSSH finding")).toBeInTheDocument());
    });

    it("handles unavailable and empty internal finding sources", async () => {
        render(<MemoryRouter><ThreatIntelligenceEnvironmentPage
            loadFindings={() => Promise.reject(new Error("unavailable"))}
        /></MemoryRouter>);
        expect(
            await screen.findByText("Internal findings are currently unavailable."),
        ).toBeInTheDocument();

        cleanup();
        render(<MemoryRouter><ThreatIntelligenceEnvironmentPage
            loadFindings={() => Promise.resolve([])}
        /></MemoryRouter>);
        expect(
            await screen.findByText("No internal findings are available."),
        ).toBeInTheDocument();
    });
});

function renderWorkspace(activeNavigationItemId: string | null, initialEntry: string) {
    return render(<MemoryRouter initialEntries={[initialEntry]}>{workspace(activeNavigationItemId)}</MemoryRouter>);
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

function LocationProbe() {
    const location = useLocation();
    return <output data-testid="location">{location.pathname}{location.search}</output>;
}
