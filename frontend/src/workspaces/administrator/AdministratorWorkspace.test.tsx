import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";

import AdministratorWorkspace from "./AdministratorWorkspace";
import { getAIModelGovernance } from "./AIModelGovernanceApiClient";
import { administratorNavigation } from "./navigation";

vi.mock("./AIModelGovernanceApiClient", () => ({
    getAIModelGovernance: vi.fn().mockResolvedValue({
        contract_version: "1.0",
        capabilities: [],
        providers: [],
    }),
    getGovernanceOperatorSession: vi.fn().mockResolvedValue(null),
    updateAIModelSelection: vi.fn(),
}));

describe("AdministratorWorkspace", () => {
    afterEach(() => cleanup());

    it("exposes AI Model Governance through visible navigation", () => {
        expect(administratorNavigation).toContainEqual(expect.objectContaining({
            label: "AI Models",
            route: "/administration/ai-models",
        }));
    });

    it("renders the Governance view from its authoritative URL", async () => {
        render(
            <WorkspaceProvider>
                <MemoryRouter initialEntries={["/administration/ai-models"]}>
                    <AdministratorWorkspace />
                </MemoryRouter>
            </WorkspaceProvider>,
        );

        expect(screen.getByRole("heading", { name: "AI Model Governance" })).toBeInTheDocument();
        expect(await screen.findByText("No governed provider families are available")).toBeInTheDocument();
        expect(getAIModelGovernance).toHaveBeenCalledOnce();
    });
});
