import { render, screen } from "@testing-library/react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import WorkspaceOutlet from "./WorkspaceOutlet";

vi.mock("@/workspaces/soc", () => ({
    SOCWorkspace: () => <div>SOC workspace</div>,
}));
vi.mock("@/workspaces/incident-response", () => ({
    IncidentResponseWorkspace: () => <div>Incident Response workspace</div>,
}));
vi.mock("@/workspaces/executive", () => ({
    ExecutiveWorkspace: () => <div>Executive workspace</div>,
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

describe("WorkspaceOutlet route synchronization", () => {
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

        expect(await screen.findByText("SOC workspace")).toBeInTheDocument();
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
