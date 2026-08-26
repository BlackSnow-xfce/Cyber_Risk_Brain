import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceContext } from "@/context/WorkspaceContext";
import Sidebar from "@/platform/navigation/Sidebar";
import { WorkspaceId } from "@/types/workspace";

import SOCWorkspace from "./SOCWorkspace";

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
});
