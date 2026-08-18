import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { VulnerabilityThreatIntelligence } from "../ThreatIntelligence";
import { ThreatIntelligenceRequestError } from "../ThreatIntelligenceApiClient";
import ThreatIntelligenceExplorerPage from "./ThreatIntelligenceExplorerPage";

afterEach(cleanup);

describe("ThreatIntelligenceExplorerPage", () => {
    it("does not request intelligence before an explicit search", () => {
        const lookup = vi.fn();

        render(<ThreatIntelligenceExplorerPage lookup={lookup} />);

        expect(lookup).not.toHaveBeenCalled();
        expect(screen.getByRole("button", { name: "Search" })).toBeDisabled();
    });

    it("looks up the entered CVE and renders contract fields without reclassification", async () => {
        const lookup = vi.fn().mockResolvedValue(intelligence);
        render(<ThreatIntelligenceExplorerPage lookup={lookup} />);

        fireEvent.change(screen.getByLabelText("CVE identifier"), {
            target: { value: " CVE-2021-44228 " },
        });
        fireEvent.click(screen.getByRole("button", { name: "Search" }));

        expect(await screen.findByText("CVE-2021-44228")).toBeInTheDocument();
        expect(lookup).toHaveBeenCalledOnce();
        expect(lookup).toHaveBeenCalledWith("CVE-2021-44228");
        expect(screen.getByText("Contract 1.0")).toBeInTheDocument();
        expect(screen.getByText("Controlled NVD summary.")).toBeInTheDocument();
        expect(screen.getByText("10")).toBeInTheDocument();
        expect(screen.getByText("CRITICAL")).toBeInTheDocument();
        expect(screen.getByText("CVSS:3.1/AV:N")).toBeInTheDocument();
        expect(screen.getByText("0.99999")).toBeInTheDocument();
        expect(screen.getByText("1")).toBeInTheDocument();
        expect(screen.getByText("Yes (true)")).toBeInTheDocument();
        expect(screen.getByText("Apply updates.")).toBeInTheDocument();
        expect(screen.getByText("Status: not_evaluated")).toBeInTheDocument();
        expect(screen.getByText("No value supplied by the backend.")).toBeInTheDocument();
        expect(screen.getAllByText(/Source reference:/)).toHaveLength(5);
    });

    it("shows loading and prevents another submission while pending", async () => {
        let resolveLookup: (value: VulnerabilityThreatIntelligence) => void = () => {};
        const lookup = vi.fn().mockReturnValue(
            new Promise<VulnerabilityThreatIntelligence>((resolve) => {
                resolveLookup = resolve;
            }),
        );
        render(<ThreatIntelligenceExplorerPage lookup={lookup} />);

        fireEvent.change(screen.getByLabelText("CVE identifier"), {
            target: { value: "CVE-2021-44228" },
        });
        fireEvent.click(screen.getByRole("button", { name: "Search" }));

        expect(screen.getByText("Loading threat intelligence…")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Loading…" })).toBeDisabled();
        expect(screen.getByLabelText("CVE identifier")).toBeDisabled();
        resolveLookup(intelligence);
        expect(await screen.findByText("Contract 1.0")).toBeInTheDocument();
        expect(lookup).toHaveBeenCalledOnce();
    });

    it.each([
        [404, "No threat intelligence was found for this CVE."],
        [422, "The CVE identifier is invalid."],
        [503, "Threat intelligence sources are currently unavailable."],
        [null, "The PredatorAI backend is not reachable."],
    ])("renders controlled request error %s", async (status, message) => {
        const lookup = vi
            .fn()
            .mockRejectedValue(new ThreatIntelligenceRequestError(status));
        render(<ThreatIntelligenceExplorerPage lookup={lookup} />);

        fireEvent.change(screen.getByLabelText("CVE identifier"), {
            target: { value: "CVE-2021-44228" },
        });
        fireEvent.click(screen.getByRole("button", { name: "Search" }));

        expect(await screen.findByText(message)).toBeInTheDocument();
        expect(screen.queryByLabelText("Threat intelligence result")).not.toBeInTheDocument();
    });
});

const intelligence: VulnerabilityThreatIntelligence = {
    contract_version: "1.0",
    cve_identifier: "CVE-2021-44228",
    nvd: fact(
        {
            summary: "Controlled NVD summary.",
            published_at: "2021-12-10T10:15:09Z",
            last_modified_at: "2026-08-11T19:33:44Z",
        },
        "nvd",
    ),
    cvss: fact(
        {
            version: "3.1",
            base_score: 10,
            vector: "CVSS:3.1/AV:N",
            severity: "CRITICAL",
        },
        "nvd",
    ),
    epss: fact({ probability: 0.99999, percentile: 1 }, "epss"),
    cisa_kev: fact(
        {
            known_exploited: true,
            date_added: "2021-12-10",
            required_action: "Apply updates.",
            due_date: "2021-12-24",
        },
        "cisa_kev",
    ),
    exploitation_evidence: fact(null, "cisa_kev", "not_evaluated"),
};

function fact<T>(
    value: T | null,
    source: string,
    status = "available",
) {
    return {
        status,
        provenance: {
            source_type: source,
            source_reference: `${source}:reference`,
        },
        observed_at: "2026-08-17T10:07:00Z",
        value,
    };
}
