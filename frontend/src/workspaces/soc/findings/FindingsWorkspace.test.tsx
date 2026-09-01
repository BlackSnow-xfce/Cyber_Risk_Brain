import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FindingsWorkspace from "./FindingsWorkspace";
import { findingsDensity } from "./FindingsPresentationDensity";
import type { FindingExplanationResult } from "./FindingExplanation";
import { FindingExplanationRequestError } from "./FindingsApiClient";
import type { FindingSummary } from "./FindingSummary";
import type { FindingRiskContext } from "./FindingRiskContext";
import type { FindingThreatIntelligenceEnrichment } from "@/workspaces/threat-intelligence/ThreatIntelligence";

afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
});

describe("local Findings typography density", () => {
    it("uses the shared hierarchy in both workspace columns", async () => {
        render(<FindingsWorkspace loadFindings={() => Promise.resolve([finding])} />);

        expect(await screen.findByText("Findings List")).toHaveAttribute("data-findings-typography", "panel-heading");
        fireEvent.click(screen.getByRole("button", { name: /Controlled scanner finding/ }));
        expect(await screen.findByText("Finding Details")).toHaveAttribute("data-findings-typography", "panel-heading");
        expect(screen.getAllByText("Asset")[0]).toHaveAttribute("data-findings-typography", "field-label");
        expect(screen.getAllByText(finding.asset)[0]).toHaveAttribute("data-findings-typography", "primary-value");
        expect(screen.getByLabelText("Search findings").closest("[data-findings-density='toolbar']")).not.toBeNull();
    });

    it("keeps a distinct readable local scale", () => {
        expect(findingsDensity.panelHeading.fontSize).toBe("0.9375rem");
        expect(findingsDensity.sectionHeading.fontSize).toBe("0.875rem");
        expect(findingsDensity.subsectionHeading.fontSize).toBe("0.8125rem");
        expect(findingsDensity.fieldLabel.fontSize).toBe("0.6875rem");
        expect(findingsDensity.primaryValue.fontSize).toBe("0.75rem");
        expect(findingsDensity.reference.lineHeight).toBe(1.3);
        expect(findingsDensity.chip.height).toBe(20);
    });
});

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

const riskContext: FindingRiskContext = {
    finding_id: finding.id,
    source_facts: [{ name: "title", value: finding.title, source_reference: finding.source }],
    asset_context: { status: "not_found", observed_identifier_type: "ip_address", observed_identifier_value: finding.asset, canonical_asset_id: null, criticality: null, source_reference: null },
    threat_intelligence: { finding_id: finding.id, finding_source: finding.source, finding_title: finding.title, relationships: [] },
    correlation: { completeness_status: "no_data", source_type: "correlation", source_reference: finding.id },
    evidence: [],
    risk_inputs: [],
    assessment: { status: "INSUFFICIENT_CONTEXT", available_inputs: [], missing_inputs: [{ name: "exposure", state: "NOT_EVALUATED", value: null, source: null }], score: null },
    evidence_readiness: { status: "INSUFFICIENT_EVIDENCE", reason: "Missing evidence.", considered_evidence_ids: [], referenced_input_references: [], missing_requirements: ["canonical_asset_context"], completeness_status: "no_data", source_type: "readiness", source_reference: finding.id },
    refusal_reason: "Required context is missing.", priority: null, business_impact: null,
    decision: null, recommendations: [],
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

async function selectFinding(name: RegExp = /Controlled scanner finding/) {
    fireEvent.click(await screen.findByRole("button", { name }));
}

describe("FindingsWorkspace", () => {
    it("shows the loading state", () => {
        render(
            <FindingsWorkspace
                loadFindings={() => new Promise(() => undefined)}
            />,
        );

        expect(screen.getByText("Loading live findings")).toBeInTheDocument();
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

    it("filters findings and resets to all findings when search is cleared", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding, secondFinding])}
            />,
        );

        const search = await screen.findByLabelText("Search findings");
        fireEvent.change(search, { target: { value: "Second" } });

        expect(screen.getByText("Second controlled finding")).toBeInTheDocument();
        expect(
            screen.queryByRole("button", { name: /Controlled scanner finding/ }),
        ).toBeNull();

        fireEvent.change(search, { target: { value: "" } });
        expect(screen.getAllByText("Controlled scanner finding").length).toBeGreaterThan(0);
    });

    it("gives the detail panel update feedback when the selected finding changes", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding, secondFinding])}
            />,
        );

        await screen.findAllByText("Controlled scanner finding");
        fireEvent.click(screen.getByRole("button", { name: /Second controlled finding/ }));

        expect(window.location.pathname).toBe("/findings");
        expect(window.location.search).toBe("?findingId=result-002");

        await waitFor(() => {
            expect(screen.getByRole("complementary")).toHaveClass("finding-details-panel--updated");
        });
    });

    it.each([null, "unknown-finding"])(
        "does not implicitly select a finding for URL context %s",
        async (findingId) => {
            window.history.replaceState(
                {},
                "",
                findingId ? `/findings?findingId=${findingId}` : "/findings",
            );
            render(
                <FindingsWorkspace
                    loadFindings={() => Promise.resolve([finding, secondFinding])}
                />,
            );

            await screen.findByText("Select a finding to review its details.");
            expect(screen.getByRole("button", { name: /Controlled scanner finding/ }))
                .toHaveAttribute("aria-pressed", "false");
            expect(screen.getByRole("button", { name: /Second controlled finding/ }))
                .toHaveAttribute("aria-pressed", "false");
        },
    );

    it("restores the canonical selection with browser Back and Forward", async () => {
        window.history.replaceState({}, "", "/findings?findingId=result-001");
        try {
            render(
                <FindingsWorkspace
                    loadFindings={() => Promise.resolve([finding, secondFinding])}
                />,
            );
            await screen.findAllByText("Controlled scanner finding");
            fireEvent.click(screen.getByRole("button", { name: /Second controlled finding/ }));

            window.history.back();
            await waitFor(() => {
                expect(screen.getByRole("button", { name: /Controlled scanner finding/ }))
                    .toHaveAttribute("aria-pressed", "true");
            });

            window.history.forward();
            await waitFor(() => {
                expect(screen.getByRole("button", { name: /Second controlled finding/ }))
                    .toHaveAttribute("aria-pressed", "true");
            });
        } finally {
            window.history.replaceState({}, "", "/");
        }
    });

    it("clears dependent detail state and ignores stale responses on URL changes", async () => {
        window.history.replaceState({}, "", "/findings?findingId=result-001");
        const pendingIncidents = deferred<readonly [{
            incident_id: string;
            relationship_id: string;
            relationship_role: string;
            lifecycle_status: string;
        }]>();
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding, secondFinding])}
                loadFindingIncidents={() => pendingIncidents.promise}
            />,
        );

        fireEvent.click(await screen.findByRole("button", { name: "Load incidents" }));
        window.history.pushState({}, "", "/findings?findingId=manipulated");
        window.dispatchEvent(new PopStateEvent("popstate"));
        await screen.findByText("Select a finding to review its details.");

        await act(async () => {
            pendingIncidents.resolve([{
                incident_id: "stale-incident",
                relationship_id: "stale-relationship",
                relationship_role: "investigation_candidate",
                lifecycle_status: "investigating",
            }]);
            await pendingIncidents.promise;
        });

        expect(screen.queryByText("stale-incident")).not.toBeInTheDocument();
        expect(screen.queryByText("Loading linked incidents…")).not.toBeInTheDocument();
    });

    it("shows an empty state when search has no matching finding", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
            />,
        );

        const search = await screen.findByLabelText("Search findings");
        fireEvent.change(search, { target: { value: "does-not-exist" } });

        expect(
            screen.getByText("No findings match the current search."),
        ).toBeInTheDocument();
    });

    it("restores a deep-linked finding and automatically loads focused threat intelligence", async () => {
        window.history.pushState({}, "", "/findings?findingId=result-001&focus=threat-intelligence");
        const loadThreatIntelligence = vi.fn<() => Promise<FindingThreatIntelligenceEnrichment>>().mockResolvedValue({
            finding_id: finding.id,
            finding_source: finding.source,
            finding_title: finding.title,
            relationships: [],
        });

        try {
            render(
                <FindingsWorkspace
                    loadFindings={() => Promise.resolve([finding, secondFinding])}
                    loadThreatIntelligence={loadThreatIntelligence}
                />,
            );

            expect(await screen.findByText("Threat Intelligence")).toBeInTheDocument();
            expect(loadThreatIntelligence).toHaveBeenCalledWith(finding.id);
            await waitFor(() => {
                expect(screen.getByRole("complementary")).toHaveClass("finding-details-panel--updated");
            });
        } finally {
            window.history.pushState({}, "", "/");
        }
    });

    it("loads linked incidents from the selected finding details", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
                loadFindingIncidents={() =>
                    Promise.resolve([
                        {
                            incident_id: "incident-task0077-distcc-live",
                            relationship_id: "relationship-1",
                            relationship_role: "investigation_candidate",
                            lifecycle_status: "investigating",
                        },
                    ])
                }
            />,
        );

        await selectFinding();
        fireEvent.click(await screen.findByRole("button", { name: "Load incidents" }));

        expect(
            await screen.findByRole("link", {
                name: /incident-task0077-distcc-live/,
            }),
        ).toHaveAttribute(
            "href",
            "/incident-response/incidents/incident-task0077-distcc-live/command-center",
        );
    });

    it("shows a controlled error when refresh fails", async () => {
        const loadFindings = vi
            .fn()
            .mockResolvedValueOnce([finding])
            .mockRejectedValueOnce(new Error("offline"));

        render(<FindingsWorkspace loadFindings={loadFindings} />);
        await screen.findAllByText("Controlled scanner finding");

        fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

        expect(
            await screen.findByText("Live findings could not be loaded."),
        ).toBeInTheDocument();
    });

    it("renders only fields from the minimal findings contract", async () => {
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
            />,
        );

        await selectFinding();
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

    it("loads risk context only on request and discards it when selection changes", async () => {
        const pending = deferred<FindingRiskContext>();
        const loadRiskContext = vi.fn(() => pending.promise);
        render(<FindingsWorkspace
            loadFindings={() => Promise.resolve([finding, secondFinding])}
            loadRiskContext={loadRiskContext}
        />);

        await selectFinding();
        expect(loadRiskContext).not.toHaveBeenCalled();
        fireEvent.click(await screen.findByRole("button", { name: "Load risk context" }));
        expect(loadRiskContext).toHaveBeenCalledWith(finding.id);
        fireEvent.click(screen.getByRole("button", { name: /Second controlled finding/ }));

        await act(async () => {
            pending.resolve(riskContext);
            await pending.promise;
        });
        expect(screen.queryByText("Required context is missing.")).not.toBeInTheDocument();
    });

    it("rejects a stale risk response after navigation returns to the same finding", async () => {
        const pending = deferred<FindingRiskContext>();
        render(<FindingsWorkspace
            loadFindings={() => Promise.resolve([finding, secondFinding])}
            loadRiskContext={() => pending.promise}
        />);

        await selectFinding();
        fireEvent.click(await screen.findByRole("button", { name: "Load risk context" }));
        fireEvent.click(screen.getByRole("button", { name: /Second controlled finding/ }));
        fireEvent.click(screen.getByRole("button", { name: /Controlled scanner finding/ }));

        await act(async () => {
            pending.resolve(riskContext);
            await pending.promise;
        });

        expect(screen.queryByText("Required context is missing.")).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Load risk context" })).toBeEnabled();
    });

    it("renders a requested fail-closed risk context without invoking decisions", async () => {
        const loadRiskContext = vi.fn(() => Promise.resolve(riskContext));
        render(<FindingsWorkspace
            loadFindings={() => Promise.resolve([finding])}
            loadRiskContext={loadRiskContext}
        />);

        await selectFinding();
        fireEvent.click(await screen.findByRole("button", { name: "Load risk context" }));

        expect(
            await screen.findByText("Evidence requirement: canonical_asset_context"),
        ).toBeInTheDocument();
        expect(screen.getByText(/PredatorAI refuses to calculate risk, priority/)).toBeInTheDocument();
        expect(loadRiskContext).toHaveBeenCalledExactlyOnceWith(finding.id);
        expect(screen.queryByText("Decision")).not.toBeInTheDocument();
    });

    it("requests the selected finding and renders the structured result", async () => {
        const loadExplanation = vi.fn(() => Promise.resolve(generatedExplanation));
        render(
            <FindingsWorkspace
                loadFindings={() => Promise.resolve([finding])}
                loadExplanation={loadExplanation}
            />,
        );

        await selectFinding();
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

        await selectFinding();
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

        await selectFinding();
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
        [404, "Finding explanation is not available for this finding."],
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

        await selectFinding();
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

        await selectFinding();
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
