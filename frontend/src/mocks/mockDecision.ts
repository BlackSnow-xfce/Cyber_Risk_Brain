import type { Decision } from "@/types/decision";

import {
    ActionStatus,
    ActionType,
    ConfidenceLevel,
    DecisionState,
    DecisionType,
    EvidenceType,
    Priority,
    RiskBand,
    Severity,
    Urgency,
} from "@/types/decision";

export const mockDecision: Decision = {
    metadata: {
        id: "decision-001",
        key: "ATTACK_PATH_CRITICAL_001",
        version: 1,
        tenantId: "predatorai",
        workspace: "SOC_ANALYST",
        engineVersion: "3.0.0",
        modelVersion: "predator-reasoning-v1",
        correlationId: "corr-001",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },

    status: {
        state: DecisionState.READY,
        reason: "Critical attack path identified",
        changedBy: "Decision Engine",
        changedAt: new Date().toISOString(),
    },

    summary: {
        title: "Critical Attack Path Detected",
        subtitle:
            "Internet-facing vulnerability enables lateral movement",
        description:
            "PredatorAI identified a critical attack path leading towards protected enterprise resources.",
        category: "CYBER_RISK",
        tags: [
            "critical",
            "attack-path",
            "internet-facing",
        ],
        decisionType: DecisionType.MITIGATION,
    },

    recommendation: {
        action: "Immediate containment recommended.",
        summary:
            "Restrict external exposure and initiate remediation workflow.",
        rationale:
            "Exploit availability combined with asset criticality creates elevated risk.",
        expectedOutcome:
            "Reduction of attack surface and prevention of lateral movement.",
        urgency: Urgency.IMMEDIATE,
        rollbackAvailable: false,
        alternatives: [],
    },

    context: {
        asset: {
            assetId: "asset-001",
            name: "Production Application Gateway",
            type: "APPLICATION",
            owner: "Platform Security",
            criticality: "HIGH",
            internetFacing: true,
            operatingSystem: "Linux",
            location: "Production",
        },

        threat: {
            cves: [
                "CVE-2025-0001",
            ],
            kevListed: true,
            epss: 0.96,
            cvss: 9.8,
            attackPaths: [
                "Internet → Gateway → Internal Systems",
            ],
            mitreTechniques: [
                "T1190",
            ],
            exploitAvailable: true,
        },

        business: {
            businessUnit: "Enterprise IT",
            application: "Core Platform",
            process: "Digital Services",
            criticality: "HIGH",
            complianceFrameworks: [
                "ISO27001",
                "NIS2",
            ],
        },
    },

    risk: {
        score: 98,
        band: RiskBand.CRITICAL,
        severity: Severity.CRITICAL,
        priority: Priority.P1,
        urgency: Urgency.IMMEDIATE,
        likelihood: 0.95,
        impact: 0.95,
        trend: 0.8,
        calculatedAt: new Date().toISOString(),
        engineVersion: "3.0.0",
    },

    confidence: {
        score: 98,
        level: ConfidenceLevel.HIGH,
        evidenceCoverage: 95,
        sourceCoverage: 90,
        evidenceQuality: 95,
        modelConfidence: 98,
        missingEvidence: [],
        conflictingEvidence: [],
        calculatedAt: new Date().toISOString(),
    },

    evidence: {
        items: [
            {
                id: "evidence-001",
                type: EvidenceType.VULNERABILITY,
                source: "Vulnerability Scanner",
                sourceReference: "finding-001",
                summary:
                    "Critical vulnerability detected on internet-facing asset.",
                timestamp: new Date().toISOString(),
                confidence: 98,
                weight: 1,
                facts: [
                    "Public exploit available",
                    "Asset externally reachable",
                ],
            },
        ],
        coverage: 95,
        quality: 95,
        sourceCount: 3,
        duplicateCount: 0,
    },

    explainability: {
        summary:
            "Decision generated based on exposure, exploitability, business criticality and attack path correlation.",

        reasoning:
            "PredatorAI correlated exposure, threat intelligence and business impact to generate this recommendation.",

        factors: [],

        rules: [],

        assumptions: [
            "Asset ownership information is current.",
            "Threat intelligence sources are available.",
        ],

        uncertainties: [],

        counterfactuals: [],
    },

    impact: {
        operational:
            "Potential disruption of critical services.",

        financial:
            "High potential business impact.",

        regulatory:
            "Potential compliance exposure.",

        reputational:
            "Potential customer trust impact.",

        confidentiality: "HIGH",

        integrity: "HIGH",

        availability: "HIGH",

        narrative:
            "Compromise could affect critical enterprise operations.",
    },

    actions: {
        actions: [
            {
                id: "action-001",

                title: "Restrict Internet Exposure",

                description:
                    "Remove unnecessary external accessibility.",

                type: ActionType.ISOLATE_ASSET,

                priority: Priority.P1,

                status: ActionStatus.PROPOSED,

                owner: "Security Operations",

                automation: false,

                outcome:
                    "Reduced attack surface.",
            },
        ],

        executionSummary:
            "Immediate containment required.",
    },

    timeline: {
        events: [],
    },

    references: {
    assets: [],
    findings: [],
    incidents: [],
    tickets: [],
    playbooks: [],
    cves: [],
    kev: [],
    mitre: [],
},

    audit: {
        entries: [],
    },
};