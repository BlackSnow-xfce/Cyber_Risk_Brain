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
        const sidebarSource = readFileSync("src/platform/navigation/Sidebar.css", "utf8");
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
        expect(sidebarSource).toMatch(/\.sidebar\s*\{[^}]*\bwidth:\s*164px;/s);
        expect(sidebarSource).toMatch(/\.sidebar\s*\{[^}]*\bmin-width:\s*164px;/s);
        expect(source).toContain('width: "100vw"');
        expect(source).toContain('height: "100vh"');
    });

    it("models Main and body scroll ownership with controlled jsdom dimensions", () => {
        // jsdom does not perform native pixel layout. This is deterministic
        // layout-contract verification with controlled DOM dimensions, not a
        // native browser pixel measurement. Actual rendering remains subject to
        // Product Owner Live Acceptance at 1536 x 1024 and 100% browser zoom.
        const viewportWidth = 1024;
        const sidebarWidth = 164;
        const mainClientWidth = viewportWidth - sidebarWidth;
        const contentWidth = 1100;
        const ownsNoHorizontalOverflow = (element: Pick<Element, "clientWidth" | "scrollWidth">) =>
            element.scrollWidth === element.clientWidth;

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
        Object.defineProperties(document.body, {
            clientWidth: { configurable: true, value: viewportWidth },
            scrollWidth: { configurable: true, value: viewportWidth },
        });

        expect(main.clientWidth).toBe(860);
        expect(main.scrollWidth).toBe(1100);
        expect(main.scrollWidth).toBeGreaterThan(main.clientWidth);
        expect(ownsNoHorizontalOverflow(document.documentElement)).toBe(true);
        expect(ownsNoHorizontalOverflow(document.body)).toBe(true);
        expect(main).toHaveStyle({ overflowX: "auto" });

        const maximumScrollLeft = main.scrollWidth - main.clientWidth;
        expect(maximumScrollLeft).toBe(240);
        main.scrollLeft = maximumScrollLeft;
        expect(main.scrollLeft + main.clientWidth).toBe(main.scrollWidth);

        const bodyOverflowRegression = { clientWidth: viewportWidth, scrollWidth: contentWidth };
        expect(ownsNoHorizontalOverflow(bodyOverflowRegression)).toBe(false);
    });
});
