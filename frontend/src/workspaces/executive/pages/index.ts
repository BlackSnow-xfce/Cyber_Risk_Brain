import ExecutiveOverviewPage from "./ExecutiveOverviewPage";

export interface ExecutiveAreaDefinition {
    title: string;
    description: string;
}

export const executiveAreaRegistry = {
    "executive-dashboard": {
        title: "Executive Dashboard",
        description:
            "Review strategic enterprise context without operational security detail.",
    },
    "enterprise-risk": {
        title: "Enterprise Risk",
        description:
            "Review authorized enterprise cyber-risk context without recalculation.",
    },
    "strategic-decisions": {
        title: "Strategic Decisions",
        description:
            "Review decisions requiring executive ownership or direction.",
    },
    "business-exposure": {
        title: "Business Exposure",
        description:
            "Review approved exposure context across business boundaries.",
    },
    "critical-business-services": {
        title: "Critical Business Services",
        description:
            "Review critical services from an authorized business inventory.",
    },
    "business-impact": {
        title: "Business Impact",
        description:
            "Review existing business-impact assessments without deriving them in the UI.",
    },
    "investment-priorities": {
        title: "Investment Priorities",
        description:
            "Review approved investment priorities without creating financial projections.",
    },
    "risk-portfolio": {
        title: "Risk Portfolio",
        description:
            "Review the authorized portfolio of enterprise cyber risks.",
    },
    "compliance-status": {
        title: "Compliance Status",
        description:
            "Review authorized compliance context without calculating status.",
    },
    "security-strategy": {
        title: "Security Strategy",
        description:
            "Review approved strategic security direction when available.",
    },
    roadmap: {
        title: "Roadmap",
        description:
            "Review an authorized security roadmap without generating delivery status.",
    },
    "board-reporting": {
        title: "Board Reporting",
        description:
            "Review board-ready reporting from an authorized source.",
    },
    trends: {
        title: "Trends",
        description:
            "Review approved historical context without generating trend data.",
    },
    "decision-history": {
        title: "Decision History",
        description:
            "Review authorized strategic decision history when available.",
    },
} satisfies Record<string, ExecutiveAreaDefinition>;

export type ExecutiveAreaId = keyof typeof executiveAreaRegistry;

export function isExecutiveAreaId(
    pageId: string | null,
): pageId is ExecutiveAreaId {
    return pageId !== null && pageId in executiveAreaRegistry;
}

export { ExecutiveOverviewPage };
