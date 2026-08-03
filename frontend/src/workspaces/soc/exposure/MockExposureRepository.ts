import type { Exposure } from "./Exposure";
import type { ExposureRepository } from "./ExposureRepository";

const exposures: readonly Exposure[] = [
    {
        id: "exposure-001",
        title: "External application exposure",
        description: "An external exposure requires analyst review.",
        type: "Internet Exposure",
        severity: "Critical",
        internetFacing: "Yes",
        riskScore: 98,
        status: "Open",
        decision: {
            id: "decision-exposure-001",
            entityId: "exposure-001",
            type: "ESCALATE",
            priority: "P1",
            state: "Proposed",
            confidence: 97,
            createdAt: "2026-08-03T11:25:00.000Z",
            outcome: {
                summary: "Escalate the confirmed external exposure.",
                rationale:
                    "Internet reachability, exploit probability and strong relationships to a critical asset and finding establish elevated exposure.",
                supportingReasoningIds: [
                    "reasoning-exposure-001-step-1",
                    "reasoning-exposure-001-step-2",
                    "reasoning-exposure-001-step-3",
                    "reasoning-exposure-001-step-4",
                ],
            },
        },
        reasoning: {
            id: "reasoning-exposure-001",
            entityId: "exposure-001",
            overallConfidence: 97,
            steps: [
                {
                    id: "reasoning-exposure-001-step-1",
                    title: "Internet exposure confirmed",
                    description:
                        "Exposure evidence confirms a publicly reachable application surface.",
                    evidenceIds: ["evidence-exposure-001-facing"],
                    correlationIds: [],
                    confidence: 98,
                    order: 1,
                },
                {
                    id: "reasoning-exposure-001-step-2",
                    title: "Exploit probability identified",
                    description:
                        "EPSS evidence confirms an elevated exploitation probability.",
                    evidenceIds: ["evidence-exposure-001-epss"],
                    correlationIds: [],
                    confidence: 95,
                    order: 2,
                },
                {
                    id: "reasoning-exposure-001-step-3",
                    title: "Related business asset confirmed",
                    description:
                        "The external surface is strongly linked to the production application gateway.",
                    evidenceIds: ["evidence-exposure-001-facing"],
                    correlationIds: [
                        "correlation-exposure-001-asset-001",
                    ],
                    confidence: 98,
                    order: 3,
                },
                {
                    id: "reasoning-exposure-001-step-4",
                    title: "Related finding confirms exposure",
                    description:
                        "A critical finding affects the same external application surface.",
                    evidenceIds: [
                        "evidence-exposure-001-facing",
                        "evidence-exposure-001-epss",
                    ],
                    correlationIds: [
                        "correlation-exposure-001-finding-001",
                    ],
                    confidence: 97,
                    order: 4,
                },
            ],
            result: {
                summary:
                    "External exposure and exploitation context are confirmed with strong entity relationships.",
                confidence: 97,
                findings: [
                    "The application surface is internet facing.",
                    "A related business asset and critical finding are confirmed.",
                ],
            },
        },
        correlations: [
            {
                id: "correlation-exposure-001-finding-001",
                type: "RELATED_FINDING",
                targetType: "Finding",
                targetId: "finding-001",
                title: "Finding on exposed surface",
                description:
                    "The critical finding affects the external application surface.",
                strength: "Strong",
                confidence: 97,
            },
            {
                id: "correlation-exposure-001-asset-001",
                type: "RELATED_ASSET",
                targetType: "Asset",
                targetId: "asset-001",
                title: "Externally exposed asset",
                description:
                    "The production application gateway is part of this exposure.",
                strength: "Strong",
                confidence: 98,
            },
        ],
        evidence: [
            {
                id: "evidence-exposure-001-facing",
                type: "Internet Facing",
                source: "Exposure Management",
                title: "External application surface detected",
                description:
                    "The application surface is reachable from the public internet.",
                confidence: 98,
                timestamp: "2026-08-03T08:30:00.000Z",
                weight: 1,
            },
            {
                id: "evidence-exposure-001-epss",
                type: "EPSS",
                source: "Threat Intelligence Platform",
                title: "High exploitation probability",
                description:
                    "The associated vulnerability has an elevated exploitation probability.",
                confidence: 95,
                timestamp: "2026-08-03T08:35:00.000Z",
                weight: 0.95,
            },
        ],
        confidence: {
            score: 96,
            evidenceCount: 3,
            dataQuality: 95,
            reason: "Asset and external exposure evidence are current.",
        },
        recommendation: {
            id: "recommendation-exposure-001",
            entityId: "exposure-001",
            decisionId: "decision-exposure-001",
            type: "HARDEN",
            priority: "P1",
            title: "Restrict external access",
            description: "Review exposure and restrict access.",
            estimatedEffort: "Medium",
            businessImpact: "Reduces the external attack surface.",
            expectedRiskReduction: 80,
            action: {
                summary: "Harden the externally exposed application surface.",
                rationale:
                    "The escalation decision is supported by internet exposure, exploit probability and asset context.",
                expectedOutcome:
                    "The externally reachable attack surface is reduced.",
            },
        },
        explainability: {
            reason:
                "Internet accessibility and asset criticality drive exposure risk.",
            confidence: {
                score: 96,
                evidenceCount: 3,
                dataQuality: 95,
                reason: "Asset and external exposure evidence are current.",
            },
            businessImpact: "Critical digital services may be exposed.",
            mitre: ["T1190"],
            kev: true,
            epss: 0.96,
            attackPath: ["Internet", "Application Surface"],
        },
        attackSurface: "Internet-accessible application surface.",
        relatedAssets: "Related assets are available.",
        relatedFindings: "Related findings are available.",
        mitigations: "Potential mitigations are available.",
    },
];

class MockExposureRepository implements ExposureRepository {
    getExposures(): readonly Exposure[] {
        return exposures;
    }
}

export const exposureRepository: ExposureRepository =
    new MockExposureRepository();
