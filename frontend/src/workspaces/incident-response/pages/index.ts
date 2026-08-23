import IncidentResponseOverviewPage from "./IncidentResponseOverviewPage";
import IncidentQueuePage from "./IncidentQueuePage";

export interface IncidentResponseAreaDefinition {
    title: string;
    description: string;
}

export const incidentResponseAreaRegistry = {
    "active-incidents": {
        title: "Active Incidents",
        description:
            "Coordinate incidents currently assigned for active response.",
    },
    "incident-queue": {
        title: "Incident Queue",
        description:
            "Review incidents awaiting authorized response ownership.",
    },
    "major-incidents": {
        title: "Major Incidents",
        description:
            "Maintain a dedicated coordination surface for major incidents.",
    },
    containment: {
        title: "Containment",
        description:
            "Review containment context without executing response actions.",
    },
    eradication: {
        title: "Eradication",
        description:
            "Coordinate removal work after containment has been established.",
    },
    recovery: {
        title: "Recovery",
        description:
            "Coordinate restoration context without automating recovery steps.",
    },
    "response-actions": {
        title: "Response Actions",
        description:
            "Review authorized response work without providing playbook execution.",
    },
    evidence: {
        title: "Evidence",
        description:
            "Review evidence context associated with the selected incident.",
    },
    timeline: {
        title: "Timeline",
        description:
            "Review the ordered history of the selected incident.",
    },
    "affected-assets": {
        title: "Affected Assets",
        description:
            "Review assets associated with the incident response scope.",
    },
    "impact-analysis": {
        title: "Impact Analysis",
        description:
            "Review authorized impact context without calculating business impact.",
    },
    "lessons-learned": {
        title: "Lessons Learned",
        description:
            "Document review context after incident recovery is complete.",
    },
    reports: {
        title: "Reports",
        description:
            "Review incident documentation when a reporting source is connected.",
    },
} satisfies Record<string, IncidentResponseAreaDefinition>;

export type IncidentResponseAreaId =
    keyof typeof incidentResponseAreaRegistry;

export function isIncidentResponseAreaId(
    pageId: string | null,
): pageId is IncidentResponseAreaId {
    return pageId !== null && pageId in incidentResponseAreaRegistry;
}

export { IncidentResponseOverviewPage, IncidentQueuePage };
