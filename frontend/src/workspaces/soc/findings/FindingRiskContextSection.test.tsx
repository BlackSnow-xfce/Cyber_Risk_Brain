import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { FindingRiskContext } from "./FindingRiskContext";
import FindingRiskContextSection from "./FindingRiskContextSection";

afterEach(cleanup);

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
    business_context: {
        status: "NOT_FOUND", canonical_asset_id: null, business_service: null,
        environment: null, service_criticality: null, source_reference: null, facts: [],
    },
    business_impact_readiness: {
        finding_id: "finding-001", status: "UNAVAILABLE", reason: "Authoritative business context is missing.",
        facts: [], missing_requirements: ["business_service"], source_references: [],
        completeness_status: "no_data", source_type: "business_impact_readiness",
        source_reference: "business-impact-readiness:unavailable:finding-001",
    },
    service_impact_profile: {
        status: "NOT_FOUND", canonical_asset_id: null, business_service: null,
        confidentiality_importance: null, integrity_importance: null,
        availability_importance: null, source_reference: null,
    },
    technical_effect: {
        finding_id: "finding-001", status: "UNAVAILABLE", effects: [],
        missing_requirements: ["applicable_technical_effect"], completeness_status: "no_data",
        source_type: "finding_technical_effect",
        source_reference: "finding-technical-effect:unavailable:finding-001",
    },
    business_impact_classification_readiness: {
        finding_id: "finding-001", status: "UNAVAILABLE", reason: "Service profile is missing.",
        business_facts: [], service_impact_facts: [], technical_effects: [],
        missing_requirements: ["service_impact_profile"], source_references: [],
        completeness_status: "no_data", source_type: "business_impact_classification_readiness",
        source_reference: "business-impact-classification-readiness:unavailable:finding-001",
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
        const { container } = render(<FindingRiskContextSection context={context} error={null} loading={false} onLoad={vi.fn()} />);
        const sourceValue = screen.getByText("greenbone");
        expect(sourceValue.closest("[data-authority-field]")).toHaveAttribute("data-authority-field", "Source");
        expect(sourceValue).toHaveStyle({ overflowWrap: "anywhere" });
        expect(screen.queryByText("Source: greenbone")).not.toBeInTheDocument();
        expect(screen.getByText("Exposure")).toBeInTheDocument();
        expect(screen.getByText("Canonical asset context")).toBeInTheDocument();
        expect(screen.getByText(/refuses to calculate risk, priority, business impact/)).toBeInTheDocument();
        expect(screen.getByText(/Score, priority, business impact, decision, and recommendations are not available/)).toBeInTheDocument();
        expect(within(screen.getByLabelText("Authoritative Business Context")).getByText("NOT_FOUND")).toBeInTheDocument();
        expect(screen.getByText("Business service")).toBeInTheDocument();
        expect(within(screen.getByLabelText("Service Impact Profile")).getByText("NOT_FOUND")).toBeInTheDocument();
        expect(within(screen.getByLabelText("Technical Effect")).getByText("UNAVAILABLE")).toBeInTheDocument();
        expect(screen.getByText(/Readiness is not a Business Impact result/)).toBeInTheDocument();
        expect(container.querySelector("br")).toBeNull();
    });

    it("renders resolved business facts with provenance without inferring impact", () => {
        render(<FindingRiskContextSection context={{
            ...context,
            business_context: {
                status: "RESOLVED", canonical_asset_id: "asset-1",
                business_service: "Payments", environment: "PRODUCTION",
                service_criticality: "CRITICAL", source_reference: "cmdb:1",
                facts: [
                    { name: "canonical_asset_id", value: "asset-1", source_reference: "cmdb:1" },
                    { name: "business_service", value: "Payments", source_reference: "cmdb:1" },
                    { name: "environment", value: "PRODUCTION", source_reference: "cmdb:1" },
                    { name: "service_criticality", value: "CRITICAL", source_reference: "cmdb:1" },
                ],
            },
            business_impact_readiness: {
                finding_id: "finding-001", status: "READY", reason: "Authoritative facts are available.",
                facts: [
                    { name: "canonical_asset_id", value: "asset-1", source_reference: "cmdb:1" },
                    { name: "business_service", value: "Payments", source_reference: "cmdb:1" },
                    { name: "environment", value: "PRODUCTION", source_reference: "cmdb:1" },
                    { name: "service_criticality", value: "CRITICAL", source_reference: "cmdb:1" },
                ],
                missing_requirements: [], source_references: ["cmdb:1"],
                completeness_status: "available", source_type: "business_impact_readiness",
                source_reference: "business-impact-readiness:ready:finding-001",
            },
        }} error={null} loading={false} onLoad={vi.fn()} />);
        const business = screen.getByLabelText("Authoritative Business Context");
        expect(within(business).getByText("Business service")).toBeInTheDocument();
        expect(within(business).getByText("Payments")).toBeInTheDocument();
        expect(within(business).getAllByText("cmdb:1")).toHaveLength(4);
        expect(screen.queryByText("business_service: Payments. Source: cmdb:1")).not.toBeInTheDocument();
        const readiness = screen.getByLabelText("Business-Impact Readiness");
        expect(within(readiness).getByText("READY")).toBeInTheDocument();
        expect(within(readiness).getByText("business-impact-readiness:ready:finding-001")).toBeInTheDocument();
        expect(screen.getAllByText(/does not calculate Business Impact/).length).toBeGreaterThan(0);
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

        const priority = screen.getByLabelText("Finding Risk Priority");
        expect(within(priority).getByText("Priority band")).toBeInTheDocument();
        expect(within(priority).getByText("high")).toBeInTheDocument();
        expect(within(priority).getByText("Gated score")).toBeInTheDocument();
        expect(within(priority).getByText("80")).toBeInTheDocument();
        expect(within(priority).getByText("Classified from the authoritative gated score.")).toBeInTheDocument();
        expect(within(priority).getByText("finding-risk-priority:prioritized:finding-001")).toBeInTheDocument();
        expect(within(priority).getByText("correlation:finding-001:CVE-2004-2687")).toBeInTheDocument();
        expect(screen.queryByText("Priority: high; gated score: 80")).not.toBeInTheDocument();
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

        const { container } = render(
            <FindingRiskContextSection
                context={resolved}
                error={null}
                loading={false}
                onLoad={vi.fn()}
            />,
        );

        const asset = screen.getByLabelText("Canonical asset context");
        expect(within(asset).getByText("asset-lab-metasploitable2-001")).toBeInTheDocument();
        expect(within(asset).getByText("product-owner:metasploitable2-lab-classification")).toHaveStyle({ overflowWrap: "anywhere" });
        const threatIntelligence = screen.getByLabelText("Threat Intelligence");
        expect(within(threatIntelligence).getByText("CVE-2004-2687")).toBeInTheDocument();
        expect(within(threatIntelligence).getByText("applicable")).toBeInTheDocument();
        expect(within(threatIntelligence).getAllByText("nvd:CVE-2004-2687").length).toBeGreaterThan(0);
        const evidence = screen.getByLabelText("Evidence");
        expect(within(evidence).getByText("correlation:finding-001:CVE-2004-2687")).toBeInTheDocument();
        expect(within(evidence).getByText("derived")).toBeInTheDocument();
        const inputs = within(evidence).getByLabelText("Inputs");
        expect(within(inputs).getByText("Finding")).toBeInTheDocument();
        expect(within(inputs).getByText("finding:greenbone:finding-001")).toBeInTheDocument();
        expect(within(inputs).getByText("Asset context")).toBeInTheDocument();
        expect(within(inputs).getByText("asset-context:asset-lab-metasploitable2-001:product-owner")).toBeInTheDocument();
        expect(screen.queryByText("Input: finding:greenbone:finding-001")).not.toBeInTheDocument();
        expect(container.querySelector("br")).toBeNull();
        const orderedSections = [
            "What PredatorAI knows",
            "Authoritative Business Context",
            "Business-Impact Readiness",
            "Service Impact Profile",
            "Technical Effect",
            "Business-Impact Classification Readiness",
            "Threat Intelligence",
            "Correlation / Evidence",
            "Information still missing",
            "Finding Risk Priority",
        ].map((label) => screen.getByLabelText(label));
        orderedSections.slice(1).forEach((section, index) => {
            expect(orderedSections[index].compareDocumentPosition(section) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        });
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
