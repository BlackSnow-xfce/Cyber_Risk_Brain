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
});
