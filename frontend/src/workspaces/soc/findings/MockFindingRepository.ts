import type { Finding } from "./Finding";
import type { FindingRepository } from "./FindingRepository";

const findings: readonly Finding[] = [
    {
        id: "finding-001",
        severity: "Critical",
        title: "Internet-facing vulnerability",
        description: "A critical exposure requires analyst review.",
        asset: "Production Application Gateway",
        riskScore: 98,
        status: "Open",
        inference: [
            {
                id: "inference-finding-001-public-exploit",
                entityId: "finding-001",
                type: "PUBLIC_EXPLOIT_AVAILABLE",
                strength: "Strong",
                title: "Public exploit context is applicable",
                description: "Known exploitation knowledge applies to the vulnerability on the internet-facing asset.",
                confidence: 97,
                supportingKnowledgeIds: ["knowledge-mitre-t1190", "knowledge-cve-2024-3400", "knowledge-kev-cve-2024-3400"],
                supportingBindingIds: ["binding-mitre-t1190-finding-001", "binding-cve-2024-3400-finding-001", "binding-kev-cve-2024-3400-finding-001"],
                supportingEvidenceIds: ["evidence-finding-001-cve", "evidence-finding-001-exposure"],
                supportingCorrelationIds: ["correlation-finding-001-threat-001", "correlation-finding-001-exposure-001"],
                result: {
                    summary: "Public exploitation context is relevant to the exposed vulnerability.",
                    confidence: 97,
                    findings: ["The vulnerability has known exploitation context.", "The affected asset is externally reachable."],
                },
            },
        ],
        decision: {
            id: "decision-finding-001",
            entityId: "finding-001",
            type: "ESCALATE",
            priority: "P1",
            state: "Proposed",
            confidence: 96,
            createdAt: "2026-08-03T11:00:00.000Z",
            outcome: {
                summary: "Escalate the critical finding to the SOC.",
                rationale:
                    "Multiple high-confidence reasoning steps confirm a critical vulnerability, external exposure and active threat context.",
                supportingReasoningIds: [
                    "reasoning-finding-001-step-1",
                    "reasoning-finding-001-step-2",
                    "reasoning-finding-001-step-4",
                    "reasoning-finding-001-step-5",
                ],
            },
        },
        reasoning: {
            id: "reasoning-finding-001",
            entityId: "finding-001",
            overallConfidence: 96,
            steps: [
                {
                    id: "reasoning-finding-001-step-1",
                    title: "Critical vulnerability detected",
                    description:
                        "Vulnerability evidence confirms a critical CVE on the affected gateway.",
                    evidenceIds: ["evidence-finding-001-cve"],
                    correlationIds: [],
                    confidence: 98,
                    order: 1,
                },
                {
                    id: "reasoning-finding-001-step-2",
                    title: "Internet exposure confirmed",
                    description:
                        "Exposure evidence confirms that the affected gateway is publicly reachable.",
                    evidenceIds: ["evidence-finding-001-exposure"],
                    correlationIds: [
                        "correlation-finding-001-exposure-001",
                    ],
                    confidence: 97,
                    order: 2,
                },
                {
                    id: "reasoning-finding-001-step-3",
                    title: "Critical asset relationship identified",
                    description:
                        "The finding is strongly related to a critical production asset.",
                    evidenceIds: [],
                    correlationIds: [
                        "correlation-finding-001-asset-001",
                    ],
                    confidence: 98,
                    order: 3,
                },
                {
                    id: "reasoning-finding-001-step-4",
                    title: "Active threat campaign correlated",
                    description:
                        "Threat intelligence links the vulnerability to active exploitation activity.",
                    evidenceIds: ["evidence-finding-001-cve"],
                    correlationIds: [
                        "correlation-finding-001-threat-001",
                    ],
                    confidence: 94,
                    order: 4,
                },
                {
                    id: "reasoning-finding-001-step-5",
                    title: "Multiple sources confirm exposure",
                    description:
                        "Evidence and related investigation context consistently confirm the exposure.",
                    evidenceIds: [
                        "evidence-finding-001-cve",
                        "evidence-finding-001-exposure",
                    ],
                    correlationIds: [
                        "correlation-finding-001-investigation-001",
                    ],
                    confidence: 96,
                    order: 5,
                },
            ],
            result: {
                summary:
                    "Critical vulnerability and external exposure are confirmed with high confidence.",
                confidence: 96,
                findings: [
                    "Critical CVE affects an internet-facing asset.",
                    "Active threat and investigation context are related.",
                ],
            },
        },
        correlations: [
            {
                id: "correlation-finding-001-asset-001",
                type: "RELATED_ASSET",
                targetType: "Asset",
                targetId: "asset-001",
                title: "Affected production gateway",
                description:
                    "The finding affects the production application gateway.",
                strength: "Strong",
                confidence: 98,
            },
            {
                id: "correlation-finding-001-threat-001",
                type: "RELATED_THREAT",
                targetType: "ThreatIntelligence",
                targetId: "threat-001",
                title: "Related exploitation campaign",
                description:
                    "The vulnerability is associated with an active exploitation campaign.",
                strength: "Strong",
                confidence: 94,
            },
            {
                id: "correlation-finding-001-investigation-001",
                type: "RELATED_INVESTIGATION",
                targetType: "Investigation",
                targetId: "investigation-001",
                title: "Active SOC investigation",
                description:
                    "The finding is included in the critical exposure investigation.",
                strength: "Strong",
                confidence: 100,
            },
            {
                id: "correlation-finding-001-exposure-001",
                type: "RELATED_EXPOSURE",
                targetType: "Exposure",
                targetId: "exposure-001",
                title: "Related external exposure",
                description:
                    "The affected asset is part of the external application exposure.",
                strength: "Strong",
                confidence: 97,
            },
        ],
        evidence: [
            {
                id: "evidence-finding-001-cve",
                type: "CVE",
                source: "Vulnerability Scanner",
                title: "Critical vulnerability detected",
                description:
                    "A critical CVE affects the production application gateway.",
                confidence: 98,
                timestamp: "2026-08-03T08:00:00.000Z",
                weight: 1,
            },
            {
                id: "evidence-finding-001-exposure",
                type: "Internet Facing",
                source: "Exposure Management",
                title: "Asset is externally reachable",
                description:
                    "The affected gateway is reachable from the public internet.",
                confidence: 96,
                timestamp: "2026-08-03T08:05:00.000Z",
                weight: 0.95,
            },
        ],
        confidence: {
            score: 96,
            evidenceCount: 3,
            dataQuality: 95,
            reason: "Correlated evidence supports this finding.",
        },
        recommendation: {
            id: "recommendation-finding-001",
            entityId: "finding-001",
            decisionId: "decision-finding-001",
            type: "PATCH",
            priority: "P1",
            title: "Review remediation priority",
            description:
                "Review the affected asset and validate remediation priority.",
            estimatedEffort: "Medium",
            businessImpact: "Protects critical digital services.",
            expectedRiskReduction: 85,
            action: {
                summary: "Review affected systems immediately.",
                rationale:
                    "The escalation decision is supported by critical vulnerability and exposure evidence.",
                expectedOutcome:
                    "The vulnerable external surface is reduced.",
            },
        },
        explainability: {
            reason:
                "Severity, asset criticality and external exposure contributed to this finding.",
            confidence: {
                score: 96,
                evidenceCount: 3,
                dataQuality: 95,
                reason: "Correlated evidence supports this finding.",
            },
            businessImpact: "Critical digital services may be affected.",
            mitre: ["T1190"],
            kev: true,
            epss: 0.96,
            attackPath: ["Internet", "Application Gateway"],
        },
    },
    {
        id: "finding-002",
        severity: "High",
        title: "Elevated identity risk",
        description: "An elevated identity exposure is under review.",
        asset: "Identity Management Service",
        riskScore: 84,
        status: "In Review",
        decision: {
            id: "decision-finding-002",
            entityId: "finding-002",
            type: "INVESTIGATE",
            priority: "P2",
            state: "Proposed",
            confidence: 89,
            createdAt: "2026-08-03T11:05:00.000Z",
            outcome: {
                summary: "Continue investigation of the identity exposure.",
                rationale:
                    "Identity evidence, critical service context and an active investigation relationship support further investigation.",
                supportingReasoningIds: [
                    "reasoning-finding-002-step-1",
                    "reasoning-finding-002-step-2",
                    "reasoning-finding-002-step-3",
                ],
            },
        },
        reasoning: {
            id: "reasoning-finding-002",
            entityId: "finding-002",
            overallConfidence: 89,
            steps: [
                {
                    id: "reasoning-finding-002-step-1",
                    title: "Privileged identity exposure detected",
                    description:
                        "Identity evidence confirms elevated privileged access risk.",
                    evidenceIds: ["evidence-finding-002-identity"],
                    correlationIds: [],
                    confidence: 93,
                    order: 1,
                },
                {
                    id: "reasoning-finding-002-step-2",
                    title: "Business-critical context verified",
                    description:
                        "Asset evidence confirms that the identity service supports critical operations.",
                    evidenceIds: ["evidence-finding-002-asset"],
                    correlationIds: [
                        "correlation-finding-002-asset-001",
                    ],
                    confidence: 90,
                    order: 2,
                },
                {
                    id: "reasoning-finding-002-step-3",
                    title: "Investigation context correlated",
                    description:
                        "The affected identity context is linked to an active investigation.",
                    evidenceIds: ["evidence-finding-002-identity"],
                    correlationIds: [
                        "correlation-finding-002-investigation-001",
                    ],
                    confidence: 86,
                    order: 3,
                },
            ],
            result: {
                summary:
                    "Privileged identity exposure is supported by asset and investigation context.",
                confidence: 89,
                findings: [
                    "Privileged access risk is present.",
                    "The affected identity service supports critical operations.",
                ],
            },
        },
        correlations: [
            {
                id: "correlation-finding-002-asset-001",
                type: "SHARED_BUSINESS_SERVICE",
                targetType: "Asset",
                targetId: "asset-001",
                title: "Shared critical service",
                description:
                    "The identity service and gateway support the same digital service.",
                strength: "Medium",
                confidence: 82,
            },
            {
                id: "correlation-finding-002-investigation-001",
                type: "SAME_IDENTITY",
                targetType: "Investigation",
                targetId: "investigation-001",
                title: "Identity context under investigation",
                description:
                    "The investigation includes the affected privileged identity context.",
                strength: "Medium",
                confidence: 86,
            },
        ],
        evidence: [
            {
                id: "evidence-finding-002-identity",
                type: "Identity Signal",
                source: "Identity Provider",
                title: "Privileged identity exposure detected",
                description:
                    "A privileged identity is associated with elevated access risk.",
                confidence: 93,
                timestamp: "2026-08-03T09:00:00.000Z",
                weight: 0.9,
            },
            {
                id: "evidence-finding-002-asset",
                type: "Asset Criticality",
                source: "Asset Inventory",
                title: "Identity service supports critical operations",
                description:
                    "The affected identity service is classified as business critical.",
                confidence: 90,
                timestamp: "2026-08-03T09:05:00.000Z",
                weight: 0.85,
            },
        ],
        confidence: {
            score: 91,
            evidenceCount: 2,
            dataQuality: 90,
            reason: "Identity and access signals support this finding.",
        },
        recommendation: {
            id: "recommendation-finding-002",
            entityId: "finding-002",
            decisionId: "decision-finding-002",
            type: "INVESTIGATE",
            priority: "P2",
            title: "Validate privileged access",
            description:
                "Validate privileged access and review the affected identity controls.",
            estimatedEffort: "Low",
            businessImpact: "Reduces privileged identity exposure.",
            expectedRiskReduction: 60,
            action: {
                summary: "Review the privileged identity context.",
                rationale:
                    "The investigation decision is supported by identity and asset evidence.",
                expectedOutcome:
                    "The scope and impact of privileged access exposure are clarified.",
            },
        },
        explainability: {
            reason:
                "Identity exposure and privileged access signals contributed to this finding.",
            confidence: {
                score: 91,
                evidenceCount: 2,
                dataQuality: 90,
                reason: "Identity and access signals support this finding.",
            },
            businessImpact: "Privileged access may be exposed.",
            mitre: ["T1078"],
            kev: null,
            epss: null,
            attackPath: ["Identity", "Privileged Access"],
        },
    },
];

class MockFindingRepository implements FindingRepository {
    getFindings(): readonly Finding[] {
        return findings;
    }
}

export const findingRepository: FindingRepository =
    new MockFindingRepository();
