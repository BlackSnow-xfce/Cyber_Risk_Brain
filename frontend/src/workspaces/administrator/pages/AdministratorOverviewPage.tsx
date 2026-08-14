import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface MissionConsoleSection {
    title: string;
    description: string;
    emptyState: string;
}

interface MissionConsoleSectionCardProps {
    section: MissionConsoleSection;
}

const platformSections: MissionConsoleSection[] = [
    {
        title: "Platform Health",
        description:
            "Review authorized health information for platform services.",
        emptyState: "No platform health source is connected.",
    },
    {
        title: "Connected Systems",
        description:
            "Review systems registered with the platform when available.",
        emptyState: "No connected-system inventory is available.",
    },
    {
        title: "Connector Status",
        description:
            "Review connector state from an authorized operations source.",
        emptyState: "No connector status source is connected.",
    },
    {
        title: "Synchronization Overview",
        description:
            "Review synchronization activity without deriving operational status.",
        emptyState: "No synchronization source is connected.",
    },
];

const operationsSections: MissionConsoleSection[] = [
    {
        title: "AI Configuration",
        description:
            "Review approved AI configuration when a platform source is available.",
        emptyState: "No AI configuration source is connected.",
    },
    {
        title: "User Management",
        description:
            "Review administrative identity context without managing identities.",
        emptyState: "No user-management source is connected.",
    },
    {
        title: "Audit Activity",
        description:
            "Review authorized platform audit activity when available.",
        emptyState: "No audit source is connected.",
    },
    {
        title: "Background Jobs",
        description:
            "Review platform job activity without controlling execution.",
        emptyState: "No background-job source is connected.",
    },
    {
        title: "System Notifications",
        description:
            "Review administrative notifications from an authorized source.",
        emptyState: "No system-notification source is connected.",
    },
];

function MissionConsoleSectionCard({
    section,
}: MissionConsoleSectionCardProps) {
    return (
        <Panel
            component="section"
            sx={{
                display: "flex",
                flexDirection: "column",
                minHeight: 184,
            }}
        >
            <Stack
                direction="row"
                spacing={1}
                sx={{
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                }}
            >
                <Typography variant="h6">
                    {section.title}
                </Typography>

                <Chip
                    label="Not connected"
                    size="small"
                    variant="outlined"
                    color="default"
                />
            </Stack>

            <Typography color="text.secondary" sx={{ mt: 1 }}>
                {section.description}
            </Typography>

            <Box
                sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexGrow: 1,
                    mt: 2,
                    p: 2,
                    border: "1px dashed",
                    borderColor: "divider",
                    borderRadius: 1.5,
                    backgroundColor: "action.hover",
                }}
            >
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ textAlign: "center" }}
                >
                    {section.emptyState}
                </Typography>
            </Box>
        </Panel>
    );
}

export default function AdministratorOverviewPage() {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="text.secondary">
                    Platform operations workspace
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Administrator Mission Console
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{ mt: 1, maxWidth: 800 }}
                >
                    Operate and govern PredatorAI through isolated platform,
                    data, identity and configuration views. Administrative
                    systems are not connected in this foundation.
                </Typography>
            </Box>

            <Box component="section" aria-labelledby="platform-state-title">
                <Typography
                    id="platform-state-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Platform state
                </Typography>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            md: "repeat(2, minmax(0, 1fr))",
                            xl: "repeat(4, minmax(0, 1fr))",
                        },
                        gap: 2,
                    }}
                >
                    {platformSections.map((section) => (
                        <MissionConsoleSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </Box>
            </Box>

            <Box component="section" aria-labelledby="operations-context-title">
                <Typography
                    id="operations-context-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Administration and operations
                </Typography>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            md: "repeat(2, minmax(0, 1fr))",
                            xl: "repeat(3, minmax(0, 1fr))",
                        },
                        gap: 2,
                    }}
                >
                    {operationsSections.map((section) => (
                        <MissionConsoleSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </Box>
            </Box>
        </Stack>
    );
}
