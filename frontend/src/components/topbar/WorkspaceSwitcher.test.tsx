import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import WorkspaceSwitcher from "./WorkspaceSwitcher";

function LocationProbe() {
    const location = useLocation();
    return <output aria-label="Current route">{location.pathname}</output>;
}

describe("WorkspaceSwitcher", () => {
    afterEach(() => {
        cleanup();
        vi.restoreAllMocks();
    });

    it("opens and closes when the trigger is clicked repeatedly", () => {
        render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /></MemoryRouter></WorkspaceProvider>);
        const trigger = screen.getByRole("button", { name: /Change workspace/ });

        fireEvent.click(trigger);
        expect(trigger).toHaveAttribute("aria-expanded", "true");
        expect(screen.getByRole("menu")).toBeInTheDocument();

        fireEvent.click(trigger);
        expect(trigger).toHaveAttribute("aria-expanded", "false");
        expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    });

    it("dismisses on an outside pointer interaction without consuming the outside action", () => {
        const outsideAction = vi.fn();
        render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /><button type="button" onClick={outsideAction}>Outside action</button></MemoryRouter></WorkspaceProvider>);
        fireEvent.click(screen.getByRole("button", { name: /Change workspace/ }));

        const outsideButton = screen.getByRole("button", { name: "Outside action" });
        fireEvent.pointerDown(outsideButton);
        fireEvent.click(outsideButton);

        expect(screen.queryByRole("menu")).not.toBeInTheDocument();
        expect(outsideAction).toHaveBeenCalledOnce();
    });

    it("keeps the menu open for pointer interactions inside its boundary", () => {
        render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /></MemoryRouter></WorkspaceProvider>);
        fireEvent.click(screen.getByRole("button", { name: /Change workspace/ }));

        fireEvent.pointerDown(screen.getByRole("menu"));

        expect(screen.getByRole("menu")).toBeInTheDocument();
    });

    it("dismisses on Escape without changing workspace or route", () => {
        render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /><LocationProbe /></MemoryRouter></WorkspaceProvider>);
        fireEvent.click(screen.getByRole("button", { name: /Change workspace/ }));

        fireEvent.keyDown(document, { key: "Escape" });

        expect(screen.queryByRole("menu")).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: /current workspace SOC Analyst/ })).toBeInTheDocument();
        expect(screen.getByLabelText("Current route")).toHaveTextContent("/");
    });

    it("registers listeners only while open and cleans them up across cycles and unmount", () => {
        const addEventListener = vi.spyOn(document, "addEventListener");
        const removeEventListener = vi.spyOn(document, "removeEventListener");
        const { unmount } = render(<WorkspaceProvider><MemoryRouter><WorkspaceSwitcher /></MemoryRouter></WorkspaceProvider>);
        const trigger = screen.getByRole("button", { name: /Change workspace/ });

        expect(addEventListener).not.toHaveBeenCalledWith("pointerdown", expect.any(Function));
        expect(addEventListener).not.toHaveBeenCalledWith("keydown", expect.any(Function));

        fireEvent.click(trigger);
        const firstPointerListener = addEventListener.mock.calls.find(([type]) => type === "pointerdown")?.[1];
        const firstKeyListener = addEventListener.mock.calls.find(([type]) => type === "keydown")?.[1];
        expect(firstPointerListener).toBeDefined();
        expect(firstKeyListener).toBeDefined();

        fireEvent.click(trigger);
        expect(removeEventListener).toHaveBeenCalledWith("pointerdown", firstPointerListener);
        expect(removeEventListener).toHaveBeenCalledWith("keydown", firstKeyListener);

        fireEvent.click(trigger);
        const pointerListeners = addEventListener.mock.calls.filter(([type]) => type === "pointerdown");
        const keyListeners = addEventListener.mock.calls.filter(([type]) => type === "keydown");
        expect(pointerListeners).toHaveLength(2);
        expect(keyListeners).toHaveLength(2);

        const secondPointerListener = pointerListeners[1][1];
        const secondKeyListener = keyListeners[1][1];
        unmount();
        expect(removeEventListener).toHaveBeenCalledWith("pointerdown", secondPointerListener);
        expect(removeEventListener).toHaveBeenCalledWith("keydown", secondKeyListener);
    });

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

        const executiveItem = screen.getByRole("menuitem", { name: "CISO / ISO" });
        fireEvent.pointerDown(executiveItem);
        fireEvent.click(executiveItem);
        expect(screen.getByLabelText("Current route")).toHaveTextContent("/executive");
        expect(screen.getByRole("button", { name: /current workspace CISO \/ ISO/ })).toHaveTextContent("CISO / ISO");
        expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    });
});
