import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ExplainabilityPage from "./ExplainabilityPage";

vi.mock("../explainability/ExplainabilityWorkspace", () => ({
    default: () => {
        throw new Error("controlled render failure");
    },
}));

describe("ExplainabilityPage render boundary", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("keeps the page shell visible when Explainability rendering fails", () => {
        vi.spyOn(console, "error").mockImplementation(() => undefined);

        render(<ExplainabilityPage />);

        expect(screen.getByRole("heading", { name: "Explainability" })).toBeInTheDocument();
        expect(screen.getByRole("alert", { name: "Explainability error" }))
            .toHaveTextContent("No explanation or security conclusion was generated");
    });
});
