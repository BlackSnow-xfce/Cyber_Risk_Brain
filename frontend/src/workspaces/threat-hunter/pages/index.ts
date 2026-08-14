import ThreatHunterOverviewPage from "./ThreatHunterOverviewPage";

export interface ThreatHunterAreaDefinition {
    title: string;
    description: string;
}

export const threatHunterAreaRegistry = {
    hunts: {
        title: "Hunts",
        description:
            "Coordinate proactive investigations around a defined security question.",
    },
    hypotheses: {
        title: "Hunt Hypotheses",
        description:
            "Frame and review testable hypotheses before collecting supporting evidence.",
    },
    "query-workspace": {
        title: "Query Workspace",
        description:
            "Prepare hunting queries without implying an active execution connection.",
    },
    "ioc-explorer": {
        title: "IOC Explorer",
        description:
            "Inspect indicators within the context of a defined hunt.",
    },
    entities: {
        title: "Entities",
        description:
            "Review the assets, identities and other entities associated with a hunt.",
    },
    "mitre-attack": {
        title: "MITRE ATT&CK",
        description:
            "Relate hunt coverage to tactics and techniques without creating new intelligence.",
    },
    "hunt-timeline": {
        title: "Hunt Timeline",
        description:
            "Review the ordered activity of a selected hunt when a source is connected.",
    },
    "saved-hunts": {
        title: "Saved Hunts",
        description:
            "Return to retained hunt definitions when persistence is available.",
    },
} satisfies Record<string, ThreatHunterAreaDefinition>;

export type ThreatHunterAreaId = keyof typeof threatHunterAreaRegistry;

export function isThreatHunterAreaId(
    pageId: string | null,
): pageId is ThreatHunterAreaId {
    return pageId !== null && pageId in threatHunterAreaRegistry;
}

export { ThreatHunterOverviewPage };
