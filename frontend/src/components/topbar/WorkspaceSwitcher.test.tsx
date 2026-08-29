import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import WorkspaceSwitcher from "./WorkspaceSwitcher";

function LocationProbe() {
    const location = useLocation();
    return <output aria-label="Current route">{location.pathname}</output>;
}

describe("WorkspaceSwitcher", () => {
    afterEach(cleanup);

    it("groups every enabled workspace under its explicit semantic heading", () => {
        render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /></MemoryRouter></WorkspaceProvider>);
        fireEvent.click(screen.getByRole("button", { name: /Change workspace/ }));

        const groups = screen.getAllByRole("group");
        expect(groups.map((group) => group.getAttribute("aria-labelledby"))).toEqual([
            "workspace-group-0",
            "workspace-group-1",
            "workspace-group-2",
        ]);
        expect(screen.getAllByText(/^(SOC WORKSPACES|MANAGEMENT WORKSPACES|SYSTEM \/ ADMINISTRATION)$/).map(({ textContent }) => textContent)).toEqual([
            "SOC WORKSPACES",
            "MANAGEMENT WORKSPACES",
            "SYSTEM / ADMINISTRATION",
        ]);
        expect(within(groups[0]).getAllByRole("menuitem").map(({ textContent }) => textContent?.replace("Selected", ""))).toEqual([
            "SOC Analyst",
            "Threat Hunter",
            "Threat Intelligence",
            "Incident Response",
        ]);
        expect(within(groups[1]).getAllByRole("menuitem").map(({ textContent }) => textContent)).toEqual(["CISO / ISO", "Risk Manager"]);
        expect(within(groups[2]).getAllByRole("menuitem").map(({ textContent }) => textContent)).toEqual(["Administrator"]);
    });

    it("marks the current workspace and preserves the canonical Executive route", () => {
        render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /><LocationProbe /></MemoryRouter></WorkspaceProvider>);
        fireEvent.click(screen.getByRole("button", { name: /Change workspace/ }));

        const selectedItem = screen.getByRole("menuitem", { name: /SOC Analyst/ });
        expect(selectedItem).toHaveAttribute("aria-current", "true");
        expect(within(selectedItem).getByLabelText("Selected")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("menuitem", { name: "CISO / ISO" }));
        expect(screen.getByLabelText("Current route")).toHaveTextContent("/executive");
        expect(screen.getByRole("button", { name: /current workspace CISO \/ ISO/ })).toHaveTextContent("CISO / ISO");
        expect(screen.queryByRole("menuitem", { name: "Executive" })).not.toBeInTheDocument();
    });
});
