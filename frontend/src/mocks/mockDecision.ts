import type { DecisionResponse } from "@/types/decision/DecisionResponse";

export const mockDecision: DecisionResponse = {
    id: "decision-001",

    createdAt: new Date().toISOString(),

    status: "completed",

    priority: "critical",

    decision: {
        title: "Critical Attack Path Detected",

        description:
            "PredatorAI identified an attack path leading to crown jewel assets.",

        action:
            "Immediate containment recommended.",
    },

    summary:
        "An internet-facing asset with a public exploit enables lateral movement towards critical business systems.",

    confidence: 98,

    evidence: [
        {
            id: "1",
            title: "EPSS",
            value: "98%",
            confidence: 98,
        },
        {
            id: "2",
            title: "CISA KEV",
            value: "Listed",
            confidence: 100,
        },
        {
            id: "3",
            title: "Attack Path",
            value: "Confirmed",
            confidence: 95,
        },
        {
            id: "4",
            title: "Internet Facing",
            value: "Yes",
            confidence: 100,
        },
    ],

    recommendations: [
        {
            id: "1",
            title: "Contain affected asset",

            description:
                "Immediately isolate the affected system from the network.",

            automated: false,
        },
        {
            id: "2",
            title: "Patch vulnerability",

            description:
                "Deploy vendor security update.",

            automated: false,
        },
    ],

    businessImpact: {
        operations: "High",

        financial: "High",

        compliance: "Medium",

        reputation: "High",
    },

    explainability: {
        reasoning:
            "Multiple evidence sources and attack graph correlation indicate a high probability of exploitation.",

        confidence: 98,
    },

    timeline: [
        {
            id: "1",

            timestamp: new Date().toISOString(),

            title: "Decision Created",

            description:
                "Initial reasoning completed.",
        },
    ],

    metadata: {
        engine: "PredatorAI Decision Engine",

        model: "Predator Reasoning Model",

        version: "3.0.0",
    },
};