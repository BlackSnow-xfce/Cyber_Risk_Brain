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

const responseSections: MissionConsoleSection[] = [
    {
        title: "Active Incidents",
        description:
            "Coordinate the incidents currently assigned for response.",
        emptyState: "No active incident source is connected.",
    },
    {
        title: "Current Response Phase",
        description:
            "Maintain shared awareness of the selected incident phase.",
        emptyState: "No response phase is available.",
    },
    {
        title: "Containment Status",
        description:
            "Review containment scope without executing response actions.",
        emptyState: "No containment status is available.",
    },
    {
        title: "Response Actions",
        description:
            "Review authorized response work associated with an incident.",
        emptyState: "No response actions are available.",
    },
];

const coordinationSections: MissionConsoleSection[] = [
    {
        title: "Evidence Collection",
        description:
            "Track the evidence context required for incident investigation.",
        emptyState: "No evidence source is connected.",
    },
    {
        title: "Timeline",
        description:
            "Review the ordered history of the selected incident.",
        emptyState: "No incident timeline is available.",
    },
    {
        title: "Affected Assets",
        description:
            "Maintain visibility of assets associated with the response.",
        emptyState: "No affected assets are available.",
    },
    {
        title: "Communication Status",
        description:
            "Coordinate stakeholder communication for the selected incident.",
        emptyState: "No communication channel is connected.",
    },
    {
        title: "Lessons Learned",
        description:
            "Capture review context after response and recovery conclude.",
        emptyState: "No lessons-learned record is available.",
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

export default function IncidentResponseOverviewPage() {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="error.main">
                    Coordinated incident response
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Incident Response Mission Console
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{ mt: 1, maxWidth: 780 }}
                >
                    Coordinate containment, investigation, recovery and
                    documentation within one isolated response workspace.
                    Incident systems are not connected in this foundation.
                </Typography>
            </Box>

            <Box component="section" aria-labelledby="response-work-title">
                <Typography
                    id="response-work-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Response work area
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
                    {responseSections.map((section) => (
                        <MissionConsoleSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </Box>
            </Box>

            <Box
                component="section"
                aria-labelledby="response-context-title"
            >
                <Typography
                    id="response-context-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Investigation and coordination context
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
                    {coordinationSections.map((section) => (
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
