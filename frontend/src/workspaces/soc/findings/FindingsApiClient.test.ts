import { afterEach, describe, expect, it, vi } from "vitest";

import { generateFindingExplanation, getFindingRiskContext } from "./FindingsApiClient";

const responsePayload = {
    finding_id: "finding/id",
    generation_status: "GENERATED",
    factual_context: [],
    missing_context: [],
    provider_id: "openai",
    model_id: "gpt-5.6-terra",
    input_contract_version: "1.0",
    input_digest: "digest",
    used_fact_ids: [],
    source_references: [],
    model_output: {
        summary: {
            kind: "GENERAL_SECURITY_REASONING",
            text: "Summary",
            basis_fact_ids: [],
        },
        technical_reasoning: [],
        organizational_relevance: [],
        uncertainty_statement: {
            kind: "GENERAL_SECURITY_REASONING",
            text: "Uncertainty",
            basis_fact_ids: [],
        },
    },
};

afterEach(() => {
    vi.unstubAllGlobals();
});

describe("generateFindingExplanation", () => {
    it("posts to the selected finding explanation endpoint", async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify(responsePayload), {
                status: 200,
                headers: { "Content-Type": "application/json" },
            }),
        );
        vi.stubGlobal("fetch", fetchMock);

        await expect(generateFindingExplanation("finding/id")).resolves.toEqual(
            responsePayload,
        );
        expect(fetchMock).toHaveBeenCalledOnce();
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/api/findings/finding%2Fid/explanation",
            { method: "POST" },
        );
    });
});

const riskContextPayload = {
    finding_id: "finding/id",
    source_facts: [{ name: "title", value: "Finding", source_reference: "greenbone" }],
    asset_context: { status: "not_found", observed_identifier_type: "ip_address", observed_identifier_value: "192.0.2.1", canonical_asset_id: null, criticality: null, source_reference: null },
    threat_intelligence: { finding_id: "finding/id", finding_source: "greenbone", finding_title: "Finding", relationships: [] },
    correlation: { completeness_status: "no_data", source_type: "correlation", source_reference: "finding/id" },
    evidence: [],
    risk_inputs: ["business_criticality", "exposure", "detection_available", "threat_intelligence_match", "mitre_tactic"].map((name) => ({ name, state: name === "business_criticality" ? "UNKNOWN" : "NOT_EVALUATED", value: null, source: null })),
    assessment: { status: "INSUFFICIENT_CONTEXT", available_inputs: [], missing_inputs: [{ name: "exposure", state: "NOT_EVALUATED", value: null, source: null }], score: null },
    evidence_readiness: { status: "INSUFFICIENT_EVIDENCE", reason: "Missing evidence.", considered_evidence_ids: [], referenced_input_references: [], missing_requirements: ["canonical_asset_context"], completeness_status: "no_data", source_type: "readiness", source_reference: "finding/id" },
    refusal_reason: "Required context is missing.",
    priority: { status: "UNAVAILABLE", band: null, score: null, reason: "Missing context.", considered_evidence_ids: [], referenced_input_references: [], missing_requirements: ["context"], completeness_status: "no_data", source_type: "finding_risk_priority", source_reference: "finding/id" },
    business_context: { status: "NOT_FOUND", canonical_asset_id: null, business_service: null, environment: null, service_criticality: null, source_reference: null, facts: [] },
    business_impact_readiness: { finding_id: "finding/id", status: "UNAVAILABLE", reason: "Missing business context.", facts: [], missing_requirements: ["business_service", "environment", "service_criticality", "business_context_provenance"], source_references: [], completeness_status: "no_data", source_type: "business_impact_readiness", source_reference: "business-impact-readiness:unavailable:finding/id" },
    business_impact: null,
    decision: null, recommendations: [],
};

describe("getFindingRiskContext", () => {
    it("loads the encoded endpoint and accepts the complete fail-closed contract", async () => {
        const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(riskContextPayload), { status: 200 }));
        vi.stubGlobal("fetch", fetchMock);

        await expect(getFindingRiskContext("finding/id")).resolves.toEqual(riskContextPayload);
        expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/findings/finding%2Fid/risk-context");
    });

    it("rejects contradictory insufficient-context values", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
            ...riskContextPayload,
            assessment: { ...riskContextPayload.assessment, score: 42 },
        }), { status: 200 })));

        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it.each([
        ["authoritative input without provenance", {
            risk_inputs: riskContextPayload.risk_inputs.map((input) => input.name === "exposure"
                ? { ...input, state: "AUTHORITATIVE", value: true, source: null }
                : input),
        }],
        ["unknown input with a value", {
            risk_inputs: riskContextPayload.risk_inputs.map((input) => input.name === "business_criticality"
                ? { ...input, value: "HIGH" }
                : input),
        }],
        ["duplicate required input", {
            risk_inputs: [...riskContextPayload.risk_inputs, riskContextPayload.risk_inputs[0]],
        }],
        ["missing required input", {
            risk_inputs: riskContextPayload.risk_inputs.slice(1),
        }],
    ])("rejects %s", async (_label, change) => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
            ...riskContextPayload,
            ...change,
        }), { status: 200 })));

        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it("keeps evidence readiness distinct from insufficient risk context", async () => {
        const payload = {
            ...riskContextPayload,
            evidence_readiness: {
                ...riskContextPayload.evidence_readiness,
                status: "READY",
                missing_requirements: [],
                completeness_status: "available",
            },
        };
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), { status: 200 }),
        ));

        const result = await getFindingRiskContext("finding/id");
        expect(result.evidence_readiness.status).toBe("READY");
        expect(result.assessment.status).toBe("INSUFFICIENT_CONTEXT");
        expect(result.assessment.score).toBeNull();
        expect(result.recommendations).toEqual([]);
    });

    it("rejects contradictory business-impact readiness without provenance", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
            ...riskContextPayload,
            business_impact_readiness: {
                ...riskContextPayload.business_impact_readiness,
                status: "READY",
                missing_requirements: [],
                completeness_status: "available",
            },
        }), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it("accepts complete ready business context with fact and result provenance", async () => {
        const facts = [
            { name: "canonical_asset_id", value: "asset-1", source_reference: "cmdb:1" },
            { name: "business_service", value: "Payments", source_reference: "cmdb:1" },
            { name: "environment", value: "TEST", source_reference: "cmdb:1" },
            { name: "service_criticality", value: "LOW", source_reference: "cmdb:1" },
        ];
        const payload = {
            ...riskContextPayload,
            business_context: {
                status: "RESOLVED", canonical_asset_id: "asset-1",
                business_service: "Payments", environment: "TEST",
                service_criticality: "LOW", source_reference: "cmdb:1", facts,
            },
            business_impact_readiness: {
                finding_id: "finding/id", status: "READY", reason: "Complete.",
                facts, missing_requirements: [], source_references: ["cmdb:1"],
                completeness_status: "available", source_type: "business_impact_readiness",
                source_reference: "business-impact-readiness:ready:finding/id",
            },
        };
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), { status: 200 }),
        ));
        await expect(getFindingRiskContext("finding/id")).resolves.toEqual(payload);
    });
});
