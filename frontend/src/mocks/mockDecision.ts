import { ActionStatus, ActionType, ConfidenceLevel, DecisionState, DecisionType, EvidenceType, Priority, RiskBand, Severity, Urgency } from "@/types/decision/enums";
import type { Decision } from "@/types/decision";

const now = new Date().toISOString();

export const mockDecision: Decision = {
    metadata: {
        id: "decision-001",
        key: "DEC-2026-0001",
        version: 1,
        tenantId: "predatorai-demo",
        workspace: "soc-analyst",
        engineVersion: "3.0.0",
        modelVersion: "Predator Reasoning Model",
        correlationId: "corr-001",
        createdAt: now,
        updatedAt: now,
    },

    status: {
        state: DecisionState.COMPLETED,
        previousState: DecisionState.EXECUTING,
        reason: "Decision execution finished successfully.",
        changedBy: "PredatorAI",
        changedAt: now,
    },

    summary: {
        title: "Critical Attack Path Detected",
        subtitle: "Internet-facing asset threatens crown jewels",
        description:
            "PredatorAI identified an exploitable attack path from an exposed asset to critical business systems.",
        category: "Attack Path",
        tags: ["KEV", "EPSS", "Internet Facing", "Lateral Movement"],
        decisionType: DecisionType.CONTAINMENT,
    },

    recommendation: {
        action: "Immediately isolate the affected asset.",
        summary: "Contain the compromised attack path.",
        rationale:
            "Public exploit availability, KEV listing and attack-path correlation significantly increase business risk.",
        expectedOutcome:
            "Prevent lateral movement while remediation is performed.",
        urgency: Urgency.IMMEDIATE,
        estimatedEffort: "30 minutes",
        rollbackAvailable: true,
        rollbackDescription:
            "Reconnect the host after validation and patch verification.",
        alternatives: [
            "Restrict network access using firewall rules.",
            "Disable affected service until remediation is complete.",
        ],
    },

    context: {
        asset: {
            assetId: "srv-web-001",
            name: "Customer Portal",
            type: "Windows Server",
            owner: "Infrastructure Team",
            criticality: "Critical",
            internetFacing: true,
            operatingSystem: "Windows Server 2022",
            location: "Frankfurt",
        },

        threat: {
            cves: ["CVE-2025-12345"],
            kevListed: true,
            epss: 0.98,
            cvss: 9.8,
            attackPaths: [
                "Internet → Web Server → AD → Crown Jewel",
            ],
            mitreTechniques: [
                "T1190",
                "T1021",
                "T1078",
            ],
            exploitAvailable: true,
        },

        business: {
            businessUnit: "E-Commerce",
            application: "Customer Portal",
            process: "Order Processing",
            criticality: "Critical",
            complianceFrameworks: [
                "ISO 27001",
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
        likelihood: 97,
        impact: 99,
        trend: 12,
        calculatedAt: now,
        engineVersion: "3.0.0",
    },

    confidence: {
        score: 98,
        level: ConfidenceLevel.VERY_HIGH,
        evidenceCoverage: 96,
        sourceCoverage: 94,
        evidenceQuality: 97,
        modelConfidence: 98,
        missingEvidence: [],
        conflictingEvidence: [],
        calculatedAt: now,
    },

    evidence: {
        items: [
            {
                id: "ev-001",
                type: EvidenceType.VULNERABILITY,
                source: "Tenable",
                sourceReference: "TEN-12345",
                summary: "Critical internet-facing vulnerability detected.",
                timestamp: now,
                confidence: 98,
                weight: 1,
                facts: [
                    "CVSS 9.8",
                    "EPSS 98%",
                    "Public exploit available",
                ],
            },
            {
                id: "ev-002",
                type: EvidenceType.ATTACK_PATH,
                source: "PredatorAI",
                sourceReference: "PATH-001",
                summary: "Attack path to crown jewel confirmed.",
                timestamp: now,
                confidence: 96,
                weight: 1,
                facts: [
                    "Lateral movement possible",
                    "Critical asset reachable",
                ],
            },
        ],
        coverage: 96,
        quality: 97,
        sourceCount: 5,
        duplicateCount: 0,
    },

    explainability: {
        summary:
            "Multiple independent evidence sources support the decision.",
        reasoning:
            "Attack-path correlation, KEV intelligence and vulnerability context produce a critical containment recommendation.",
        factors: [
            {
                id: "factor-1",
                label: "Attack Path",
                contribution: 45,
                weight: 1,
                direction: "positive",
                evidenceIds: ["ev-002"],
            },
            {
                id: "factor-2",
                label: "KEV Listed",
                contribution: 35,
                weight: 1,
                direction: "positive",
                evidenceIds: ["ev-001"],
            },
        ],
        rules: [
            {
                id: "rule-1",
                name: "Critical Attack Path",
                version: "1.0",
                matched: true,
                contribution: 90,
                description:
                    "Internet-facing exploitable asset reaches crown jewel.",
            },
        ],
        assumptions: [],
        uncertainties: [],
        counterfactuals: [
            "Without public exploit availability the recommendation would be downgraded.",
        ],
    },

    impact: {
        operational: "High",
        financial: "High",
        regulatory: "Medium",
        reputational: "High",
        confidentiality: "High",
        integrity: "High",
        availability: "High",
        narrative:
            "Successful exploitation could interrupt critical business processes.",
    },

    actions: {
        actions: [
            {
                id: "action-1",
                title: "Isolate Asset",
                description: "Disconnect affected host from the network.",
                type: ActionType.ISOLATE_ASSET,
                priority: Priority.P1,
                status: ActionStatus.PROPOSED,
                owner: "SOC",
                dueDate: now,
                automation: false,
            },
        ],
        executionSummary:
            "One immediate containment action proposed.",
    },

    timeline: {
        events: [
            {
                id: "timeline-1",
                timestamp: now,
                actor: "PredatorAI",
                type: "Decision",
                title: "Decision created",
                description:
                    "Reasoning completed successfully.",
            },
        ],
    },

    references: {
        assets: ["srv-web-001"],
        findings: ["TEN-12345"],
        incidents: [],
        tickets: ["JIRA-123"],
        playbooks: ["PB-CONTAIN-001"],
        cves: ["CVE-2025-12345"],
        kev: ["CISA-KEV"],
        mitre: ["T1190", "T1021", "T1078"],
    },

    audit: {
        entries: [
            {
                id: "audit-1",
                actor: "PredatorAI",
                timestamp: now,
                action: "Decision Generated",
            },
        ],
    },
};