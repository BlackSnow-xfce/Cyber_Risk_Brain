import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFindingRiskContext, getFindings } from "@/workspaces/soc/findings/FindingsApiClient";
import type { FindingRiskContext } from "@/workspaces/soc/findings/FindingRiskContext";

import { loadRiskManagerProjection } from "./RiskManagerProjection";

vi.mock("@/workspaces/soc/findings/FindingsApiClient", () => ({
    getFindings: vi.fn(),
    getFindingRiskContext: vi.fn(),
}));

const context = {
    finding_id: "finding-1",
    source_facts: [],
    asset_context: {
        status: "resolved",
        observed_identifier_type: "ip",
        observed_identifier_value: "172.18.0.19",
        canonical_asset_id: "asset-1",
        criticality: "critical",
        source_reference: "asset-context:test",
    },
    threat_intelligence: { finding_id: "finding-1", finding_source: "greenbone", finding_title: "Finding 1", relationships: [] },
    correlation: { completeness_status: "COMPLETE", source_type: "correlation", source_reference: "correlation:test" },
    evidence: [],
    risk_inputs: [],
    assessment: { status: "ASSESSED", available_inputs: [], missing_inputs: [], score: 92 },
    evidence_readiness: { status: "READY", reason: "ready", considered_evidence_ids: [], referenced_input_references: [], missing_requirements: [], completeness_status: "COMPLETE", source_type: "readiness", source_reference: "readiness:test" },
    refusal_reason: null,
    priority: { status: "PRIORITIZED", band: "critical", score: 92, reason: "evidence", considered_evidence_ids: [], referenced_input_references: [], missing_requirements: [], completeness_status: "COMPLETE", source_type: "priority", source_reference: "priority:test" },
    business_context: { status: "RESOLVED", canonical_asset_id: "asset-1", business_service: "eShop", environment: "PRODUCTION", service_criticality: "CRITICAL", source_reference: "business:test", facts: [] },
    business_impact_readiness: { finding_id: "finding-1", status: "READY", reason: "ready", facts: [], missing_requirements: [], source_references: [], completeness_status: "COMPLETE", source_type: "impact-readiness", source_reference: "impact:test" },
    service_impact_profile: { status: "RESOLVED", canonical_asset_id: "asset-1", business_service: "eShop", confidentiality_importance: "HIGH", integrity_importance: "CRITICAL", availability_importance: "CRITICAL", source_reference: "service:test" },
    technical_effect: { finding_id: "finding-1", status: "AVAILABLE", effects: [], missing_requirements: [], completeness_status: "COMPLETE", source_type: "finding_technical_effect", source_reference: "technical:test" },
    business_impact_classification_readiness: { finding_id: "finding-1", status: "READY", reason: "ready", business_facts: [], service_impact_facts: [], technical_effects: [], missing_requirements: [], source_references: [], completeness_status: "COMPLETE", source_type: "business_impact_classification_readiness", source_reference: "classification:test" },
    business_impact: null,
    decision: null,
    recommendations: [],
} as unknown as FindingRiskContext;

describe("RiskManagerProjection", () => {
    beforeEach(() => vi.resetAllMocks());

    it("aggregates only existing authoritative risk context", async () => {
        vi.mocked(getFindings).mockResolvedValue([
            { id: "finding-1", source: "greenbone", title: "Finding 1", vendorSeverity: "Critical", asset: "172.18.0.19" },
        ]);
        vi.mocked(getFindingRiskContext).mockResolvedValue(context);

        const projection = await loadRiskManagerProjection();

        expect(projection.totalFindings).toBe(1);
        expect(projection.assessedFindings).toBe(1);
        expect(projection.criticalFindings).toBe(1);
        expect(projection.businessServices).toEqual(["eShop"]);
        expect(projection.unresolvedContexts).toBe(0);
    });

    it("keeps findings visible when risk context fails closed", async () => {
        vi.mocked(getFindings).mockResolvedValue([
            { id: "finding-1", source: "greenbone", title: "Finding 1", vendorSeverity: "Critical", asset: "172.18.0.19" },
        ]);
        vi.mocked(getFindingRiskContext).mockRejectedValue(new Error("unavailable"));

        const projection = await loadRiskManagerProjection();

        expect(projection.totalFindings).toBe(1);
        expect(projection.assessedFindings).toBe(0);
        expect(projection.unresolvedContexts).toBe(1);
        expect(projection.records[0].context).toBeNull();
    });
});
