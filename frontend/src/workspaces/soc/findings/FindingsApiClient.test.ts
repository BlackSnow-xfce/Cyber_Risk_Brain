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
    service_impact_profile: { status: "NOT_FOUND", canonical_asset_id: null, business_service: null, confidentiality_importance: null, integrity_importance: null, availability_importance: null, source_reference: null },
    technical_effect: { finding_id: "finding/id", status: "UNAVAILABLE", effects: [], missing_requirements: ["applicable_technical_effect"], completeness_status: "no_data", source_type: "finding_technical_effect", source_reference: "finding-technical-effect:unavailable:finding/id" },
    business_impact_classification_readiness: { finding_id: "finding/id", status: "UNAVAILABLE", reason: "Missing authority.", business_facts: [], service_impact_facts: [], technical_effects: [], missing_requirements: ["service_impact_profile"], source_references: [], completeness_status: "no_data", source_type: "business_impact_classification_readiness", source_reference: "business-impact-classification-readiness:unavailable:finding/id" },
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

    it.each([
        ["invalid CIA importance", { service_impact_profile: { ...riskContextPayload.service_impact_profile, status: "RESOLVED", canonical_asset_id: "asset-1", business_service: "Payments", confidentiality_importance: "SEVERE", integrity_importance: "HIGH", availability_importance: "LOW", source_reference: "bia:1" } }],
        ["technical effect without provenance", { technical_effect: { ...riskContextPayload.technical_effect, status: "AVAILABLE", missing_requirements: [], completeness_status: "available", effects: [{ finding_id: "finding/id", cve_identifier: "CVE-2024-1234", cvss_vector: "CVSS:3.1/C:H/I:L/A:N", confidentiality: "HIGH", integrity: "LOW", availability: "NONE", source_reference: "", observed_at: null }] } }],
        ["classification readiness with missing requirements", { business_impact_classification_readiness: { ...riskContextPayload.business_impact_classification_readiness, status: "READY", missing_requirements: ["service_impact_profile"], completeness_status: "available", source_reference: "business-impact-classification-readiness:ready:finding/id" } }],
    ])("rejects %s", async (_label, change) => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ ...riskContextPayload, ...change }), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
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

    const readyBusinessPayload = () => {
        const facts = [
            { name: "canonical_asset_id", value: "asset-1", source_reference: "cmdb:1" },
            { name: "business_service", value: "Payments", source_reference: "cmdb:1" },
            { name: "environment", value: "PRODUCTION", source_reference: "cmdb:1" },
            { name: "service_criticality", value: "CRITICAL", source_reference: "cmdb:1" },
        ];
        return {
            ...riskContextPayload,
            business_context: {
                status: "RESOLVED", canonical_asset_id: "asset-1",
                business_service: "Payments", environment: "PRODUCTION",
                service_criticality: "CRITICAL", source_reference: "cmdb:1", facts,
            },
            business_impact_readiness: {
                finding_id: "finding/id", status: "READY", reason: "Complete.", facts,
                missing_requirements: [] as string[], source_references: ["cmdb:1"],
                completeness_status: "available", source_type: "business_impact_readiness",
                source_reference: "business-impact-readiness:ready:finding/id",
            },
        };
    };

    it.each([
        ["top-level environment differs from context fact", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_context.facts = payload.business_context.facts.map((fact) =>
                fact.name === "environment" ? { ...fact, value: "TEST" } : fact);
        }],
        ["top-level environment differs from readiness fact", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = payload.business_impact_readiness.facts.map((fact) =>
                fact.name === "environment" ? { ...fact, value: "TEST" } : fact);
        }],
        ["top-level criticality differs from context fact", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_context.facts = payload.business_context.facts.map((fact) =>
                fact.name === "service_criticality" ? { ...fact, value: "LOW" } : fact);
        }],
        ["top-level criticality differs from readiness fact", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = payload.business_impact_readiness.facts.map((fact) =>
                fact.name === "service_criticality" ? { ...fact, value: "LOW" } : fact);
        }],
        ["context and readiness values differ", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_context.environment = "TEST";
            payload.business_context.facts = payload.business_context.facts.map((fact) =>
                fact.name === "environment" ? { ...fact, value: "TEST" } : fact);
        }],
        ["fact provenance differs", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = payload.business_impact_readiness.facts.map((fact) =>
                fact.name === "service_criticality" ? { ...fact, source_reference: "cmdb:2" } : fact);
            payload.business_impact_readiness.source_references = ["cmdb:1", "cmdb:2"];
        }],
        ["required mirrored fact is missing", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = payload.business_impact_readiness.facts.slice(1);
        }],
        ["mirrored fact is duplicated", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = [
                ...payload.business_impact_readiness.facts,
                payload.business_impact_readiness.facts[0],
            ];
        }],
        ["unexpected fact is added", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = [
                ...payload.business_impact_readiness.facts,
                { name: "business_owner", value: "owner", source_reference: "cmdb:1" },
            ];
        }],
        ["canonical relationship is altered", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = payload.business_impact_readiness.facts.map((fact) =>
                fact.name === "canonical_asset_id" ? { ...fact, value: "asset-2" } : fact);
        }],
        ["business service is altered", (payload: ReturnType<typeof readyBusinessPayload>) => {
            payload.business_impact_readiness.facts = payload.business_impact_readiness.facts.map((fact) =>
                fact.name === "business_service" ? { ...fact, value: "Other" } : fact);
        }],
    ])("rejects inconsistent business snapshot: %s", async (_label, mutate) => {
        const payload = readyBusinessPayload();
        mutate(payload);
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), { status: 200 }),
        ));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it("accepts a consistent partial unavailable snapshot", async () => {
        const payload = readyBusinessPayload();
        payload.business_impact_readiness = {
            ...payload.business_impact_readiness,
            status: "UNAVAILABLE",
            facts: payload.business_impact_readiness.facts.slice(0, 2),
            missing_requirements: ["environment", "service_criticality"],
            completeness_status: "partial",
            source_reference: "business-impact-readiness:unavailable:finding/id",
        };
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), { status: 200 }),
        ));
        await expect(getFindingRiskContext("finding/id")).resolves.toEqual(payload);
    });

    const partialUnavailablePayload = (
        facts: readonly Record<string, unknown>[],
        missingRequirements: readonly string[] = ["business_service"],
    ) => ({
        ...riskContextPayload,
        business_impact_readiness: {
            ...riskContextPayload.business_impact_readiness,
            facts,
            missing_requirements: missingRequirements,
            source_references: [...new Set(facts.map((fact) => fact.source_reference))],
        },
    });

    it.each([
        ["environment BANANA", { name: "environment", value: "BANANA", source_reference: "cmdb:1" }],
        ["environment lowercase", { name: "environment", value: "production", source_reference: "cmdb:1" }],
        ["environment title case", { name: "environment", value: "Production", source_reference: "cmdb:1" }],
        ["environment invalid type", { name: "environment", value: 1, source_reference: "cmdb:1" }],
        ["service criticality SEVERE", { name: "service_criticality", value: "SEVERE", source_reference: "cmdb:1" }],
        ["service criticality lowercase", { name: "service_criticality", value: "critical", source_reference: "cmdb:1" }],
        ["service criticality title case", { name: "service_criticality", value: "Critical", source_reference: "cmdb:1" }],
        ["service criticality invalid type", { name: "service_criticality", value: true, source_reference: "cmdb:1" }],
    ])("rejects partial unavailable with invalid %s", async (_label, fact) => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(partialUnavailablePayload([fact])), { status: 200 }),
        ));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it.each([
        ["environment only", [
            { name: "environment", value: "TEST", source_reference: "cmdb:1" },
        ]],
        ["service criticality only", [
            { name: "service_criticality", value: "LOW", source_reference: "cmdb:1" },
        ]],
        ["canonical asset and service", [
            { name: "canonical_asset_id", value: "asset-1", source_reference: "cmdb:1" },
            { name: "business_service", value: "Payments", source_reference: "cmdb:1" },
        ]],
    ])("accepts valid partial unavailable %s", async (_label, facts) => {
        const missingRequirements = ["environment", "service_criticality"];
        const payload = partialUnavailablePayload(facts, missingRequirements);
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), { status: 200 }),
        ));
        const result = await getFindingRiskContext("finding/id");
        expect(result.business_impact_readiness?.status).toBe("UNAVAILABLE");
        expect(result.business_impact_readiness?.missing_requirements)
            .toEqual(missingRequirements);
        expect(result.business_impact).toBeNull();
    });

    it("rejects a partial unavailable fact contradicting resolved authority", async () => {
        const payload = readyBusinessPayload();
        payload.business_impact_readiness = {
            ...payload.business_impact_readiness,
            status: "UNAVAILABLE",
            facts: [{ name: "environment", value: "TEST", source_reference: "cmdb:1" }],
            missing_requirements: ["service_criticality"],
            completeness_status: "partial",
            source_reference: "business-impact-readiness:unavailable:finding/id",
        };
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(payload), { status: 200 }),
        ));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it("rejects duplicate partial unavailable facts", async () => {
        const fact = { name: "environment", value: "TEST", source_reference: "cmdb:1" };
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(JSON.stringify(partialUnavailablePayload([fact, fact])), { status: 200 }),
        ));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    const sourceBoundTechnicalPayload = () => {
        const observedAt = "2026-01-01T00:00:00+00:00";
        const effect = {
            finding_id: "finding/id", cve_identifier: "CVE-2024-1234", cvss_version: "3.1",
            cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N",
            confidentiality: "HIGH", integrity: "LOW", availability: "NONE",
            source_type: "nvd", source_reference: "nvd:CVE-2024-1234#cvss-3.1", observed_at: observedAt,
        };
        const unavailableFact = (sourceType: string, sourceReference: string) => ({
            status: "no_data", provenance: { source_type: sourceType, source_reference: sourceReference },
            observed_at: null, value: null,
        });
        return {
            ...riskContextPayload,
            threat_intelligence: {
                ...riskContextPayload.threat_intelligence,
                relationships: [{ applicability: "applicable", cve_identifier: "CVE-2024-1234", intelligence: {
                    contract_version: "1.0", cve_identifier: "CVE-2024-1234",
                    nvd: unavailableFact("nvd", "nvd:none"),
                    cvss: { status: "available", provenance: { source_type: "nvd", source_reference: effect.source_reference }, observed_at: observedAt,
                        value: { version: "3.1", base_score: 8, vector: effect.cvss_vector, severity: "HIGH" } },
                    epss: unavailableFact("epss", "epss:none"), cisa_kev: unavailableFact("cisa_kev", "kev:none"),
                    exploitation_evidence: unavailableFact("cisa_kev", "evidence:none"),
                }}],
            },
            technical_effect: {
                finding_id: "finding/id", status: "AVAILABLE", effects: [effect], missing_requirements: [],
                completeness_status: "available", source_type: "finding_technical_effect",
                source_reference: "finding-technical-effect:available:finding/id",
            },
            business_impact_classification_readiness: {
                ...riskContextPayload.business_impact_classification_readiness,
                technical_effects: [effect], missing_requirements: ["service_impact_profile"],
                source_references: [effect.source_reference],
            },
        };
    };

    it("accepts an exact authoritative TI-bound technical effect", async () => {
        const payload = sourceBoundTechnicalPayload();
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).resolves.toEqual(payload);
    });

    it("accepts exact string CVSS 3.0 authority", async () => {
        const payload = sourceBoundTechnicalPayload();
        const vector = "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N";
        payload.threat_intelligence.relationships[0].intelligence.cvss.value.version = "3.0";
        payload.threat_intelligence.relationships[0].intelligence.cvss.value.vector = vector;
        payload.technical_effect.effects[0].cvss_version = "3.0";
        payload.technical_effect.effects[0].cvss_vector = vector;
        payload.business_impact_classification_readiness.technical_effects = [
            { ...payload.technical_effect.effects[0] },
        ];
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).resolves.toEqual(payload);
    });

    it.each([3.1, 3, true, null, {}, []])(
        "rejects non-string Technical Effect CVSS version %j",
        async (version) => {
        const payload = sourceBoundTechnicalPayload();
        payload.technical_effect.effects[0].cvss_version = version as unknown as string;
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
        },
    );

    it("rejects a jointly numeric CVSS version across source and effect snapshots", async () => {
        const payload = sourceBoundTechnicalPayload();
        payload.threat_intelligence.relationships[0].intelligence.cvss.value.version = 3.1 as unknown as string;
        payload.technical_effect.effects[0].cvss_version = 3.1 as unknown as string;
        payload.business_impact_classification_readiness.technical_effects[0].cvss_version = 3.1 as unknown as string;
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });

    it("accepts multiple exact CVE bindings without cross-source mixing", async () => {
        const payload = sourceBoundTechnicalPayload();
        const secondEffect = {
            ...payload.technical_effect.effects[0],
            cve_identifier: "CVE-2024-5678",
            source_reference: "nvd:CVE-2024-5678#cvss-3.1",
        };
        const secondRelationship = structuredClone(payload.threat_intelligence.relationships[0]);
        secondRelationship.cve_identifier = secondEffect.cve_identifier;
        secondRelationship.intelligence.cve_identifier = secondEffect.cve_identifier;
        secondRelationship.intelligence.cvss.provenance.source_reference = secondEffect.source_reference;
        payload.threat_intelligence.relationships.push(secondRelationship);
        payload.technical_effect.effects.push(secondEffect);
        payload.business_impact_classification_readiness.technical_effects.push(secondEffect);
        payload.business_impact_classification_readiness.source_references.push(secondEffect.source_reference);
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).resolves.toEqual(payload);
    });

    it.each([
        ["CVE", (effect: Record<string, unknown>) => { effect.cve_identifier = "CVE-2024-9999"; }],
        ["version", (effect: Record<string, unknown>) => { effect.cvss_version = "3.0"; effect.cvss_vector = "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N"; }],
        ["vector", (effect: Record<string, unknown>) => { effect.cvss_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N"; effect.confidentiality = "LOW"; }],
        ["source type", (effect: Record<string, unknown>) => { effect.source_type = "epss"; }],
        ["source reference", (effect: Record<string, unknown>) => { effect.source_reference = "nvd:other"; }],
        ["observed_at", (effect: Record<string, unknown>) => { effect.observed_at = "2026-02-01T00:00:00+00:00"; }],
        ["null observed_at", (effect: Record<string, unknown>) => { effect.observed_at = null; }],
        ["confidentiality", (effect: Record<string, unknown>) => { effect.confidentiality = "LOW"; }],
        ["integrity", (effect: Record<string, unknown>) => { effect.integrity = "HIGH"; }],
        ["availability", (effect: Record<string, unknown>) => { effect.availability = "LOW"; }],
    ])("rejects jointly tampered %s not matching authoritative TI", async (_label, mutate) => {
        const payload = sourceBoundTechnicalPayload();
        mutate(payload.technical_effect.effects[0]);
        payload.business_impact_classification_readiness.technical_effects = [
            { ...payload.technical_effect.effects[0] },
        ];
        payload.business_impact_classification_readiness.source_references = [
            String(payload.technical_effect.effects[0].source_reference),
        ];
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
        await expect(getFindingRiskContext("finding/id")).rejects.toMatchObject({ status: 200 });
    });
});
