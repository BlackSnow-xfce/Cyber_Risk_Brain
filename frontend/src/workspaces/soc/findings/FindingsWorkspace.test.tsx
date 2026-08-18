import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FindingsWorkspace from "./FindingsWorkspace";
import type { FindingExplanationResult } from "./FindingExplanation";
import { FindingExplanationRequestError } from "./FindingsApiClient";
import type { FindingSummary } from "./FindingSummary";

afterEach(cleanup);

const finding: FindingSummary = {
    id: "result-001",
    source: "greenbone",
    title: "Controlled scanner finding",
    vendorSeverity: "Medium",
    asset: "192.0.2.10",
};

const secondFinding: FindingSummary = {
    id: "result-002",
    source: "greenbone",
    title: "Second controlled finding",
    vendorSeverity: "Low",
    asset: "192.0.2.11",
};

const generatedExplanation: FindingExplanationResult = {
    finding_id: finding.id,
    generation_status: "GENERATED",
    factual_context: [
        {
            fact_id: "finding.title",
            value: finding.title,
            source_reference: null,
        },
    ],
    missing_context: [
        { name: "exposure", state: "NOT_EVALUATED" },
        { name: "mitre_tactic", state: "NOT_EVALUATED" },
    ],
    provider_id: "openai",
    model_id: "gpt-5.6-terra",
    input_contract_version: "1.0",
    input_digest: "controlled-digest",
    used_fact_ids: ["finding.title", "risk.exposure_state"],
    source_references: ["controlled-source"],
    model_output: {
        summary: {
            kind: "CONTEXTUAL_INFERENCE",
            text: "Controlled summary.",
            basis_fact_ids: ["finding.title"],
        },
        technical_reasoning: [
            {
                kind: "GENERAL_SECURITY_REASONING",
                text: "First technical statement.",
                basis_fact_ids: [],
            },
            {
                kind: "CONTEXTUAL_INFERENCE",
                text: "Second technical statement.",
                basis_fact_ids: ["finding.title"],
            },
        ],
        organizational_relevance: [
            {
                kind: "CONTEXTUAL_INFERENCE",
                text: "First organizational statement.",
                basis_fact_ids: ["finding.title"],
            },
            {
                kind: "CONTEXTUAL_INFERENCE",
                text: "Second organizational statement.",
                basis_fact_ids: ["risk.exposure_state"],
            },
        ],
        uncertainty_statement: {
            kind: "CONTEXTUAL_INFERENCE",
            text: "Controlled uncertainty.",
            basis_fact_ids: ["risk.exposure_state"],
        },
    },
};

function deferred<Value>() {
    let resolve!: (value: Value) => void;
    const promise = new Promise<Value>((promiseResolve) => {
        resolve = promiseResolve;
    });
    return { promise, resolve };
}

describe("FindingsWorkspace", () => {
    it("shows the loading state", () => {
        render(
            <FindingsWorkspace
                loadFindings={() => new Promise(() => undefined)}
            />,
        );

        expect(screen.getByText("Loading live findings…")).toBeInTheDocument();
    });

    it("shows the error state without mock fallback", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.reject(new Error("offline"))}
            />,
        );

        expect(
            await screen.findByText("Live findings could not be loaded."),
        ).toBeInTheDocument();
        expect(screen.queryByText("Internet-facing vulnerability")).toBeNull();
    });

    it("shows the empty state", async () => {
        render(
            <FindingsWorkspace loadFindings={() => Promise.resolve([])} />,
        );

        expect(
            await screen.findByText("No live findings are available."),
        ).toBeInTheDocument();
    });

    it("renders only fields from the minimal findings contract", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
            />,
        );

        expect(
            await screen.findAllByText("Controlled scanner finding"),
        ).toHaveLength(2);
        expect(screen.getAllByText("greenbone")).toHaveLength(2);
        expect(screen.getAllByText("192.0.2.10")).toHaveLength(2);
        expect(screen.getAllByText("Medium")).toHaveLength(1);
        expect(screen.queryByText("Risk Score")).toBeNull();
        expect(screen.queryByText("Confidence")).toBeNull();
        expect(screen.queryByText("Recommendations")).toBeNull();
    });

    it("does not request an explanation on load or finding selection", async () => {
        const loadExplanation = vi.fn(() => Promise.resolve(generatedExplanation));
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding, secondFinding])}
                loadExplanation={loadExplanation}
            />,
        );

        await screen.findByText("Second controlled finding");
        expect(loadExplanation).not.toHaveBeenCalled();

        fireEvent.click(
            screen.getByRole("button", { name: /Second controlled finding/ }),
        );
        expect(loadExplanation).not.toHaveBeenCalled();
    });

    it("requests the selected finding and renders the structured result", async () => {
        const loadExplanation = vi.fn(() => Promise.resolve(generatedExplanation));
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
                loadExplanation={loadExplanation}
            />,
        );

        fireEvent.click(
            await screen.findByRole("button", {
                name: "Generate AI Explanation",
            }),
        );

        expect(await screen.findByText("Controlled summary.")).toBeInTheDocument();
        expect(loadExplanation).toHaveBeenCalledTimes(1);
        expect(loadExplanation).toHaveBeenCalledWith("result-001");
        expect(screen.getByText("First technical statement.")).toBeInTheDocument();
        expect(screen.getByText("Second technical statement.")).toBeInTheDocument();
        expect(
            screen.getByText("First organizational statement."),
        ).toBeInTheDocument();
        expect(
            screen.getByText("Second organizational statement."),
        ).toBeInTheDocument();
        expect(screen.getByText("Controlled uncertainty.")).toBeInTheDocument();
        expect(screen.getByText("GENERAL_SECURITY_REASONING")).toBeInTheDocument();
        expect(screen.getAllByText("CONTEXTUAL_INFERENCE").length).toBeGreaterThan(0);
        expect(screen.getAllByText("finding.title").length).toBeGreaterThan(0);
        expect(
            screen.getByText("exposure: NOT_EVALUATED"),
        ).toBeInTheDocument();
        expect(screen.getByText("mitre_tactic: NOT_EVALUATED")).toBeInTheDocument();
        expect(screen.getByText("Status GENERATED")).toBeInTheDocument();
        expect(screen.getByText("Provider openai")).toBeInTheDocument();
        expect(screen.getByText("Model gpt-5.6-terra")).toBeInTheDocument();
        expect(screen.getByText("Contract 1.0")).toBeInTheDocument();
        expect(screen.getByText("Source controlled-source")).toBeInTheDocument();
    });

    it("prevents repeated generation while a request is pending", async () => {
        const pending = deferred<FindingExplanationResult>();
        const loadExplanation = vi.fn(() => pending.promise);
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
                loadExplanation={loadExplanation}
            />,
        );

        const button = await screen.findByRole("button", {
            name: "Generate AI Explanation",
        });
        fireEvent.click(button);
        fireEvent.click(button);

        expect(loadExplanation).toHaveBeenCalledTimes(1);
        expect(screen.getByRole("button", { name: "Generating…" })).toBeDisabled();
        expect(screen.getByText("Generating explanation…")).toBeInTheDocument();
    });

    it("does not apply a stale response after the selected finding changes", async () => {
        const pending = deferred<FindingExplanationResult>();
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding, secondFinding])}
                loadExplanation={() => pending.promise}
            />,
        );

        fireEvent.click(
            await screen.findByRole("button", {
                name: "Generate AI Explanation",
            }),
        );
        fireEvent.click(
            screen.getByRole("button", { name: /Second controlled finding/ }),
        );

        await act(async () => {
            pending.resolve(generatedExplanation);
            await pending.promise;
        });

        expect(screen.queryByText("Controlled summary.")).toBeNull();
        expect(screen.queryByText("Generating explanation…")).toBeNull();
    });

    it.each([
        [404, "The selected finding is no longer available."],
        [503, "Finding explanation service is temporarily unavailable."],
        [500, "Finding explanation could not be generated."],
        [null, "Finding explanation request could not reach the service."],
    ])("shows a controlled request error for status %s", async (status, message) => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
                loadExplanation={() =>
                    Promise.reject(new FindingExplanationRequestError(status))
                }
            />,
        );

        fireEvent.click(
            await screen.findByRole("button", {
                name: "Generate AI Explanation",
            }),
        );

        expect(await screen.findByText(message)).toBeInTheDocument();
    });

    it("shows a controlled non-generated result without reinterpretation", async () => {
        const controlledFailure: FindingExplanationResult = {
            ...generatedExplanation,
            generation_status: "PROVIDER_ERROR",
            provider_id: "openai",
            model_output: null,
            used_fact_ids: [],
            source_references: [],
        };
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
                loadExplanation={() => Promise.resolve(controlledFailure)}
            />,
        );

        fireEvent.click(
            await screen.findByRole("button", {
                name: "Generate AI Explanation",
            }),
        );

        expect(
            await screen.findByText("Explanation status: PROVIDER_ERROR"),
        ).toBeInTheDocument();
        expect(screen.getByText("Status PROVIDER_ERROR")).toBeInTheDocument();
        expect(screen.queryByText("Controlled summary.")).toBeNull();
    });
});
