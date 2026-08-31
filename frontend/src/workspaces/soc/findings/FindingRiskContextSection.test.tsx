import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { FindingRiskContext } from "./FindingRiskContext";
import FindingRiskContextSection from "./FindingRiskContextSection";

const context: FindingRiskContext = {
    finding_id: "finding-001",
    source_facts: [{ name: "title", value: "Controlled finding", source_reference: "greenbone" }],
    asset_context: { status: "not_found", observed_identifier_type: "ip_address", observed_identifier_value: "192.0.2.1", canonical_asset_id: null, criticality: null, source_reference: null },
    threat_intelligence: { finding_id: "finding-001", finding_source: "greenbone", finding_title: "Controlled finding", relationships: [] },
    correlation: { completeness_status: "no_data", source_type: "security_observation_correlation", source_reference: "canonical-asset-context-unresolved" },
    evidence: [],
    risk_inputs: [],
    assessment: {
        status: "INSUFFICIENT_CONTEXT",
        available_inputs: [],
        missing_inputs: [{ name: "exposure", state: "NOT_EVALUATED", value: null, source: null }],
        score: null,
    },
    evidence_readiness: {
        status: "INSUFFICIENT_EVIDENCE",
        reason: "Canonical evidence is missing.",
        considered_evidence_ids: [], referenced_input_references: [],
        missing_requirements: ["canonical_asset_context"],
        completeness_status: "no_data", source_type: "risk_assessment_readiness",
        source_reference: "risk-assessment-readiness:insufficient:finding-001",
    },
    refusal_reason: "Risk calculation refused because required context is missing.",
    priority: {
        status: "UNAVAILABLE",
        band: null,
        score: null,
        reason: "Required authoritative context is missing.",
        considered_evidence_ids: [],
        referenced_input_references: [],
        missing_requirements: ["risk_input:exposure:NOT_EVALUATED"],
        completeness_status: "no_data",
        source_type: "finding_risk_priority",
        source_reference: "finding-risk-priority:unavailable:finding-001",
    },
    business_impact: null, decision: null, recommendations: [],
};

describe("FindingRiskContextSection", () => {
    it("renders controlled loading and error lifecycle states", () => {
        const { rerender } = render(
            <FindingRiskContextSection context={null} error={null} loading onLoad={vi.fn()} />,
        );
        expect(screen.getByRole("progressbar")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Loading" })).toBeDisabled();

        rerender(
            <FindingRiskContextSection
                context={null}
                error="Risk context is unavailable."
                loading={false}
                onLoad={vi.fn()}
            />,
        );
        expect(screen.getByRole("alert")).toHaveTextContent("Risk context is unavailable.");
    });

    it("shows provenance, missing context, evidence requirements, and refusal", () => {
        render(<FindingRiskContextSection context={context} error={null} loading={false} onLoad={vi.fn()} />);
        expect(screen.getByText("Source: greenbone")).toBeInTheDocument();
        expect(screen.getByText("exposure: NOT_EVALUATED")).toBeInTheDocument();
        expect(screen.getByText("Evidence requirement: canonical_asset_context")).toBeInTheDocument();
        expect(screen.getByText(/refuses to calculate risk, priority, business impact/)).toBeInTheDocument();
        expect(screen.getByText(/Score, priority, business impact, decision, and recommendations are not available/)).toBeInTheDocument();
        expect(screen.getByText(/Priority unavailable/)).toHaveTextContent(
            "Band and score are not available",
        );
    });

    it("renders only a transported gated priority with evidence provenance", () => {
        const prioritized: FindingRiskContext = {
            ...context,
            priority: {
                status: "PRIORITIZED",
                band: "high",
                score: 80,
                reason: "Classified from the authoritative gated score.",
                considered_evidence_ids: ["correlation:finding-001:CVE-2004-2687"],
                referenced_input_references: ["finding:greenbone:finding-001"],
                missing_requirements: [],
                completeness_status: "available",
                source_type: "finding_risk_priority",
                source_reference: "finding-risk-priority:prioritized:finding-001",
            },
        };

        render(
            <FindingRiskContextSection
                context={prioritized}
                error={null}
                loading={false}
                onLoad={vi.fn()}
            />,
        );

        expect(screen.getByText("Priority: high; gated score: 80")).toBeInTheDocument();
        expect(screen.getByText(/Classified from the authoritative gated score/)).toHaveTextContent(
            "finding-risk-priority:prioritized:finding-001",
        );
        expect(screen.getByText("Evidence: correlation:finding-001:CVE-2004-2687")).toBeInTheDocument();
    });

    it("renders canonical asset, TI provenance, and canonical evidence metadata", () => {
        const resolved: FindingRiskContext = {
            ...context,
            asset_context: {
                status: "resolved",
                observed_identifier_type: "ip_address",
                observed_identifier_value: "172.18.0.19",
                canonical_asset_id: "asset-lab-metasploitable2-001",
                criticality: "LOW",
                source_reference: "product-owner:metasploitable2-lab-classification",
            },
            threat_intelligence: {
                finding_id: "finding-001",
                finding_source: "greenbone",
                finding_title: "Controlled finding",
                relationships: [{
                    applicability: "applicable",
                    cve_identifier: "CVE-2004-2687",
                    intelligence: {
                        contract_version: "1.0",
                        cve_identifier: "CVE-2004-2687",
                        nvd: fact("available", "nvd", "nvd:CVE-2004-2687"),
                        cvss: fact("available", "nvd", "nvd:CVE-2004-2687#cvss"),
                        epss: fact("available", "epss", "epss:CVE-2004-2687"),
                        cisa_kev: fact("available", "cisa_kev", "cisa-kev:CVE-2004-2687"),
                        exploitation_evidence: fact("not_evaluated", "cisa_kev", "cisa-kev:not-evaluated"),
                    },
                }],
            },
            evidence: [{
                identifier: "correlation:finding-001:CVE-2004-2687",
                kind: "derived",
                evidence_type: "correlation",
                contract_version: "1.0",
                source_type: "security_observation_correlation",
                source_reference: "security-observation-correlation:1.0:finding-001:CVE-2004-2687",
                input_references: ["finding:greenbone:finding-001", "asset-context:asset-lab-metasploitable2-001:product-owner"],
            }],
            risk_inputs: [
                { name: "business_criticality", state: "AUTHORITATIVE", value: "LOW", source: "product-owner" },
                { name: "exposure", state: "NOT_EVALUATED", value: null, source: null },
                { name: "detection_available", state: "NOT_EVALUATED", value: null, source: null },
                { name: "threat_intelligence_match", state: "NOT_EVALUATED", value: null, source: null },
                { name: "mitre_tactic", state: "NOT_EVALUATED", value: null, source: null },
            ],
        };

        render(
            <FindingRiskContextSection
                context={resolved}
                error={null}
                loading={false}
                onLoad={vi.fn()}
            />,
        );

        expect(screen.getByText(/Canonical asset asset-lab-metasploitable2-001/)).toHaveTextContent(
            "product-owner:metasploitable2-lab-classification",
        );
        expect(screen.getByText("CVE-2004-2687: applicable")).toBeInTheDocument();
        expect(screen.getByText("nvd: available. Source: nvd / nvd:CVE-2004-2687")).toBeInTheDocument();
        expect(screen.getByText(/Evidence correlation:finding-001:CVE-2004-2687/)).toHaveTextContent(
            "derived, correlation, v1.0",
        );
        expect(screen.getByText("Input: finding:greenbone:finding-001")).toBeInTheDocument();
        expect(resolved.risk_inputs.map((input) => input.name)).toEqual([
            "business_criticality",
            "exposure",
            "detection_available",
            "threat_intelligence_match",
            "mitre_tactic",
        ]);
    });
});

function fact(status: string, sourceType: string, sourceReference: string) {
    return {
        status,
        provenance: { source_type: sourceType, source_reference: sourceReference },
        observed_at: null,
        value: null,
    };
}
