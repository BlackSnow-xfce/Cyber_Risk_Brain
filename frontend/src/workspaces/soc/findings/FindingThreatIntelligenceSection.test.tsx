import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
    FindingThreatIntelligenceEnrichment,
    VulnerabilityThreatIntelligence,
} from "@/workspaces/threat-intelligence/ThreatIntelligence";
import { ThreatIntelligenceRequestError } from "@/workspaces/threat-intelligence/ThreatIntelligenceApiClient";

import FindingsWorkspace from "./FindingsWorkspace";
import type { FindingSummary } from "./FindingSummary";

afterEach(cleanup);

const finding: FindingSummary = {
    id: "finding-1",
    source: "greenbone",
    title: "DistCC RCE Vulnerability",
    vendorSeverity: "Critical",
    asset: "172.18.0.19",
};

const secondFinding: FindingSummary = {
    ...finding,
    id: "finding-2",
    title: "Second finding",
};

const intelligence: VulnerabilityThreatIntelligence = {
    contract_version: "1.0",
    cve_identifier: "CVE-2004-2687",
    nvd: fact(
        {
            summary: "Controlled NVD summary.",
            published_at: null,
            last_modified_at: null,
        },
        "nvd",
    ),
    cvss: fact(
        {
            version: "2.0",
            base_score: 9.3,
            vector: "AV:N/AC:M/Au:N/C:C/I:C/A:C",
            severity: "HIGH",
        },
        "nvd",
    ),
    epss: fact({ probability: 0.88195, percentile: 0.99755 }, "epss"),
    cisa_kev: fact(
        {
            known_exploited: false,
            date_added: null,
            required_action: null,
            due_date: null,
        },
        "cisa_kev",
    ),
    exploitation_evidence: fact(null, "cisa_kev", "not_evaluated"),
};

const enrichment: FindingThreatIntelligenceEnrichment = {
    finding_id: finding.id,
    finding_source: finding.source,
    finding_title: finding.title,
    relationships: [
        {
            applicability: "applicable",
            cve_identifier: intelligence.cve_identifier,
            intelligence,
        },
    ],
};

describe("finding threat intelligence integration", () => {
    it("does not load intelligence on initial load or finding selection", async () => {
        const lookup = vi.fn().mockResolvedValue(enrichment);
        renderWorkspace(lookup, [finding, secondFinding]);

        await screen.findByText("Second finding");
        expect(lookup).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: /Second finding/ }));
        expect(lookup).not.toHaveBeenCalled();
    });

    it("loads the selected finding and renders the complete backend result", async () => {
        const lookup = vi.fn().mockResolvedValue(enrichment);
        renderWorkspace(lookup);

        fireEvent.click(
            await screen.findByRole("button", { name: "Load Threat Intelligence" }),
        );

        expect(await screen.findByText("CVE-2004-2687")).toBeInTheDocument();
        expect(lookup).toHaveBeenCalledOnce();
        expect(lookup).toHaveBeenCalledWith("finding-1");
        expect(screen.getByText("Applicability: applicable")).toBeInTheDocument();
        expect(screen.getByText("Contract 1.0")).toBeInTheDocument();
        expect(screen.getByText("Controlled NVD summary.")).toBeInTheDocument();
        expect(screen.getByText("9.3")).toBeInTheDocument();
        expect(screen.getByText("HIGH")).toBeInTheDocument();
        expect(screen.getByText("AV:N/AC:M/Au:N/C:C/I:C/A:C")).toBeInTheDocument();
        expect(screen.getByText("0.88195")).toBeInTheDocument();
        expect(screen.getByText("0.99755")).toBeInTheDocument();
        expect(screen.getByText("No (false)")).toBeInTheDocument();
        expect(screen.getByText("Status: not_evaluated")).toBeInTheDocument();
        expect(screen.getAllByText(/Source reference:/)).toHaveLength(5);
        expect(screen.getAllByText(/Observed at:/)).toHaveLength(5);
        expect(screen.getAllByText("Not provided").length).toBeGreaterThan(0);
    });

    it("renders every CVE in backend order without ranking", async () => {
        const secondIntelligence = {
            ...intelligence,
            cve_identifier: "CVE-2011-5094",
        };
        const multi: FindingThreatIntelligenceEnrichment = {
            ...enrichment,
            relationships: [
                enrichment.relationships[0],
                {
                    applicability: "applicable",
                    cve_identifier: secondIntelligence.cve_identifier,
                    intelligence: secondIntelligence,
                },
            ],
        };
        renderWorkspace(vi.fn().mockResolvedValue(multi));

        fireEvent.click(
            await screen.findByRole("button", { name: "Load Threat Intelligence" }),
        );

        const identifiers = await screen.findAllByText(/CVE-(2004-2687|2011-5094)/);
        expect(identifiers.map((element) => element.textContent)).toEqual([
            "CVE-2004-2687",
            "CVE-2011-5094",
        ]);
    });

    it("renders not applicable without an intelligence card", async () => {
        renderWorkspace(
            vi.fn().mockResolvedValue({
                ...enrichment,
                relationships: [
                    {
                        applicability: "not_applicable",
                        cve_identifier: null,
                        intelligence: null,
                    },
                ],
            }),
        );

        fireEvent.click(
            await screen.findByRole("button", { name: "Load Threat Intelligence" }),
        );

        expect(
            await screen.findByText(/Applicability: not_applicable/),
        ).toBeInTheDocument();
        expect(screen.queryByLabelText("Threat intelligence result")).toBeNull();
    });

    it("prevents duplicate requests and discards stale results", async () => {
        const pending = deferred<FindingThreatIntelligenceEnrichment>();
        const lookup = vi.fn().mockReturnValue(pending.promise);
        renderWorkspace(lookup, [finding, secondFinding]);

        const loadButton = await screen.findByRole("button", {
            name: "Load Threat Intelligence",
        });
        fireEvent.click(loadButton);
        fireEvent.click(loadButton);
        expect(lookup).toHaveBeenCalledOnce();
        expect(screen.getByRole("button", { name: "Loading" })).toBeDisabled();

        fireEvent.click(screen.getByRole("button", { name: /Second finding/ }));
        await act(async () => {
            pending.resolve(enrichment);
            await pending.promise;
        });
        expect(screen.queryByText("CVE-2004-2687")).toBeNull();
        expect(screen.queryByText("Loading finding threat intelligence")).toBeNull();
    });

    it.each([
        [404, "Threat intelligence is not available for this finding."],
        [503, "Threat intelligence sources are currently unavailable."],
        [500, "Threat intelligence could not be loaded for this finding."],
        [null, "Threat intelligence request could not reach the service."],
    ])("renders controlled request error %s", async (status, message) => {
        renderWorkspace(
            vi.fn().mockRejectedValue(new ThreatIntelligenceRequestError(status)),
        );

        fireEvent.click(
            await screen.findByRole("button", { name: "Load Threat Intelligence" }),
        );
        expect(await screen.findByText(message)).toBeInTheDocument();
    });
});

function renderWorkspace(
    lookup: (findingId: string) => Promise<FindingThreatIntelligenceEnrichment>,
    findings: readonly FindingSummary[] = [finding],
) {
    render(
        <FindingsWorkspace
            loadFindings={() => Promise.resolve(findings)}
            loadThreatIntelligence={lookup}
        />,
    );
}

function fact<T>(value: T | null, source: string, status = "available") {
    return {
        status,
        provenance: {
            source_type: source,
            source_reference: `${source}:reference`,
        },
        observed_at: "2026-08-17T12:54:42Z",
        value,
    };
}

function deferred<Value>() {
    let resolve!: (value: Value) => void;
    const promise = new Promise<Value>((promiseResolve) => {
        resolve = promiseResolve;
    });
    return { promise, resolve };
}
