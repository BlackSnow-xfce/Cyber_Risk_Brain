import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ExplainabilityWorkspace from "./ExplainabilityWorkspace";

describe("ExplainabilityWorkspace", () => {
    it("shows a truthful unavailable state without loading mock or provider data", () => {
        const request = vi.spyOn(globalThis, "fetch");

        render(<ExplainabilityWorkspace />);

        expect(screen.getByRole("alert", { name: "Explainability unavailable" }))
            .toHaveTextContent("No authoritative explainability context is available");
        expect(screen.getByText(/will not generate or infer an explanation/i))
            .toBeInTheDocument();
        expect(request).not.toHaveBeenCalled();
        request.mockRestore();
    });
});
