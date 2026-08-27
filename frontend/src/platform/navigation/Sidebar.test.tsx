import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import Sidebar from "./Sidebar";

function LocationProbe() {
    const { pathname, search } = useLocation();
    return <output data-testid="location">{pathname}{search}</output>;
}

function BackProbe() {
    const navigate = useNavigate();
    return (
        <button onClick={() => navigate(-1)}>
            Back
        </button>
    );
}

function renderSidebar(initialEntries: string[]) {
    return render(
        <WorkspaceProvider>
            <MemoryRouter initialEntries={initialEntries}>
                <Sidebar />
                <LocationProbe />
            </MemoryRouter>
        </WorkspaceProvider>,
    );
}

function renderSidebarWithBack(initialEntries: string[], initialIndex: number) {
    return render(
        <WorkspaceProvider>
            <MemoryRouter
                initialEntries={initialEntries}
                initialIndex={initialIndex}
            >
                <Sidebar />
                <LocationProbe />
                <BackProbe />
            </MemoryRouter>
        </WorkspaceProvider>,
    );
}

describe("Sidebar routing", () => {
    afterEach(() => {
        cleanup();
    });

    it("navigates from the command center to Dashboard", () => {
        renderSidebar([
            "/incident-response/incidents/incident-real-001/command-center",
        ]);

        fireEvent.click(screen.getByRole("button", { name: "Dashboard" }));

        expect(screen.getByTestId("location")).toHaveTextContent("/");
        expect(screen.getByRole("button", { name: "Dashboard" })).toHaveClass(
            "sidebar-item-active",
        );
    });

    it("preserves the validated Finding context when navigating to Dashboard", () => {
        renderSidebar(["/findings?findingId=finding-real-001"]);

        fireEvent.click(screen.getByRole("button", { name: "Dashboard" }));

        expect(screen.getByTestId("location")).toHaveTextContent(
            "/?findingId=finding-real-001",
        );
    });

    it.each([
        ["Findings", "/findings"],
        ["Investigations", "/investigations"],
    ])("navigates to %s", (label, route) => {
        renderSidebar([
            "/incident-response/incidents/incident-real-001/command-center",
        ]);

        fireEvent.click(screen.getByRole("button", { name: label }));

        expect(screen.getByTestId("location")).toHaveTextContent(route);
        expect(screen.getByRole("button", { name: label })).toHaveClass(
            "sidebar-item-active",
        );
    });

    it("does not mark Dashboard active on the command center path", () => {
        renderSidebar([
            "/incident-response/incidents/incident-real-001/command-center",
        ]);

        expect(screen.getByRole("button", { name: "Dashboard" })).not.toHaveClass(
            "sidebar-item-active",
        );
    });

    it("restores the command center path with browser back", () => {
        renderSidebarWithBack(
            [
                "/incident-response/incidents/incident-real-001/command-center",
                "/findings",
            ],
            1,
        );

        fireEvent.click(screen.getByRole("button", { name: "Back" }));

        expect(screen.getByTestId("location")).toHaveTextContent(
            "/incident-response/incidents/incident-real-001/command-center",
        );
        expect(screen.getByRole("button", { name: "Dashboard" })).not.toHaveClass(
            "sidebar-item-active",
        );
    });
});
