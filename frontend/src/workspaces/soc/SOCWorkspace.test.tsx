import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter, MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceContext } from "@/context/WorkspaceContext";
import Sidebar from "@/platform/navigation/Sidebar";
import { WorkspaceId } from "@/types/workspace";

import SOCWorkspace from "./SOCWorkspace";
import FindingsWorkspace from "./findings/FindingsWorkspace";
import type { FindingSummary } from "./findings/FindingSummary";

vi.mock("./pages/DashboardPage", () => ({
    default: () => <div>Dashboard route content</div>,
}));
vi.mock("./pages/ExplainabilityPage", () => ({
    default: () => <div>Explainability route content</div>,
}));
vi.mock("./pages/AssetsPage", () => ({ default: () => <div>Assets</div> }));
vi.mock("./pages/ExposurePage", () => ({ default: () => <div>Exposure</div> }));
vi.mock("./pages/FindingsPage", () => ({ default: () => <div>Findings</div> }));
vi.mock("./pages/InvestigationsPage", () => ({ default: () => <div>Investigations</div> }));
vi.mock("./pages/ThreatIntelligencePage", () => ({
    default: () => <div>Threat intelligence</div>,
}));

const { default: RoutedDashboardPage } = await vi.importActual<
    typeof import("./pages/DashboardPage")
>("./pages/DashboardPage");

function HistoryControls() {
    const navigate = useNavigate();
    return (
        <>
            <button onClick={() => navigate(-1)}>Back</button>
            <button onClick={() => navigate(1)}>Forward</button>
        </>
    );
}

function renderSOC(initialEntries: string[], initialIndex = 0, stalePage = "dashboard") {
    return render(
        <WorkspaceContext.Provider
            value={{
                workspace: WorkspaceId.DECISION_CENTER,
                setWorkspace: vi.fn(),
                activeNavigationItemId: stalePage,
                setActiveNavigationItemId: vi.fn(),
            }}
        >
            <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
                <Sidebar />
                <HistoryControls />
                <SOCWorkspace />
            </MemoryRouter>
        </WorkspaceContext.Provider>,
    );
}

describe("SOCWorkspace URL-authoritative routing", () => {
    afterEach(() => {
        cleanup();
        window.history.replaceState({}, "", "/");
    });

    it("renders a direct Explainability deep link despite stale local navigation state", () => {
        renderSOC(["/explainability"], 0, "dashboard");

        expect(screen.getByText("Explainability route content")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Explainability" })).toHaveClass(
            "sidebar-item-active",
        );
    });

    it("keeps Dashboard, Explainability, Back, and Forward content synchronized", () => {
        renderSOC(["/", "/explainability"], 1, "explainability");

        expect(screen.getByText("Explainability route content")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Back" }));
        expect(screen.getByText("Dashboard route content")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Dashboard" })).toHaveClass(
            "sidebar-item-active",
        );

        fireEvent.click(screen.getByRole("button", { name: "Forward" }));
        expect(screen.getByText("Explainability route content")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Explainability" })).toHaveClass(
            "sidebar-item-active",
        );
    });

    it("navigates visibly from Dashboard to Explainability", () => {
        renderSOC(["/"], 0, "dashboard");

        fireEvent.click(screen.getByRole("button", { name: "Explainability" }));

        expect(screen.getByText("Explainability route content")).toBeInTheDocument();
        expect(screen.queryByText("Dashboard route content")).not.toBeInTheDocument();
    });

    it("keeps the exact canonical Finding through Sidebar Dashboard navigation and history", async () => {
        const selectedFinding: FindingSummary = {
            id: "finding-selected",
            source: "greenbone",
            title: "Selected routed finding",
            vendorSeverity: "Medium",
            asset: "192.0.2.20",
        };
        const otherFinding: FindingSummary = {
            id: "finding-other",
            source: "greenbone",
            title: "Other routed finding",
            vendorSeverity: "Low",
            asset: "192.0.2.21",
        };
        const loadFindingIncidents = vi.fn().mockResolvedValue([]);
        window.history.replaceState({}, "", "/findings");

        render(
            <WorkspaceContext.Provider
                value={{
                    workspace: WorkspaceId.DECISION_CENTER,
                    setWorkspace: vi.fn(),
                    activeNavigationItemId: "findings",
                    setActiveNavigationItemId: vi.fn(),
                }}
            >
                <BrowserRouter>
                    <Sidebar />
                    <HistoryControls />
                    <Routes>
                        <Route
                            path="/findings"
                            element={
                                <FindingsWorkspace
                                    loadFindings={() => Promise.resolve([selectedFinding, otherFinding])}
                                />
                            }
                        />
                        <Route
                            path="/"
                            element={
                                <RoutedDashboardPage
                                    loadFindings={() => Promise.resolve([selectedFinding, otherFinding])}
                                    loadFindingIncidents={loadFindingIncidents}
                                />
                            }
                        />
                    </Routes>
                </BrowserRouter>
            </WorkspaceContext.Provider>,
        );

        const findingButton = (await screen.findByText("Selected routed finding")).closest("button");
        if (!findingButton) {
            throw new Error("Selected Finding button was not rendered.");
        }
        fireEvent.click(findingButton);
        await waitFor(() => expect(window.location.search).toBe("?findingId=finding-selected"));
        fireEvent.click(screen.getByRole("button", { name: "Dashboard" }));
        await waitFor(() => expect(loadFindingIncidents).toHaveBeenCalledWith("finding-selected"));
        expect(window.location.pathname).toBe("/");
        expect(screen.getAllByText("Selected routed finding").length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole("button", { name: "Back" }));
        await waitFor(() => expect(window.location.pathname).toBe("/findings"));
        await waitFor(() => {
            expect(document.querySelector('button[aria-pressed="true"]'))
                .toHaveTextContent("Selected routed finding");
        });

        fireEvent.click(screen.getByRole("button", { name: "Forward" }));
        await waitFor(() => expect(loadFindingIncidents).toHaveBeenCalledTimes(2));
        expect(window.location.pathname).toBe("/");
        expect(screen.getAllByText("Selected routed finding").length).toBeGreaterThan(0);
        expect(screen.queryByText("Other routed finding")).not.toBeInTheDocument();
    }, 10_000);
});
