import type { Investigation } from "./Investigation";
import type { InvestigationRepository } from "./InvestigationRepository";

const investigations: readonly Investigation[] = [
    {
        id: "investigation-001",
        title: "Critical exposure investigation",
        description: "A critical exposure is under investigation.",
        severity: "Critical",
        riskScore: 96,
        confidence: {
            score: 94,
            evidenceCount: 4,
            dataQuality: 93,
            reason: "Correlated investigation evidence is available.",
        },
        recommendation: {
            id: "recommendation-investigation-001",
            entityId: "investigation-001",
            decisionId: "decision-investigation-001",
            type: "ISOLATE",
            priority: "P1",
            title: "Continue containment review",
            description:
                "Continue investigation and containment review.",
            estimatedEffort: "High",
            businessImpact: "Reduces risk of operational impact.",
            expectedRiskReduction: 80,
            action: {
                summary: "Isolate the affected exposure scope.",
                rationale:
                    "The mitigation decision is supported by investigation, finding and threat context.",
                expectedOutcome:
                    "The investigated exposure is contained from broader operations.",
            },
        },
        explainability: {
            reason:
                "Exposure severity and correlated evidence drive the investigation priority.",
            confidence: {
                score: 94,
                evidenceCount: 4,
                dataQuality: 93,
                reason: "Correlated investigation evidence is available.",
            },
            businessImpact: "Critical operations may be affected.",
            mitre: ["T1190"],
            kev: true,
            epss: 0.96,
            attackPath: ["Internet", "Application Gateway"],
        },
        assignedAnalyst: "SOC Analyst",
        status: "Open",
        inference: [
            {
                id: "inference-investigation-001-validation",
                entityId: "investigation-001",
                type: "ADDITIONAL_VALIDATION_REQUIRED",
                strength: "Medium",
                title: "Additional forensic validation is required",
                description: "Detection and playbook knowledge identify investigation context that still requires analyst validation.",
                confidence: 90,
                supportingKnowledgeIds: ["knowledge-detection-public-exploit", "knowledge-playbook-critical-exposure"],
                supportingBindingIds: ["binding-detection-investigation-001", "binding-playbook-investigation-001"],
                supportingEvidenceIds: ["evidence-investigation-001-activity", "evidence-investigation-001-scan"],
                supportingCorrelationIds: ["correlation-investigation-001-finding-001", "correlation-investigation-001-threat-001"],
                result: {
                    summary: "The correlated investigation context requires additional analyst validation.",
                    confidence: 90,
                    findings: ["Relevant detection knowledge maps to the scan evidence.", "Playbook applicability has not yet been validated."],
                },
            },
        ],
        decision: {
            id: "decision-investigation-001",
            entityId: "investigation-001",
            type: "MITIGATE",
            priority: "P1",
            state: "Proposed",
            confidence: 97,
            createdAt: "2026-08-03T11:15:00.000Z",
            outcome: {
                summary: "Mitigate the exposure covered by the investigation.",
                rationale:
                    "Reviewed evidence and strong finding, asset and threat relationships establish the investigated exposure.",
                supportingReasoningIds: [
                    "reasoning-investigation-001-step-1",
                    "reasoning-investigation-001-step-2",
                    "reasoning-investigation-001-step-3",
                ],
            },
        },
        reasoning: {
            id: "reasoning-investigation-001",
            entityId: "investigation-001",
            overallConfidence: 97,
            steps: [
                {
                    id: "reasoning-investigation-001-step-1",
                    title: "Investigation evidence reviewed",
                    description:
                        "SOC activity and vulnerability scan evidence are present in the investigation context.",
                    evidenceIds: [
                        "evidence-investigation-001-activity",
                        "evidence-investigation-001-scan",
                    ],
                    correlationIds: [],
                    confidence: 99,
                    order: 1,
                },
                {
                    id: "reasoning-investigation-001-step-2",
                    title: "Related finding and asset confirmed",
                    description:
                        "The investigation is strongly linked to the critical finding and production asset.",
                    evidenceIds: [
                        "evidence-investigation-001-scan",
                    ],
                    correlationIds: [
                        "correlation-investigation-001-finding-001",
                        "correlation-investigation-001-asset-001",
                    ],
                    confidence: 100,
                    order: 2,
                },
                {
                    id: "reasoning-investigation-001-step-3",
                    title: "Threat intelligence correlated",
                    description:
                        "The active exploitation campaign is relevant to the investigation scope.",
                    evidenceIds: [
                        "evidence-investigation-001-scan",
                    ],
                    correlationIds: [
                        "correlation-investigation-001-threat-001",
                    ],
                    confidence: 94,
                    order: 3,
                },
            ],
            result: {
                summary:
                    "Investigation evidence, affected entities and threat context are consistently linked.",
                confidence: 97,
                findings: [
                    "The critical finding and asset are in scope.",
                    "Active threat intelligence is relevant to the investigation.",
                ],
            },
        },
        correlations: [
            {
                id: "correlation-investigation-001-finding-001",
                type: "RELATED_FINDING",
                targetType: "Finding",
                targetId: "finding-001",
                title: "Primary investigation finding",
                description:
                    "The critical vulnerability finding initiated this investigation.",
                strength: "Strong",
                confidence: 100,
            },
            {
                id: "correlation-investigation-001-asset-001",
                type: "RELATED_ASSET",
                targetType: "Asset",
                targetId: "asset-001",
                title: "Investigated production asset",
                description:
                    "The production application gateway is in investigation scope.",
                strength: "Strong",
                confidence: 100,
            },
            {
                id: "correlation-investigation-001-threat-001",
                type: "RELATED_THREAT",
                targetType: "ThreatIntelligence",
                targetId: "threat-001",
                title: "Relevant threat campaign",
                description:
                    "The investigation considers the active exploitation campaign.",
                strength: "Strong",
                confidence: 94,
            },
        ],
        evidence: [
            {
                id: "evidence-investigation-001-activity",
                type: "Investigation Activity",
                source: "SOC Investigation",
                title: "Analyst investigation opened",
                description:
                    "The SOC opened an investigation for the critical exposure.",
                confidence: 100,
                timestamp: "2026-08-03T10:00:00.000Z",
                weight: 0.8,
            },
            {
                id: "evidence-investigation-001-scan",
                type: "Vulnerability Scan",
                source: "Vulnerability Scanner",
                title: "Critical scan result correlated",
                description:
                    "A critical vulnerability scan result is linked to the investigation.",
                confidence: 98,
                timestamp: "2026-08-03T10:05:00.000Z",
                weight: 1,
            },
        ],
        lastUpdated: "Recently updated",
        timeline: "Investigation activity is available.",
        relatedFindings: "Related findings are available.",
        analystNotes: "Analyst notes are available.",
    },
];

class MockInvestigationRepository implements InvestigationRepository {
    getInvestigations(): readonly Investigation[] {
        return investigations;
    }
}

export const investigationRepository: InvestigationRepository =
    new MockInvestigationRepository();
