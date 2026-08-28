import { readFileSync } from "node:fs";

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import PlatformLayout from "./PlatformLayout";

vi.mock("../navigation/Sidebar", () => ({ default: () => <aside>Sidebar</aside> }));
vi.mock("../navigation/Topbar", () => ({ default: () => <header>Topbar</header> }));

describe("PlatformLayout", () => {
    it("binds the shell to the viewport and makes Main the scroll owner", () => {
        const source = readFileSync("src/platform/layout/PlatformLayout.tsx", "utf8");
        render(
            <WorkspaceProvider>
                <MemoryRouter>
                    <PlatformLayout><div>Workspace content</div></PlatformLayout>
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        const main = screen.getByRole("main");
        const rightColumn = main.parentElement;
        const root = rightColumn?.parentElement;

        expect(root).toHaveStyle({ overflow: "hidden" });
        expect(rightColumn).toHaveStyle({ minWidth: 0, minHeight: 0 });
        expect(main).toHaveStyle({
            minWidth: 0,
            minHeight: 0,
            overflowX: "auto",
            overflowY: "auto",
        });
        expect(source).toContain('gridTemplateColumns: "164px minmax(0, 1fr)"');
        expect(source).toContain('width: "100vw"');
        expect(source).toContain('height: "100vh"');
    });
});
