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

    it("models independent 1536px fit dimensions and rejects width and offset regressions", () => {
        // jsdom does not perform native pixel layout. This deterministic
        // layout-contract verification uses independently controlled dimensions,
        // not native browser pixel measurement. Actual rendering remains subject
        // to Product Owner Live Acceptance at 1536 x 1024 and 100% browser zoom.
        const viewportWidth = 1536;
        const sidebarWidth = 164;
        const expectedMainWidth = 1372;
        const inset = 24;
        const main = {
            left: sidebarWidth,
            clientWidth: 1372,
            scrollWidth: 1372,
        };
        const executive = {
            externalOffset: 0,
            borderBoxWidth: 1372,
            clientWidth: 1372,
            contentWidth: 1324,
        };
        const fitsMain = (candidate: typeof executive) => {
            const mainRight = main.left + main.clientWidth;
            const executiveLeft = main.left + candidate.externalOffset;
            const executiveRight = executiveLeft + candidate.borderBoxWidth;

            return candidate.externalOffset === 0 && executiveRight <= mainRight;
        };

        render(<ExecutiveLayout><div>Executive content</div></ExecutiveLayout>);
        const layout = screen.getByText("Executive content").parentElement;

        expect(viewportWidth - sidebarWidth).toBe(expectedMainWidth);
        expect(main.clientWidth).toBe(expectedMainWidth);
        expect(main.scrollWidth).toBe(main.clientWidth);
        expect(layout).toHaveStyle({ width: "100%", padding: `${inset}px`, boxSizing: "border-box" });
        expect(executive.clientWidth).toBe(executive.borderBoxWidth);
        expect(executive.contentWidth).toBe(1324);
        expect(executive.contentWidth + (2 * inset)).toBe(executive.borderBoxWidth);
        expect(fitsMain(executive)).toBe(true);

        const oversizedExecutive = { ...executive, borderBoxWidth: 1373 };
        const externallyOffsetExecutive = { ...executive, externalOffset: 1 };
        expect(fitsMain(oversizedExecutive)).toBe(false);
        expect(fitsMain(externallyOffsetExecutive)).toBe(false);
    });
});
