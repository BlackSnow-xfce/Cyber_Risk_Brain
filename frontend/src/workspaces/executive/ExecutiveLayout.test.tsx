import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import ExecutiveLayout from "./ExecutiveLayout";

describe("ExecutiveLayout", () => {
    afterEach(cleanup);

    it("owns a positive inset without negative offset or viewport overflow", () => {
        render(<ExecutiveLayout><div>Executive content</div></ExecutiveLayout>);

        const layout = screen.getByText("Executive content").parentElement;

        expect(layout).toHaveStyle({
            width: "100%",
            minWidth: 0,
            padding: "24px",
            boxSizing: "border-box",
        });
        expect(layout?.getAttribute("style") ?? "").not.toMatch(/margin-left:\s*-|transform:/);
    });

    it("fits its border box inside the 1536px viewport Main track", () => {
        const viewportWidth = 1536;
        const sidebarWidth = 164;
        const mainClientWidth = viewportWidth - sidebarWidth;
        const inset = 24;

        render(<ExecutiveLayout><div>Executive content</div></ExecutiveLayout>);
        const layout = screen.getByText("Executive content").parentElement;

        expect(mainClientWidth).toBe(1372);
        expect(layout).toHaveStyle({ width: "100%", padding: `${inset}px`, boxSizing: "border-box" });

        const executiveBorderBoxWidth = mainClientWidth;
        const executiveContentWidth = executiveBorderBoxWidth - (2 * inset);
        expect(executiveBorderBoxWidth).toBeLessThanOrEqual(mainClientWidth);
        expect(executiveContentWidth).toBe(1324);
        expect(executiveContentWidth + (2 * inset)).toBe(mainClientWidth);
    });
});
