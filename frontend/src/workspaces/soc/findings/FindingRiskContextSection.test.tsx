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
        facts: [], missing_requirements: ["business_service", "environment", "service_criticality", "business_context_provenance"], source_references: [],
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
        missing_requirements: ["service_impact_profile", "supported_cvss_v3_effect:CVE-2004-2687"], source_references: [],
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
        const missingBusinessService = screen.getByText("Business service");
        expect(missingBusinessService).toHaveAttribute("data-color-token", "text.primary");
        expect(missingBusinessService.closest(".MuiChip-root")).toBeNull();
        expect(screen.queryByText("business_service")).not.toBeInTheDocument();
        expect(screen.queryByText("environment")).not.toBeInTheDocument();
        expect(screen.queryByText("service_criticality")).not.toBeInTheDocument();
        expect(screen.queryByText("business_context_provenance")).not.toBeInTheDocument();
        expect(screen.queryByText("service_impact_profile")).not.toBeInTheDocument();
        expect(screen.queryByText("supported_cvss_v3_effect:CVE-2004-2687")).not.toBeInTheDocument();
        expect(screen.getByText("Environment")).toBeInTheDocument();
        expect(screen.getByText("Service criticality")).toBeInTheDocument();
        expect(screen.getByText("Business context provenance")).toBeInTheDocument();
        expect(screen.getByText("Service impact profile")).toBeInTheDocument();
        expect(screen.getByText("Supported CVSS v3 effect — CVE-2004-2687")).toBeInTheDocument();
        expect(screen.queryByText("Supported cvss v3 effect — CVE-2004-2687")).not.toBeInTheDocument();
        expect(context.business_impact_classification_readiness?.missing_requirements).toContain("supported_cvss_v3_effect:CVE-2004-2687");
        expect(context.business_impact_readiness?.missing_requirements).toContain("business_service");
        expect(screen.getByLabelText("Authoritative Business Context").querySelector('[data-color-token="warning.main"]')).not.toBeNull();
        expect(within(screen.getByLabelText("Service Impact Profile")).getByText("NOT_FOUND")).toBeInTheDocument();
        expect(within(screen.getByLabelText("Technical Effect")).getByText("UNAVAILABLE")).toBeInTheDocument();
        expect(screen.getByText(/Readiness is not a Business Impact result/)).toBeInTheDocument();
        expect(container.querySelector("br")).toBeNull();
    });

    it("uses traffic-light authority semantics without coloring neutral values", () => {
        const semanticContext: FindingRiskContext = {
            ...context,
            business_context: {
                status: "RESOLVED",
                canonical_asset_id: "asset-1",
                business_service: "Payments",
                environment: "PRODUCTION",
                service_criticality: "CRITICAL",
                source_reference: "cmdb:1",
                facts: [],
            },
            business_impact_readiness: {
                ...context.business_impact_readiness!,
                status: "READY",
                reason: "Authoritative facts are available.",
                missing_requirements: [],
                completeness_status: "available",
            },
            service_impact_profile: {
                status: "RESOLVED",
                canonical_asset_id: "asset-1",
                business_service: "Payments",
                confidentiality_importance: "HIGH",
                integrity_importance: "CRITICAL",
                availability_importance: "HIGH",
                source_reference: "service-profile:1",
            },
            threat_intelligence: {
                ...context.threat_intelligence,
                relationships: [{
                    applicability: "applicable",
                    cve_identifier: "CVE-2004-2687",
                    intelligence: {
                        contract_version: "1.0",
                        cve_identifier: "CVE-2004-2687",
                        nvd: fact("AVAILABLE", "nvd", "nvd:CVE-2004-2687"),
                        cvss: fact("UNKNOWN", "nvd", "nvd:CVE-2004-2687#cvss"),
                        epss: fact("NOT_EVALUATED", "epss", "epss:CVE-2004-2687"),
                        cisa_kev: fact("available", "cisa_kev", "cisa-kev:CVE-2004-2687"),
                        exploitation_evidence: fact("not_evaluated", "nvd", "nvd:CVE-2004-2687#exploitation"),
                    },
                }],
            },
        };

        render(<FindingRiskContextSection context={semanticContext} error={null} loading={false} onLoad={vi.fn()} />);

        const sourceField = screen.getAllByText("Source")[0].closest("[data-authority-field]");
        expect(within(sourceField as HTMLElement).getByText("Source")).toHaveAttribute("data-color-token", "success.main");
        expect(within(sourceField as HTMLElement).getByText("Source")).toHaveAttribute("data-structural-label", "true");
        expect(within(sourceField as HTMLElement).getByText("Source")).toHaveStyle({ textTransform: "uppercase", fontWeight: "700" });
        expect(within(sourceField as HTMLElement).getByText("Source")).toHaveTextContent("Source");
        expect(within(sourceField as HTMLElement).getByText("greenbone")).toHaveAttribute("data-color-token", "text.secondary");
        expect(sourceField).toHaveAttribute("data-layout-spacing", "compact");
        expect(sourceField?.parentElement).toHaveAttribute("data-layout-spacing", "units");
        expectStatusChip(within(screen.getByLabelText("Business-Impact Readiness")).getByText("READY"), "success");
        expectStatusChip(within(screen.getByLabelText("Service Impact Profile")).getByText("RESOLVED"), "success");
        expectStatusChip(within(screen.getByLabelText("Technical Effect")).getByText("UNAVAILABLE"), "warning");
        expectStatusChip(screen.getByText("AVAILABLE"), "success");
        expectStatusChip(screen.getByText("UNKNOWN"), "warning");
        expectStatusChip(screen.getAllByText("NOT_EVALUATED")[0], "warning");
        expect(screen.getByLabelText("What PredatorAI knows").querySelector('[data-color-token="success.main"]')).not.toBeNull();
        expect(screen.getByLabelText("Business-Impact Readiness").querySelector(':scope > [data-color-token="success.main"]')).not.toBeNull();
        expect(screen.getByLabelText("Technical Effect").querySelector(':scope > [data-color-token="warning.main"]')).not.toBeNull();
        const availableTi = screen.getByLabelText("Nvd");
        const unavailableTi = screen.getByLabelText("Cvss");
        expect(availableTi).toHaveAttribute("data-authority-tone", "success");
        expect(unavailableTi).toHaveAttribute("data-authority-tone", "warning");
        expect(within(availableTi).getByText("Authority")).toHaveAttribute("data-color-token", "success.main");
        expect(within(unavailableTi).getByText("Authority")).toHaveAttribute("data-color-token", "warning.main");
        expect(within(availableTi).getByText("nvd")).toHaveAttribute("data-color-token", "text.primary");
        expect(within(unavailableTi).getByText("nvd:CVE-2004-2687#cvss")).toHaveAttribute("data-color-token", "text.secondary");
        screen.getAllByText("HIGH").forEach((value) => {
            expect(value).toHaveAttribute("data-color-token", "text.primary");
            expect(value.closest(".MuiChip-root")).toBeNull();
        });
        expect(screen.getByText("service-profile:1")).toHaveAttribute("data-color-token", "text.secondary");
        expect(screen.getByLabelText("Nvd")).toHaveAttribute("data-layout-spacing", "units");
        expect(semanticContext.business_impact).toBeNull();
        expect(semanticContext.decision).toBeNull();
        expect(semanticContext.recommendations).toEqual([]);
    });

    it("retains existing error semantics without using color as the error text", () => {
        render(<FindingRiskContextSection context={null} error="Controlled source failure." loading={false} onLoad={vi.fn()} />);
        const error = screen.getByRole("alert");
        expect(error).toHaveClass("MuiAlert-colorError");
        expect(error).toHaveTextContent("Controlled source failure.");
    });

    it("separates repeated Technical Effect records without mixing their authority", () => {
        const multiEffectContext: FindingRiskContext = {
            ...context,
            technical_effect: {
                finding_id: "finding-001",
                status: "AVAILABLE",
                effects: [
                    {
                        finding_id: "finding-001",
                        cve_identifier: "CVE-2004-2687",
                        cvss_version: "3.1",
                        cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N",
                        confidentiality: "HIGH",
                        integrity: "LOW",
                        availability: "NONE",
                        source_type: "nvd",
                        source_reference: "nvd:CVE-2004-2687#cvss-v3.1-authoritative-reference",
                        observed_at: "2026-09-01T08:00:00Z",
                    },
                    {
                        finding_id: "finding-001",
                        cve_identifier: "CVE-2021-44228",
                        cvss_version: "3.0",
                        cvss_vector: "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:L",
                        confidentiality: "NONE",
                        integrity: "HIGH",
                        availability: "LOW",
                        source_type: "nvd",
                        source_reference: "nvd:CVE-2021-44228#cvss-v3.0-authoritative-reference",
                        observed_at: "2026-09-01T08:05:00Z",
                    },
                ],
                missing_requirements: [],
                completeness_status: "available",
                source_type: "finding_technical_effect",
                source_reference: "finding-technical-effect:available:finding-001",
            },
        };

        render(<FindingRiskContextSection context={multiEffectContext} error={null} loading={false} onLoad={vi.fn()} />);

        const technicalEffect = screen.getByLabelText("Technical Effect");
        expectStatusChip(within(technicalEffect).getByText("AVAILABLE"), "success");
        const records = within(technicalEffect).getByLabelText("Technical effect records");
        expect(records).toHaveAttribute("data-layout-spacing", "records");
        expect(within(records).queryByText("This technical projection is not Business Impact.")).not.toBeInTheDocument();

        const first = within(records).getByLabelText("Technical effect CVE-2004-2687");
        const second = within(records).getByLabelText("Technical effect CVE-2021-44228");
        expect(first).toHaveAttribute("data-layout-spacing", "units");
        expect(second).toHaveAttribute("data-layout-spacing", "units");
        expect(first.querySelector('[data-layout-spacing="compact"]')).not.toBeNull();
        expect(second.querySelector('[data-layout-spacing="compact"]')).not.toBeNull();

        expect(within(first).getByText("CVE-2004-2687")).toBeInTheDocument();
        expect(within(first).getByText("CVE-2004-2687")).toHaveAttribute("data-color-token", "text.primary");
        expect(within(first).getByText("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N")).toBeInTheDocument();
        expect(within(first).getByText("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N")).toHaveAttribute("data-color-token", "text.primary");
        expect(within(first).getByText("nvd:CVE-2004-2687#cvss-v3.1-authoritative-reference")).toHaveStyle({ overflowWrap: "anywhere" });
        expect(within(first).getByText("2026-09-01T08:00:00Z")).toBeInTheDocument();
        expect(within(first).queryByText("CVE-2021-44228")).not.toBeInTheDocument();
        expect(within(first).queryByText("nvd:CVE-2021-44228#cvss-v3.0-authoritative-reference")).not.toBeInTheDocument();

        expect(within(second).getByText("CVE-2021-44228")).toBeInTheDocument();
        expect(within(second).getByText("CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:L")).toBeInTheDocument();
        expect(within(second).getByText("nvd:CVE-2021-44228#cvss-v3.0-authoritative-reference")).toHaveStyle({ overflowWrap: "anywhere" });
        expect(within(second).getByText("2026-09-01T08:05:00Z")).toBeInTheDocument();
        expect(within(second).queryByText("CVE-2004-2687")).not.toBeInTheDocument();
        expect(within(second).queryByText("nvd:CVE-2004-2687#cvss-v3.1-authoritative-reference")).not.toBeInTheDocument();

        [...within(first).getAllByText(/^(HIGH|LOW|NONE)$/), ...within(second).getAllByText(/^(HIGH|LOW|NONE)$/)].forEach((value) => {
            expect(value).toHaveAttribute("data-color-token", "text.primary");
            expect(value.closest(".MuiChip-root")).toBeNull();
        });
        expect(multiEffectContext.business_impact).toBeNull();
        expect(multiEffectContext.decision).toBeNull();
        expect(multiEffectContext.recommendations).toEqual([]);
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
        const correlationEvidence = screen.getByLabelText("Correlation / Evidence");
        const parentHeading = within(correlationEvidence).getByText("Correlation / Evidence");
        expect(parentHeading).not.toHaveAttribute("data-color-token", "success.main");
        expect(parentHeading).not.toHaveAttribute("data-color-token", "warning.main");
        const correlation = within(correlationEvidence).getByLabelText("Correlation");
        expect(within(correlation).getByText("Correlation")).toHaveAttribute("data-color-token", "warning.main");
        expect(within(evidence).getByText("Evidence")).toHaveAttribute("data-color-token", "success.main");
        expect(within(correlation).queryByText("correlation:finding-001:CVE-2004-2687")).not.toBeInTheDocument();
        expect(within(evidence).queryByText("canonical-asset-context-unresolved")).not.toBeInTheDocument();
        const inputs = within(evidence).getByLabelText("Inputs");
        expect(inputs).toHaveAttribute("data-layout-spacing", "group");
        expect(inputs.querySelector('[data-layout-spacing="records"]')).not.toBeNull();
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

function expectStatusChip(text: HTMLElement, semantic: "success" | "warning") {
    const chip = text.closest(".MuiChip-root");
    expect(chip).not.toBeNull();
    expect(chip).toHaveClass("MuiChip-sizeSmall", "MuiChip-outlined", `MuiChip-color${semantic === "success" ? "Success" : "Warning"}`);
    expect(chip).toHaveAttribute("data-status-semantic", semantic);
    expect(chip).toHaveAttribute("data-color-token", `${semantic}.main`);
    expect(chip).toHaveTextContent(text.textContent ?? "");
}
