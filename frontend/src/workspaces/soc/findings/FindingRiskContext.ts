export type RiskInputState = "AUTHORITATIVE" | "UNKNOWN" | "NOT_EVALUATED";

export interface FindingRiskInput {
    name: string;
    state: RiskInputState;
    value: string | boolean | null;
    source: string | null;
}

export interface FindingRiskContext {
    finding_id: string;
    source_facts: readonly {
        name: string;
        value: string;
        source_reference: string;
    }[];
    asset_context: {
        status: "resolved" | "not_found" | "missing_identifier";
        observed_identifier_type: string | null;
        observed_identifier_value: string | null;
        canonical_asset_id: string | null;
        criticality: string | null;
        source_reference: string | null;
    };
    threat_intelligence: FindingThreatIntelligenceEnrichment;
    correlation: {
        completeness_status: string;
        source_type: string;
        source_reference: string;
    };
    evidence: readonly {
        identifier: string;
        kind: string;
        evidence_type: string;
        contract_version: string;
        source_type: string;
        source_reference: string;
        input_references: readonly string[];
    }[];
    risk_inputs: readonly FindingRiskInput[];
    assessment: {
        status: "ASSESSED" | "INSUFFICIENT_CONTEXT";
        available_inputs: readonly FindingRiskInput[];
        missing_inputs: readonly FindingRiskInput[];
        score: number | null;
    };
    evidence_readiness: {
        status: "READY" | "INSUFFICIENT_EVIDENCE";
        reason: string;
        considered_evidence_ids: readonly string[];
        referenced_input_references: readonly string[];
        missing_requirements: readonly string[];
        completeness_status: string;
        source_type: string;
        source_reference: string;
    };
    refusal_reason: string | null;
    priority: {
        status: "PRIORITIZED" | "UNAVAILABLE";
        band: "critical" | "high" | "medium" | "low" | "informational" | null;
        score: number | null;
        reason: string;
        considered_evidence_ids: readonly string[];
        referenced_input_references: readonly string[];
        missing_requirements: readonly string[];
        completeness_status: string;
        source_type: string;
        source_reference: string;
    } | null;
    business_context?: {
        status: "RESOLVED" | "NOT_FOUND" | "MISSING_CANONICAL_ASSET";
        canonical_asset_id: string | null;
        business_service: string | null;
        environment: "PRODUCTION" | "PRE_PRODUCTION" | "DEVELOPMENT" | "TEST" | null;
        service_criticality: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | null;
        source_reference: string | null;
        facts: readonly { name: string; value: string; source_reference: string }[];
    };
    business_impact_readiness?: {
        finding_id: string;
        status: "READY" | "UNAVAILABLE";
        reason: string;
        facts: readonly { name: string; value: string; source_reference: string }[];
        missing_requirements: readonly string[];
        source_references: readonly string[];
        completeness_status: string;
        source_type: string;
        source_reference: string;
    };
    service_impact_profile?: {
        status: "RESOLVED" | "NOT_FOUND" | "MISSING_CANONICAL_ASSET";
        canonical_asset_id: string | null;
        business_service: string | null;
        confidentiality_importance: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | null;
        integrity_importance: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | null;
        availability_importance: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | null;
        source_reference: string | null;
    };
    technical_effect?: {
        finding_id: string;
        status: "AVAILABLE" | "UNAVAILABLE";
        effects: readonly TechnicalEffect[];
        missing_requirements: readonly string[];
        completeness_status: string;
        source_type: "finding_technical_effect";
        source_reference: string;
    };
    business_impact_classification_readiness?: {
        finding_id: string;
        status: "READY" | "UNAVAILABLE";
        reason: string;
        business_facts: readonly { name: string; value: string; source_reference: string }[];
        service_impact_facts: readonly { name: string; value: string; source_reference: string }[];
        technical_effects: readonly TechnicalEffect[];
        missing_requirements: readonly string[];
        source_references: readonly string[];
        completeness_status: string;
        source_type: "business_impact_classification_readiness";
        source_reference: string;
    };
    business_impact: null;
    decision: null;
    recommendations: readonly never[];
}

export interface TechnicalEffect {
    finding_id: string;
    cve_identifier: string;
    cvss_version: "3.0" | "3.1";
    cvss_vector: string;
    confidentiality: "NONE" | "LOW" | "HIGH";
    integrity: "NONE" | "LOW" | "HIGH";
    availability: "NONE" | "LOW" | "HIGH";
    source_type: "nvd";
    source_reference: string;
    observed_at: string;
}
import type { FindingThreatIntelligenceEnrichment } from "@/workspaces/threat-intelligence/ThreatIntelligence";
