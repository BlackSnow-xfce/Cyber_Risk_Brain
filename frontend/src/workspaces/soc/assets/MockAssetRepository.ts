import type { Asset } from "./Asset";
import type { AssetRepository } from "./AssetRepository";

const assets: readonly Asset[] = [
    {
        id: "asset-001",
        title: "Production Application Gateway",
        description: "Internet-facing production gateway.",
        type: "Application Gateway",
        severity: "Critical",
        owner: "Platform Security",
        riskScore: 98,
        status: "Active",
        decision: {
            id: "decision-asset-001",
            entityId: "asset-001",
            type: "MONITOR",
            priority: "P2",
            state: "Proposed",
            confidence: 96,
            createdAt: "2026-08-03T11:10:00.000Z",
            outcome: {
                summary: "Maintain enhanced monitoring of the production asset.",
                rationale:
                    "The asset is verified as critical and externally exposed with related finding and threat context.",
                supportingReasoningIds: [
                    "reasoning-asset-001-step-1",
                    "reasoning-asset-001-step-2",
                    "reasoning-asset-001-step-3",
                    "reasoning-asset-001-step-4",
                ],
            },
        },
        reasoning: {
            id: "reasoning-asset-001",
            entityId: "asset-001",
            overallConfidence: 96,
            steps: [
                {
                    id: "reasoning-asset-001-step-1",
                    title: "Asset inventory verified",
                    description:
                        "Inventory evidence confirms the identity and production role of the asset.",
                    evidenceIds: ["evidence-asset-001-inventory"],
                    correlationIds: [],
                    confidence: 97,
                    order: 1,
                },
                {
                    id: "reasoning-asset-001-step-2",
                    title: "External exposure confirmed",
                    description:
                        "Exposure evidence confirms that the asset is reachable from the public internet.",
                    evidenceIds: ["evidence-asset-001-facing"],
                    correlationIds: [
                        "correlation-asset-001-exposure-001",
                    ],
                    confidence: 97,
                    order: 2,
                },
                {
                    id: "reasoning-asset-001-step-3",
                    title: "Related critical finding identified",
                    description:
                        "A strongly correlated vulnerability finding affects the asset.",
                    evidenceIds: ["evidence-asset-001-inventory"],
                    correlationIds: [
                        "correlation-asset-001-finding-001",
                    ],
                    confidence: 98,
                    order: 3,
                },
                {
                    id: "reasoning-asset-001-step-4",
                    title: "Active threat context confirmed",
                    description:
                        "Threat intelligence identifies active exploitation relevant to this asset.",
                    evidenceIds: ["evidence-asset-001-facing"],
                    correlationIds: [
                        "correlation-asset-001-threat-001",
                    ],
                    confidence: 94,
                    order: 4,
                },
            ],
            result: {
                summary:
                    "The critical production asset is externally exposed and linked to active risk context.",
                confidence: 96,
                findings: [
                    "Asset identity and criticality are verified.",
                    "External exposure and related security context are confirmed.",
                ],
            },
        },
        correlations: [
            {
                id: "correlation-asset-001-finding-001",
                type: "RELATED_FINDING",
                targetType: "Finding",
                targetId: "finding-001",
                title: "Critical vulnerability finding",
                description:
                    "A critical vulnerability finding affects this asset.",
                strength: "Strong",
                confidence: 98,
            },
            {
                id: "correlation-asset-001-threat-001",
                type: "RELATED_THREAT",
                targetType: "ThreatIntelligence",
                targetId: "threat-001",
                title: "Relevant exploitation threat",
                description:
                    "Active exploitation intelligence is relevant to this asset.",
                strength: "Strong",
                confidence: 94,
            },
            {
                id: "correlation-asset-001-exposure-001",
                type: "RELATED_EXPOSURE",
                targetType: "Exposure",
                targetId: "exposure-001",
                title: "External application exposure",
                description:
                    "This asset is included in the external application surface.",
                strength: "Strong",
                confidence: 97,
            },
        ],
        evidence: [
            {
                id: "evidence-asset-001-inventory",
                type: "Asset Inventory",
                source: "Asset Inventory",
                title: "Critical production asset",
                description:
                    "The application gateway is registered as a critical production asset.",
                confidence: 97,
                timestamp: "2026-08-03T07:30:00.000Z",
                weight: 1,
            },
            {
                id: "evidence-asset-001-facing",
                type: "Internet Facing",
                source: "Exposure Management",
                title: "Public network exposure confirmed",
                description:
                    "External reachability was confirmed for the application gateway.",
                confidence: 96,
                timestamp: "2026-08-03T07:35:00.000Z",
                weight: 0.95,
            },
        ],
        confidence: {
            score: 96,
            evidenceCount: 3,
            dataQuality: 95,
            reason: "Asset inventory and exposure evidence are current.",
        },
        recommendation: {
            id: "recommendation-asset-001",
            entityId: "asset-001",
            decisionId: "decision-asset-001",
            type: "MONITOR",
            priority: "P2",
            title: "Review exposure",
            description: "Review exposure and remediation priority.",
            estimatedEffort: "Medium",
            businessImpact: "Protects critical digital services.",
            expectedRiskReduction: 45,
            action: {
                summary: "Maintain enhanced monitoring of the asset.",
                rationale:
                    "The monitoring decision reflects verified exposure and related threat context.",
                expectedOutcome:
                    "Changes in the asset exposure are identified promptly.",
            },
        },
        explainability: {
            reason:
                "Criticality and internet exposure drive the asset risk.",
            confidence: {
                score: 96,
                evidenceCount: 3,
                dataQuality: 95,
                reason: "Asset inventory and exposure evidence are current.",
            },
            businessImpact: "Critical digital services may be affected.",
            mitre: ["T1190"],
            kev: true,
            epss: 0.96,
            attackPath: ["Internet", "Application Gateway"],
        },
        businessContext: "Supports critical digital services.",
        relatedFindings: "Related security findings are available.",
        relatedInvestigations: "Related investigations are available.",
        vulnerabilities: "Correlated vulnerabilities are available.",
    },
];

class MockAssetRepository implements AssetRepository {
    getAssets(): readonly Asset[] {
        return assets;
    }
}

export const assetRepository: AssetRepository =
    new MockAssetRepository();
