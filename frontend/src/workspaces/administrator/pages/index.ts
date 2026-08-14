import AdministratorOverviewPage from "./AdministratorOverviewPage";

export interface AdministratorAreaDefinition {
    title: string;
    description: string;
}

export const administratorAreaRegistry = {
    "platform-health": {
        title: "Platform Health",
        description: "Review authorized health information for platform services.",
    },
    services: {
        title: "Services",
        description: "Review registered platform services when available.",
    },
    integrations: {
        title: "Integrations",
        description: "Review configured platform integrations from an authorized source.",
    },
    users: {
        title: "Users",
        description: "Review administrative user context without managing identities.",
    },
    roles: {
        title: "Roles",
        description: "Review configured platform roles without changing authorization.",
    },
    permissions: {
        title: "Permissions",
        description: "Review permission configuration without enforcing authorization in the UI.",
    },
    organizations: {
        title: "Organizations",
        description: "Review configured organization context when available.",
    },
    connectors: {
        title: "Connectors",
        description: "Review connector configuration without implementing connector behavior.",
    },
    "data-sources": {
        title: "Data Sources",
        description: "Review registered data sources from an authorized platform source.",
    },
    synchronization: {
        title: "Synchronization",
        description: "Review synchronization context without executing synchronization.",
    },
    "import-status": {
        title: "Import Status",
        description: "Review import activity without deriving or simulating status.",
    },
    "ai-models": {
        title: "AI Models",
        description: "Review approved model configuration without implementing an AI engine.",
    },
    policies: {
        title: "Policies",
        description: "Review configured platform policies when available.",
    },
    rules: {
        title: "Rules",
        description: "Review configured platform rules without executing them.",
    },
    "prompt-library": {
        title: "Prompt Library",
        description: "Review approved prompt configuration without invoking AI models.",
    },
    "audit-log": {
        title: "Audit Log",
        description: "Review authorized audit activity when a source is connected.",
    },
    "background-jobs": {
        title: "Background Jobs",
        description: "Review job activity without controlling background execution.",
    },
    notifications: {
        title: "Notifications",
        description: "Review administrative notifications from an authorized source.",
    },
    "system-settings": {
        title: "System Settings",
        description: "Review platform settings without persisting configuration changes.",
    },
    "feature-flags": {
        title: "Feature Flags",
        description: "Review feature configuration without changing runtime behavior.",
    },
    licensing: {
        title: "Licensing",
        description: "Review licensing context when an authorized source is connected.",
    },
} satisfies Record<string, AdministratorAreaDefinition>;

export type AdministratorAreaId = keyof typeof administratorAreaRegistry;

export function isAdministratorAreaId(
    pageId: string | null,
): pageId is AdministratorAreaId {
    return pageId !== null && pageId in administratorAreaRegistry;
}

export { AdministratorOverviewPage };
