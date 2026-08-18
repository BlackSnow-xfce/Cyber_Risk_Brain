import { afterEach, describe, expect, it, vi } from "vitest";

import {
    getFindingThreatIntelligence,
    getVulnerabilityThreatIntelligence,
    ThreatIntelligenceRequestError,
} from "./ThreatIntelligenceApiClient";

const payload = {
    contract_version: "1.0",
    cve_identifier: "CVE-2021-44228",
    nvd: fact({ summary: "NVD summary", published_at: null, last_modified_at: null }, "nvd"),
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

afterEach(() => {
    vi.unstubAllGlobals();
});

describe("getVulnerabilityThreatIntelligence", () => {
    it("uses the existing PredatorAI vulnerability intelligence endpoint", async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), {
                status: 200,
                headers: { "Content-Type": "application/json" },
            }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(
            getVulnerabilityThreatIntelligence("CVE-2021/44228"),
        ).resolves.toEqual(payload);
        expect(fetchMock).toHaveBeenCalledOnce();
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/threat-intelligence/vulnerabilities/CVE-2021%2F44228",
        );
    });

    it("rejects a response that does not match contract 1.0 shape", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue(
                new Response(JSON.stringify({ ...payload, epss: {} }), {
                    status: 200,
                }),
            ),
        );

        await expect(
            getVulnerabilityThreatIntelligence("CVE-2021-44228"),
        ).rejects.toEqual(new ThreatIntelligenceRequestError(200));
    });
});

describe("getFindingThreatIntelligence", () => {
    it("uses only the selected PredatorAI finding intelligence endpoint", async () => {
        const enrichment = {
            finding_id: "finding/id",
            finding_source: "greenbone",
            finding_title: "Controlled finding",
            relationships: [
                {
                    applicability: "applicable",
                    cve_identifier: payload.cve_identifier,
                    intelligence: payload,
                },
            ],
        };
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(enrichment), {
                status: 200,
                headers: { "Content-Type": "application/json" },
            }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(getFindingThreatIntelligence("finding/id")).resolves.toEqual(
            enrichment,
        );
        expect(fetchMock).toHaveBeenCalledOnce();
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/findings/finding%2Fid/threat-intelligence",
        );
    });

    it("rejects a malformed finding intelligence response", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue(
                new Response(
                    JSON.stringify({
                        finding_id: "finding-1",
                        finding_source: "greenbone",
                        finding_title: "Finding",
                        relationships: [{ applicability: "applicable" }],
                    }),
                    { status: 200 },
                ),
            ),
        );

        await expect(
            getFindingThreatIntelligence("finding-1"),
        ).rejects.toEqual(new ThreatIntelligenceRequestError(200));
    });
});

function fact(value: unknown, source: string, status = "available") {
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
