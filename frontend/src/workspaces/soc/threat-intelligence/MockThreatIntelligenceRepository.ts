import type { ThreatIntelligence } from "./ThreatIntelligence";
import type { ThreatIntelligenceRepository } from "./ThreatIntelligenceRepository";

const threatIntelligence: readonly ThreatIntelligence[] = [
    {
        id: "threat-001",
        title: "Active exploitation campaign",
        description: "An active exploitation campaign requires review.",
        type: "Campaign",
        severity: "Critical",
        status: "Active",
        decision: {
            id: "decision-threat-001",
            entityId: "threat-001",
            type: "INVESTIGATE",
            priority: "P1",
            state: "Proposed",
            confidence: 94,
            createdAt: "2026-08-03T11:20:00.000Z",
            outcome: {
                summary: "Investigate the active exploitation campaign.",
                rationale:
                    "Verified campaign evidence and strong relationships to a finding, asset and investigation establish direct relevance.",
                supportingReasoningIds: [
                    "reasoning-threat-001-step-1",
                    "reasoning-threat-001-step-2",
                    "reasoning-threat-001-step-3",
                ],
            },
        },
        reasoning: {
            id: "reasoning-threat-001",
            entityId: "threat-001",
            overallConfidence: 94,
            steps: [
                {
                    id: "reasoning-threat-001-step-1",
                    title: "Threat campaign verified",
                    description:
                        "Threat intelligence evidence confirms active exploitation activity.",
                    evidenceIds: [
                        "evidence-threat-001-intelligence",
                        "evidence-threat-001-kev",
                    ],
                    correlationIds: [],
                    confidence: 97,
                    order: 1,
                },
                {
                    id: "reasoning-threat-001-step-2",
                    title: "Affected finding and asset correlated",
                    description:
                        "The campaign shares vulnerability context with a finding and its affected asset.",
                    evidenceIds: ["evidence-threat-001-kev"],
                    correlationIds: [
                        "correlation-threat-001-finding-001",
                        "correlation-threat-001-asset-001",
                    ],
                    confidence: 94,
                    order: 2,
                },
                {
                    id: "reasoning-threat-001-step-3",
                    title: "Investigation relevance confirmed",
                    description:
                        "The active SOC investigation includes this threat campaign context.",
                    evidenceIds: [
                        "evidence-threat-001-intelligence",
                    ],
                    correlationIds: [
                        "correlation-threat-001-investigation-001",
                    ],
                    confidence: 94,
                    order: 3,
                },
            ],
            result: {
                summary:
                    "The exploitation campaign is verified and linked to affected entities.",
                confidence: 94,
                findings: [
                    "Active exploitation and KEV evidence are present.",
                    "A related finding, asset and investigation are identified.",
                ],
            },
        },
        correlations: [
            {
                id: "correlation-threat-001-finding-001",
                type: "SAME_CVE",
                targetType: "Finding",
                targetId: "finding-001",
                title: "Shared exploited vulnerability",
                description:
                    "The campaign targets the vulnerability identified by the finding.",
                strength: "Strong",
                confidence: 96,
            },
            {
                id: "correlation-threat-001-asset-001",
                type: "RELATED_ASSET",
                targetType: "Asset",
                targetId: "asset-001",
                title: "Potentially targeted asset",
                description:
                    "The production gateway matches the campaign target profile.",
                strength: "Strong",
                confidence: 92,
            },
            {
                id: "correlation-threat-001-investigation-001",
                type: "RELATED_INVESTIGATION",
                targetType: "Investigation",
                targetId: "investigation-001",
                title: "Threat considered by investigation",
                description:
                    "The active SOC investigation includes this campaign context.",
                strength: "Strong",
                confidence: 94,
            },
        ],
        evidence: [
            {
                id: "evidence-threat-001-intelligence",
                type: "Threat Intelligence",
                source: "Threat Intelligence Platform",
                title: "Active exploitation campaign reported",
                description:
                    "Multiple intelligence sources report active exploitation activity.",
                confidence: 94,
                timestamp: "2026-08-03T06:00:00.000Z",
                weight: 1,
            },
            {
                id: "evidence-threat-001-kev",
                type: "KEV",
                source: "Threat Intelligence Platform",
                title: "Vulnerability is listed in KEV",
                description:
                    "The associated vulnerability is present in the known exploited catalog.",
                confidence: 100,
                timestamp: "2026-08-03T06:05:00.000Z",
                weight: 1,
            },
        ],
        riskScore: 94,
        source: "Threat Intelligence",
        confidence: {
            score: 94,
            evidenceCount: 5,
            dataQuality: 92,
            reason: "Multiple intelligence sources support this assessment.",
        },
        recommendation: {
            id: "recommendation-threat-001",
            entityId: "threat-001",
            decisionId: "decision-threat-001",
            type: "INVESTIGATE",
            priority: "P1",
            title: "Review affected assets",
            description: "Review indicators and affected assets.",
            estimatedEffort: "Medium",
            businessImpact: "Reduces exposure to active exploitation.",
            expectedRiskReduction: 65,
            action: {
                summary: "Investigate campaign indicators and affected assets.",
                rationale:
                    "The investigation decision is supported by campaign, KEV and entity correlations.",
                expectedOutcome:
                    "The campaign relevance and affected scope are clarified.",
            },
        },
        explainability: {
            reason:
                "Active exploitation evidence and asset relevance drive severity.",
            confidence: {
                score: 94,
                evidenceCount: 5,
                dataQuality: 92,
                reason:
                    "Multiple intelligence sources support this assessment.",
            },
            businessImpact: "Related enterprise assets may be targeted.",
            mitre: ["T1190"],
            kev: true,
            epss: 0.96,
            attackPath: ["Threat Actor", "Internet-facing Asset"],
        },
        lastUpdated: "Recently updated",
        intelligenceSource: "Correlated threat intelligence sources.",
        indicators: "Related indicators are available.",
        relatedAssets: "Potentially related assets are available.",
    },
];

class MockThreatIntelligenceRepository
    implements ThreatIntelligenceRepository
{
    getThreatIntelligence(): readonly ThreatIntelligence[] {
        return threatIntelligence;
    }
}

export const threatIntelligenceRepository: ThreatIntelligenceRepository =
    new MockThreatIntelligenceRepository();
