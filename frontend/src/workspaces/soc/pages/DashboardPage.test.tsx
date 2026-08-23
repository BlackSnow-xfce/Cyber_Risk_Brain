import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "./DashboardPage";

const findings = [
    {
        id: "finding-1",
        source: "greenbone",
        title: "DistCC RCE Vulnerability",
        vendorSeverity: "High",
        asset: "asset-lab-metasploitable2-001",
    },
];

const noIncidentContext = () => Promise.resolve([] as const);

function LocationProbe() {
    const { pathname, search } = useLocation();
    return <output data-testid="location">{pathname}{search}</output>;
}

describe("SOC Analyst dashboard foundation", () => {
    afterEach(() => {
        cleanup();
    });

    it("renders the operational SOC structure without mock decision data", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.resolve(findings)} loadFindingIncidents={noIncidentContext} />
            </MemoryRouter>,
        );

        expect(screen.getByText("SOC Analyst")).toBeInTheDocument();
        expect(screen.getByText("SOC Analyst Dashboard")).toBeInTheDocument();
        expect(screen.getByLabelText("Operational status")).toBeInTheDocument();
        expect(screen.getByText("Situation overview")).toBeInTheDocument();
        expect(screen.getByLabelText("Analyst workspace")).toBeInTheDocument();
        expect(screen.getByText("PredatorAI Analyst Brief")).toBeInTheDocument();
        expect(screen.queryByText("Decision Workspace")).not.toBeInTheDocument();
        expect((await screen.findAllByText("DistCC RCE Vulnerability")).length).toBeGreaterThan(0);
        expect(screen.getAllByText("1", { selector: "h4" }).length).toBeGreaterThan(0);
    });

    it("keeps the real findings navigation entry point", () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.resolve(findings)} loadFindingIncidents={noIncidentContext} />
                <LocationProbe />
            </MemoryRouter>,
        );

        fireEvent.click(screen.getByRole("button", { name: "Open Findings" }));

        expect(screen.getByTestId("location")).toHaveTextContent("/findings");
    });

    it("shows a neutral empty state", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.resolve([])} loadFindingIncidents={noIncidentContext} />
            </MemoryRouter>,
        );

        expect(await screen.findByText("No live findings available.")).toBeInTheDocument();
        expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
    });

    it("shows a controlled error state", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.reject(new Error("offline"))} loadFindingIncidents={noIncidentContext} />
            </MemoryRouter>,
        );

        expect(await screen.findByText("Live findings could not be loaded.")).toBeInTheDocument();
        expect(screen.getByText("Unavailable")).toBeInTheDocument();
    });

    it("filters live dashboard findings and supports selecting one", async () => {
        const secondFinding = {
            ...findings[0],
            id: "finding-2",
            title: "Unrelated finding",
        };

        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve([findings[0], secondFinding])}
                    loadFindingIncidents={noIncidentContext}
                />
                <LocationProbe />
            </MemoryRouter>,
        );

        const search = await screen.findByLabelText("Search findings");
        fireEvent.change(search, { target: { value: "DistCC" } });

        expect(screen.getAllByText("DistCC RCE Vulnerability").length).toBeGreaterThan(0);
        expect(screen.queryByText("Unrelated finding")).toBeNull();

        fireEvent.click(screen.getAllByRole("button", { name: /DistCC RCE Vulnerability/ })[0]);
        expect(screen.getByTestId("location")).toHaveTextContent(
            "/findings?findingId=finding-1",
        );
    });

    it("reloads live findings through the refresh control", async () => {
        const loadFindings = vi
            .fn()
            .mockResolvedValueOnce(findings)
            .mockResolvedValueOnce(findings);

        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={loadFindings}
                    loadFindingIncidents={noIncidentContext}
                />
            </MemoryRouter>,
        );

        await screen.findAllByText("DistCC RCE Vulnerability");
        fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

        await screen.findByRole("button", { name: "Refreshing" }).catch(() => undefined);
        expect(loadFindings).toHaveBeenCalledTimes(2);
    });

    it("shows a persisted incident relationship and opens its command center", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve([{
                        ...findings[0],
                        title: "DistCC RCE Vulnerability (CVE-2004-2687)",
                    }])}
                    loadFindingIncidents={() =>
                        Promise.resolve([
                            {
                                incident_id: "incident-real-001",
                                relationship_id: "relationship-001",
                                relationship_role: "investigation_candidate",
                                lifecycle_status: "investigating",
                            },
                        ])
                    }
                />
                <LocationProbe />
            </MemoryRouter>,
        );

        expect((await screen.findAllByText("incident-real-001")).length).toBeGreaterThan(0);
        expect(screen.getByText(/investigation_candidate/)).toBeInTheDocument();
        fireEvent.click(screen.getAllByRole("button", { name: "Open Incident" })[0]);
        expect(screen.getByTestId("location")).toHaveTextContent("/incident-response");
        fireEvent.click(screen.getAllByRole("button", { name: "Open Command Center" })[0]);
        expect(screen.getByTestId("location")).toHaveTextContent(
            "/incident-response/incidents/incident-real-001/command-center",
        );
    });

    it("presents a grounded investigation path and explicit not-verified boundary", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve(findings)}
                    loadFindingIncidents={() => Promise.resolve([])}
                />
            </MemoryRouter>,
        );

        expect(await screen.findByLabelText("Investigation path")).toBeInTheDocument();
        expect(screen.getByText("What happened?")).toBeInTheDocument();
        expect(screen.getByText("Why this matters")).toBeInTheDocument();
        expect(screen.getByText("What we know")).toBeInTheDocument();
        expect(screen.getByText("What is not verified")).toBeInTheDocument();
        expect(screen.getByText("Investigate next")).toBeInTheDocument();
        expect(screen.getByText("No exploit, RCE or compromise conclusion")).toBeInTheDocument();
        expect(screen.queryByText(/RCE confirmed|compromised|exploited/i)).toBeNull();
    });

    it("keeps the canonical asset node static while relationship actions remain interactive", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve([{
                        ...findings[0],
                        title: "DistCC RCE Vulnerability (CVE-2004-2687)",
                    }])}
                    loadFindingIncidents={noIncidentContext}
                />
            </MemoryRouter>,
        );

        const assetLabel = await screen.findByText("CANONICAL ASSET");
        const assetNode = assetLabel.closest(".soc-cockpit__node");
        expect(assetNode).toHaveClass("soc-cockpit__node--static");
        expect(assetNode?.tagName).toBe("DIV");
        expect(assetNode).not.toHaveClass("soc-cockpit__node--interactive");
        expect(screen.getAllByRole("button", { name: /DistCC RCE Vulnerability/ }).length).toBeGreaterThan(0);
        expect(screen.getAllByRole("button", { name: /CVE|Threat intelligence/i }).length).toBeGreaterThan(0);
    });

    it("marks the selected Finding and CVE/TI relationship nodes", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve([{
                        ...findings[0],
                        title: "DistCC RCE Vulnerability (CVE-2004-2687)",
                    }])}
                    loadFindingIncidents={noIncidentContext}
                />
            </MemoryRouter>,
        );

        const findingNode = (await screen.findAllByRole("button", { name: /DistCC RCE Vulnerability/ }))[0];
        fireEvent.click(findingNode);
        expect(findingNode).toHaveAttribute("aria-pressed", "true");

        const cveNode = (await screen.findAllByRole("button", { name: /CVE-2004-2687/ }))
            .find((button) => button.textContent?.includes("Threat intelligence"));
        expect(cveNode).toBeDefined();
        fireEvent.click(cveNode!);
        expect(cveNode).toHaveAttribute("aria-pressed", "true");
        expect(findingNode).toHaveAttribute("aria-pressed", "false");
    });

    it("gives the visible recommended-investigation panel update feedback", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve([{
                        ...findings[0],
                        title: "DistCC RCE Vulnerability (CVE-2004-2687)",
                    }])}
                    loadFindingIncidents={noIncidentContext}
                />
            </MemoryRouter>,
        );

        const findingNode = (await screen.findAllByRole("button", { name: /DistCC RCE Vulnerability/ }))[0];
        fireEvent.click(findingNode);
        await waitFor(() => {
            expect(screen.getByText("Next analyst actions").closest(".soc-cockpit__panel")).toHaveClass("soc-cockpit__panel--updated");
        });
    });

    it("preserves the CVE context and focuses threat intelligence in Finding Details", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage
                    loadFindings={() => Promise.resolve([{
                        ...findings[0],
                        title: "DistCC RCE Vulnerability (CVE-2004-2687)",
                    }])}
                    loadFindingIncidents={noIncidentContext}
                />
                <LocationProbe />
            </MemoryRouter>,
        );

        const cveNode = (await screen.findAllByRole("button", { name: /CVE-2004-2687/ }))
            .find((button) => button.textContent?.includes("Threat intelligence"));
        expect(cveNode).toBeDefined();
        fireEvent.click(cveNode!);

        expect(screen.getByTestId("location")).toHaveTextContent(
            "/findings?findingId=finding-1&focus=threat-intelligence",
        );
    });
});
