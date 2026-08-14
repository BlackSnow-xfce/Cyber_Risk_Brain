import RiskManagerOverviewPage from "./RiskManagerOverviewPage";

export interface RiskManagerAreaDefinition {
    title: string;
    description: string;
}

export const riskManagerAreaRegistry = {
    "risk-register": {
        title: "Risk Register",
        description:
            "Review registered enterprise risks from an authorized source.",
    },
    "critical-risks": {
        title: "Critical Risks",
        description:
            "Review approved critical-risk classifications without recalculating priority.",
    },
    "treatment-plans": {
        title: "Treatment Plans",
        description:
            "Maintain oversight of approved risk treatment activity.",
    },
    "business-services": {
        title: "Business Services",
        description:
            "Review business services associated with enterprise risk context.",
    },
    "crown-jewels": {
        title: "Crown Jewels",
        description:
            "Review critical business assets from an authorized inventory.",
    },
    "business-impact": {
        title: "Business Impact",
        description:
            "Review existing business-impact assessments without deriving them in the UI.",
    },
    "risk-ownership": {
        title: "Risk Ownership",
        description:
            "Review accountable ownership associated with registered risks.",
    },
    compliance: {
        title: "Compliance",
        description:
            "Review authorized compliance context without calculating compliance status.",
    },
    exceptions: {
        title: "Exceptions",
        description:
            "Review approved governance exceptions when a source is connected.",
    },
    "risk-acceptance": {
        title: "Risk Acceptance",
        description:
            "Review documented risk-acceptance decisions without creating approvals.",
    },
    policies: {
        title: "Policies",
        description:
            "Review policies associated with enterprise cyber-risk governance.",
    },
    trends: {
        title: "Risk Trends",
        description:
            "Review approved historical risk context without generating trend data.",
    },
    "executive-reports": {
        title: "Executive Reports",
        description:
            "Review authorized executive reporting when a report source is connected.",
    },
} satisfies Record<string, RiskManagerAreaDefinition>;

export type RiskManagerAreaId = keyof typeof riskManagerAreaRegistry;

export function isRiskManagerAreaId(
    pageId: string | null,
): pageId is RiskManagerAreaId {
    return pageId !== null && pageId in riskManagerAreaRegistry;
}

export { RiskManagerOverviewPage };
