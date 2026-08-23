import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { Link, MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import IncidentResponseWorkspace from "./IncidentResponseWorkspace";

vi.mock("./IncidentResponseLayout", () => ({
    default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));
vi.mock("./pages/IncidentQueuePage", () => ({
    default: () => <div>Incident Queue Mock</div>,
}));
vi.mock("./pages/IncidentCommandCenterPage", () => ({
    default: () => <CommandCenterMock />,
}));

function CommandCenterMock() {
    const { pathname } = useLocation();
    return (
        <div>
            <span>Command Center for {pathname.split("/")[3]}</span>
            <Link to="/incident-response/queue">Back to Queue</Link>
        </div>
    );
}

describe("IncidentResponseWorkspace URL authority", () => {
    afterEach(() => cleanup());

    it("renders the queue from a direct queue deep link", () => {
        render(
            <MemoryRouter initialEntries={["/incident-response/queue"]}>
                <IncidentResponseWorkspace />
            </MemoryRouter>,
        );

        expect(screen.getByText("Incident Queue Mock")).toBeInTheDocument();
    });

    it("renders the command center from a direct deep-link URL", () => {
        render(
            <MemoryRouter initialEntries={["/incident-response/incidents/incident-real-001/command-center"]}>
                <IncidentResponseWorkspace />
            </MemoryRouter>,
        );

        expect(screen.getByText("Command Center for incident-real-001")).toBeInTheDocument();
    });

    it("keeps command-center identity through queue, back and forward", () => {
        render(
            <MemoryRouter initialEntries={["/incident-response/queue"]}>
                <NavigationHarness />
            </MemoryRouter>,
        );

        fireEvent.click(screen.getByRole("link", { name: "Open Command Center" }));
        expect(screen.getByText("Command Center for incident-real-001")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Browser Back" }));
        expect(screen.getByText("Incident Queue Mock")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Browser Forward" }));
        expect(screen.getByText("Command Center for incident-real-001")).toBeInTheDocument();
    });
});

function NavigationHarness() {
    const { pathname } = useLocation();
    const navigate = useNavigate();
    return (
        <>
            <IncidentResponseWorkspace />
            <button type="button" onClick={() => navigate(-1)}>Browser Back</button>
            <button type="button" onClick={() => navigate(1)}>Browser Forward</button>
            {pathname === "/incident-response/queue" && (
                <Link to="/incident-response/incidents/incident-real-001/command-center">
                    Open Command Center
                </Link>
            )}
        </>
    );
}
