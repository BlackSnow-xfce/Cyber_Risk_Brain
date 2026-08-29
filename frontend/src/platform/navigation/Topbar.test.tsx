import { readFileSync } from "node:fs";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";
import Topbar from "./Topbar";

function Probe() { const location = useLocation(); return <output>{location.pathname}</output>; }
describe("Topbar", () => {
    afterEach(cleanup);
    it("uses neutral identity and routes Explainability", () => {
        render(<WorkspaceProvider><MemoryRouter><Topbar /><Probe /></MemoryRouter></WorkspaceProvider>);
        expect(screen.getByLabelText("Operator unavailable")).toBeInTheDocument();
        expect(screen.queryByText("Max Mustermann")).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Explain This Dashboard" }));
        expect(screen.getByRole("status")).toHaveTextContent("/explainability");
    });
    it("opens and closes the theme popover explicitly", () => {
        render(<WorkspaceProvider><MemoryRouter><Topbar /></MemoryRouter></WorkspaceProvider>);
        expect(screen.queryByRole("region", { name: "Theme options" })).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Theme" }));
        expect(screen.getByRole("region", { name: "Theme options" })).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Theme" }));
        expect(screen.queryByRole("region", { name: "Theme options" })).not.toBeInTheDocument();
    });
    it("presents the current workspace as a bounded interactive control", () => {
        render(<WorkspaceProvider><MemoryRouter><Topbar /></MemoryRouter></WorkspaceProvider>);

        const switcher = screen.getByRole("button", { name: /Change workspace, current workspace SOC Analyst/ });
        const stylesheet = readFileSync("src/platform/navigation/Topbar.css", "utf8");

        expect(switcher).toHaveTextContent("SOC Analyst");
        expect(stylesheet).toMatch(/\.workspace-switcher>button \{[^}]*min-height:28px/);
        expect(stylesheet).toMatch(/\.workspace-switcher>button \{[^}]*padding:0 9px/);
        expect(stylesheet).toMatch(/\.workspace-switcher>button \{[^}]*background:#0c1423/);
        expect(stylesheet).toMatch(/\.workspace-switcher>button \{[^}]*border:1px solid #334155/);
        expect(stylesheet).toMatch(/\.workspace-switcher>button \{[^}]*font-size:14px/);
        expect(stylesheet).toMatch(/\.workspace-switcher>button \{[^}]*font-weight:600/);
        expect(stylesheet).toContain(".workspace-switcher>button:focus-visible");
    });
    it("exposes semantic workspace group presentation hooks", () => {
        render(<WorkspaceProvider><MemoryRouter><Topbar /></MemoryRouter></WorkspaceProvider>);
        fireEvent.click(screen.getByRole("button", { name: /Change workspace/ }));

        expect(screen.getAllByRole("group")).toHaveLength(3);
        expect(screen.getAllByRole("separator")).toHaveLength(2);

        const stylesheet = readFileSync("src/platform/navigation/Topbar.css", "utf8");
        expect(stylesheet).toContain(".workspace-menu-label");
        expect(stylesheet).toContain(".workspace-menu-divider");
        expect(stylesheet).toContain(".workspace-menu-check");
        expect(stylesheet).toMatch(/\.workspace-menu button \{[^}]*font-size:13px/);
        expect(stylesheet).toMatch(/\.workspace-menu-label \{[^}]*font-size:11px/);
        expect(stylesheet).toMatch(/\.workspace-menu-label \{[^}]*font-weight:600/);
    });
});
