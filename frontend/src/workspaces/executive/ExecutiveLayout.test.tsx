import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ExecutiveLayout from "./ExecutiveLayout";

describe("ExecutiveLayout", () => {
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
});
