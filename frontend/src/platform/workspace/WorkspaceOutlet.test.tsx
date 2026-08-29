import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";
import Sidebar from "@/platform/navigation/Sidebar";
import Topbar from "@/platform/navigation/Topbar";

import WorkspaceOutlet from "./WorkspaceOutlet";

vi.mock("@/workspaces/soc/findings/FindingsApiClient", async (importOriginal) => ({
    ...await importOriginal<typeof import("@/workspaces/soc/findings/FindingsApiClient")>(),
    getFindings: vi.fn().mockResolvedValue([]),
}));
vi.mock("@/workspaces/incident-response", () => ({
    IncidentResponseWorkspace: () => <div>Incident Response workspace</div>,
}));
vi.mock("@/workspaces/threat-hunter", () => ({
    ThreatHunterWorkspace: () => <div>Threat Hunter workspace</div>,
}));
vi.mock("@/workspaces/threat-intelligence", () => ({
    ThreatIntelligenceWorkspace: () => <div>Threat Intelligence workspace</div>,
}));
vi.mock("@/workspaces/risk-manager", () => ({
    RiskManagerWorkspace: () => <div>Risk Manager workspace</div>,
}));
vi.mock("@/workspaces/administrator", () => ({
    AdministratorWorkspace: () => <div>Administrator workspace</div>,
}));

function BackButton() {
    const navigate = useNavigate();
    return <button onClick={() => navigate(-1)}>Back</button>;
}

function LocationProbe() {
    const { pathname } = useLocation();
    return <output aria-label="Current route">{pathname}</output>;
}

describe("WorkspaceOutlet route synchronization", () => {
    afterEach(cleanup);

    it("switches from SOC to CISO / ISO and back through the visible workspace control", async () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter initialEntries={["/"]}>
                    <Topbar />
                    <Sidebar />
                    <WorkspaceOutlet />
                    <LocationProbe />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(await screen.findByRole("main", { name: "Enterprise SOC dashboard" })).toBeInTheDocument();
        expect(screen.getByText("Total Findings")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: /Change workspace, current workspace SOC Analyst/ }));
        fireEvent.click(screen.getByRole("menuitem", { name: "CISO / ISO" }));

        expect(await screen.findByText("Executive Mission Console")).toBeInTheDocument();
        expect(screen.getByLabelText("Current route")).toHaveTextContent("/executive");
        expect(screen.getByRole("button", { name: "Executive Overview" })).toBeInTheDocument();
        expect(screen.getByLabelText("Current workspace: CISO / ISO")).toBeInTheDocument();

        expect(screen.getByRole("button", { name: /Change workspace, current workspace CISO \/ ISO/ })).toHaveTextContent("CISO / ISO");
        fireEvent.click(screen.getByRole("button", { name: /Change workspace, current workspace CISO \/ ISO/ }));
        fireEvent.click(screen.getByRole("menuitem", { name: "SOC Analyst" }));

        expect(await screen.findByRole("main", { name: "Enterprise SOC dashboard" })).toBeInTheDocument();
        expect(screen.getByText("Total Findings")).toBeInTheDocument();
        expect(screen.getByLabelText("Current route")).toHaveTextContent("/");
        expect(screen.getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
        expect(screen.getByLabelText("Current workspace: SOC Analyst")).toBeInTheDocument();
    }, 15_000);

    it("restores the SOC workspace when browser history returns from Incident Response", async () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter
                    initialEntries={["/findings", "/incident-response"]}
                    initialIndex={1}
                >
                    <BackButton />
                    <WorkspaceOutlet />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(screen.getByText("Incident Response workspace")).toBeInTheDocument();

        screen.getByRole("button", { name: "Back" }).click();

        expect(await screen.findByRole("heading", { name: "Findings" })).toBeInTheDocument();
        expect(screen.queryByText("Incident Response workspace")).not.toBeInTheDocument();
    });

    it("derives the Threat Hunter workspace from its route", () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter initialEntries={["/threat-hunting"]}>
                    <WorkspaceOutlet />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(screen.getByText("Threat Hunter workspace")).toBeInTheDocument();
    });
});
