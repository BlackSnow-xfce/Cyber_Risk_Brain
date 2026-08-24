import { render, screen } from "@testing-library/react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { describe, expect, it } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { useWorkspace } from "@/hooks/useWorkspace";

import ThreatHunterWorkspace from "./ThreatHunterWorkspace";

function HistoryControls() {
    const navigate = useNavigate();

    return (
        <>
            <button onClick={() => navigate(-1)}>Back</button>
            <button onClick={() => navigate(1)}>Forward</button>
        </>
    );
}

function StaleNavigationState() {
    const { setActiveNavigationItemId } = useWorkspace();

    useEffect(() => {
        setActiveNavigationItemId("hunts");
    }, [setActiveNavigationItemId]);

    return null;
}

describe("ThreatHunterWorkspace", () => {
    it("renders an explicit foundation overview without claiming connected data", () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter initialEntries={["/threat-hunting"]}>
                    <ThreatHunterWorkspace />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(screen.getByText("Threat Hunter Mission Console")).toBeInTheDocument();
        expect(screen.getAllByText("Not connected").length).toBeGreaterThan(0);
        expect(screen.getByText("No active hunts are available.")).toBeInTheDocument();
    });

    it("uses the route for a direct Hunts deep link", () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter initialEntries={["/threat-hunting/hunts"]}>
                    <ThreatHunterWorkspace />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(
            screen.getByRole("heading", { name: "No hunts are available" }),
        ).toBeInTheDocument();
        expect(
            screen.getByText(
                "Connect a hunting data source before hunts can be shown here.",
            ),
        ).toBeInTheDocument();
        expect(
            screen.queryByText("Workspace connection required"),
        ).not.toBeInTheDocument();
        expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
    });

    it("keeps Overview and Hunts synchronized across Back and Forward", async () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter
                    initialEntries={["/threat-hunting", "/threat-hunting/hunts"]}
                    initialIndex={1}
                >
                    <StaleNavigationState />
                    <HistoryControls />
                    <ThreatHunterWorkspace />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(screen.getAllByText("Hunts").length).toBeGreaterThan(0);

        screen.getByRole("button", { name: "Back" }).click();
        expect(await screen.findByText("Threat Hunter Mission Console")).toBeInTheDocument();

        screen.getByRole("button", { name: "Forward" }).click();
        expect(
            await screen.findByRole("heading", {
                name: "No hunts are available",
            }),
        ).toBeInTheDocument();
        expect(screen.getAllByText("Hunts").length).toBeGreaterThan(0);
    });
});
