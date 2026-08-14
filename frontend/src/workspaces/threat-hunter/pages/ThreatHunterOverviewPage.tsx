import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface WorkspaceSection {
    title: string;
    description: string;
    emptyState: string;
}

interface WorkspaceSectionCardProps {
    section: WorkspaceSection;
}

const primaryWorkSections: WorkspaceSection[] = [
    {
        title: "Active Hunts",
        description:
            "Coordinate hypotheses, scope and investigation progress.",
        emptyState: "No active hunts are available.",
    },
    {
        title: "Hunt Hypotheses",
        description:
            "Frame testable security hypotheses before investigation.",
        emptyState: "No hunt hypotheses are available.",
    },
    {
        title: "Query Workspace",
        description:
            "Prepare and review hunting queries within an active hunt.",
        emptyState: "Query execution is not connected.",
    },
];

const contextSections: WorkspaceSection[] = [
    {
        title: "Recent Signals",
        description:
            "Review signals relevant to the current hunting focus.",
        emptyState: "No signal source is connected.",
    },
    {
        title: "Entity Context",
        description:
            "Inspect the entities associated with the current hypothesis.",
        emptyState: "No entity is selected.",
    },
    {
        title: "MITRE Coverage",
        description:
            "Relate the current hunt to applicable ATT&CK techniques.",
        emptyState: "No MITRE coverage is available.",
    },
    {
        title: "Hunt Timeline",
        description:
            "Follow the ordered activity of the selected hunt.",
        emptyState: "No hunt timeline is available.",
    },
    {
        title: "Saved Hunts",
        description:
            "Return to retained hunt definitions and investigation context.",
        emptyState: "No saved hunts are available.",
    },
];

function WorkspaceSectionCard({
    section,
}: WorkspaceSectionCardProps) {
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

            <Typography
                color="text.secondary"
                sx={{ mt: 1 }}
            >
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

export default function ThreatHunterOverviewPage() {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="warning.main">
                    Proactive discovery workspace
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Threat Hunter Mission Console
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{ mt: 1, maxWidth: 760 }}
                >
                    Develop hypotheses, prepare queries and maintain entity
                    context without interrupting the operational SOC workflow.
                    Hunting data sources are not connected in this foundation.
                </Typography>
            </Box>

            <Box component="section" aria-labelledby="hunt-work-area-title">
                <Typography
                    id="hunt-work-area-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Hunt work area
                </Typography>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            lg: "repeat(3, minmax(0, 1fr))",
                        },
                        gap: 2,
                    }}
                >
                    {primaryWorkSections.map((section) => (
                        <WorkspaceSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </Box>
            </Box>

            <Box component="section" aria-labelledby="hunt-context-title">
                <Typography
                    id="hunt-context-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Hunting context
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
                    {contextSections.map((section) => (
                        <WorkspaceSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </Box>
            </Box>
        </Stack>
    );
}
