import { readFileSync } from "node:fs";

import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import PlatformLayout from "./PlatformLayout";

vi.mock("../navigation/Sidebar", () => ({ default: () => <aside>Sidebar</aside> }));
vi.mock("../navigation/Topbar", () => ({ default: () => <header>Topbar</header> }));

describe("PlatformLayout", () => {
    afterEach(cleanup);

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

    it("keeps deliberately wide content reachable through Main at a smaller viewport", () => {
        const viewportWidth = 1024;
        const sidebarWidth = 164;
        const mainClientWidth = viewportWidth - sidebarWidth;
        const contentWidth = 1100;

        render(
            <WorkspaceProvider>
                <MemoryRouter>
                    <PlatformLayout><div style={{ minWidth: contentWidth }}>Wide workspace content</div></PlatformLayout>
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        const main = screen.getByRole("main");
        Object.defineProperties(main, {
            clientWidth: { configurable: true, value: mainClientWidth },
            scrollWidth: { configurable: true, value: contentWidth },
            scrollLeft: { configurable: true, writable: true, value: 0 },
        });
        Object.defineProperties(document.documentElement, {
            clientWidth: { configurable: true, value: viewportWidth },
            scrollWidth: { configurable: true, value: viewportWidth },
        });

        expect(main.scrollWidth).toBeGreaterThan(main.clientWidth);
        expect(document.documentElement.scrollWidth).toBe(document.documentElement.clientWidth);
        expect(main).toHaveStyle({ overflowX: "auto" });

        const maximumScrollLeft = main.scrollWidth - main.clientWidth;
        main.scrollLeft = maximumScrollLeft;
        expect(main.scrollLeft + main.clientWidth).toBe(main.scrollWidth);
    });
});
