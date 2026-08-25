import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
    getAIModelGovernance,
    getGovernanceOperatorSession,
    updateAIModelSelection,
} from "../AIModelGovernanceApiClient";
import AIModelGovernancePage from "./AIModelGovernancePage";

vi.mock("../AIModelGovernanceApiClient", () => ({
    getAIModelGovernance: vi.fn(),
    getGovernanceOperatorSession: vi.fn().mockResolvedValue(null),
    updateAIModelSelection: vi.fn(),
}));

const visibility = {
    contract_version: "1.0",
    capabilities: ["finding_explanation", "hunt_hypothesis_proposal"],
    providers: [
        {
            provider: "openai",
            governance_status: "registered" as const,
            registrations: [{
                provider: "openai",
                model_id: "gpt-5.6",
                api_protocol_family: "openai_responses",
                deployment_class: "managed_provider_api",
                policy_reference: "policy:ai-model-selection:finding-explanation:1.0",
                execution_binding: "1.0",
                status: "enabled" as const,
                governance_status: "adapter_available_configuration_unavailable",
                capabilities: [
                    { capability: "finding_explanation", authorized: true, adapter_available: true, execution_available: false, active: false },
                    { capability: "hunt_hypothesis_proposal", authorized: false, adapter_available: false, execution_available: false, active: false },
                ],
            }],
        },
        ...["anthropic", "google", "local_openai_compatible"].map((provider) => ({
            provider,
            governance_status: "foundation_only" as const,
            registrations: [],
        })),
    ],
};

describe("AIModelGovernancePage", () => {
    afterEach(() => cleanup());
    beforeEach(() => {
        vi.resetAllMocks();
        vi.mocked(getGovernanceOperatorSession).mockResolvedValue(null);
    });

    it("shows a loading state", () => {
        vi.mocked(getAIModelGovernance).mockReturnValue(new Promise(() => undefined));
        render(<AIModelGovernancePage />);
        expect(screen.getByText("Loading governed model registry…")).toBeInTheDocument();
    });

    it("shows an error without fallback data", async () => {
        vi.mocked(getAIModelGovernance).mockRejectedValue(new Error("controlled"));
        render(<AIModelGovernancePage />);
        expect(await screen.findByText(/could not be loaded/)).toBeInTheDocument();
        expect(screen.getByText(/No local fallback data/)).toBeInTheDocument();
    });

    it("shows an explicit empty state", async () => {
        vi.mocked(getAIModelGovernance).mockResolvedValue({ ...visibility, providers: [] });
        render(<AIModelGovernancePage />);
        expect(await screen.findByText("No governed provider families are available")).toBeInTheDocument();
    });

    it("distinguishes registered, authorized, adapter and execution state", async () => {
        vi.mocked(getAIModelGovernance).mockResolvedValue(visibility);
        render(<AIModelGovernancePage />);

        expect(await screen.findByText("gpt-5.6")).toBeInTheDocument();
        for (const provider of ["openai", "anthropic", "google", "local_openai_compatible"]) {
            expect(screen.getByText(provider)).toBeInTheDocument();
        }
        expect(screen.getByText("Authorized: Yes · Live adapter: Yes · Executable now: No")).toBeInTheDocument();
        expect(screen.getByText("Authorized: No · Live adapter: No · Executable now: No")).toBeInTheDocument();
        expect(screen.getAllByText(/not configured or executable/)).toHaveLength(3);
    });

    it("shows capability-specific disabled reasons without free text input", async () => {
        vi.mocked(getAIModelGovernance).mockResolvedValue(visibility);
        vi.mocked(getGovernanceOperatorSession).mockResolvedValue({
            granted_permissions: ["ai_model_selection:update"],
            csrf_token: "csrf-value",
        });
        render(<AIModelGovernancePage />);

        const dropdowns = await screen.findAllByRole("combobox");
        expect(dropdowns).toHaveLength(2);
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
        fireEvent.mouseDown(dropdowns[1]);
        expect(await screen.findByRole("option", { name: /Not authorized for capability/ })).toHaveAttribute("aria-disabled", "true");
    });

    it("persists an executable selection and reports success", async () => {
        const executable = structuredClone(visibility);
        executable.providers[0].registrations[0].capabilities[0].execution_available = true;
        vi.mocked(getAIModelGovernance).mockResolvedValue(executable);
        vi.mocked(getGovernanceOperatorSession).mockResolvedValue({
            granted_permissions: ["ai_model_selection:update"],
            csrf_token: "csrf-value",
        });
        vi.mocked(updateAIModelSelection).mockResolvedValue(executable);
        render(<AIModelGovernancePage />);

        const dropdowns = await screen.findAllByRole("combobox");
        fireEvent.mouseDown(dropdowns[0]);
        fireEvent.click(await screen.findByRole("option", { name: "openai / gpt-5.6" }));

        await waitFor(() => expect(updateAIModelSelection).toHaveBeenCalledWith(
            "finding_explanation",
            "openai",
            "gpt-5.6",
            "csrf-value",
        ));
        expect(await screen.findByText("Finding Explanation selection saved.")).toBeInTheDocument();
    });

    it("shows a governed rejection without fabricating success", async () => {
        const executable = structuredClone(visibility);
        executable.providers[0].registrations[0].capabilities[0].execution_available = true;
        vi.mocked(getAIModelGovernance).mockResolvedValue(executable);
        vi.mocked(getGovernanceOperatorSession).mockResolvedValue({
            granted_permissions: ["ai_model_selection:update"],
            csrf_token: "csrf-value",
        });
        vi.mocked(updateAIModelSelection).mockRejectedValue(new Error("rejected"));
        render(<AIModelGovernancePage />);

        const dropdowns = await screen.findAllByRole("combobox");
        fireEvent.mouseDown(dropdowns[0]);
        fireEvent.click(await screen.findByRole("option", { name: "openai / gpt-5.6" }));

        expect(await screen.findByText(/selection was rejected by governance/)).toBeInTheDocument();
        expect(screen.queryByText(/selection saved/)).not.toBeInTheDocument();
    });
});
