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

const riskSections: MissionConsoleSection[] = [
    {
        title: "Enterprise Risk Overview",
        description:
            "Review enterprise cyber-risk context across business boundaries.",
        emptyState: "No enterprise risk source is connected.",
    },
    {
        title: "Top Business Risks",
        description:
            "Review prioritized business risks from an authorized source.",
        emptyState: "No prioritized business risks are available.",
    },
    {
        title: "Risk Treatment Status",
        description:
            "Maintain oversight of approved risk treatment activity.",
        emptyState: "No treatment status is available.",
    },
    {
        title: "Ownership Summary",
        description:
            "Review accountable ownership for registered business risks.",
        emptyState: "No risk ownership source is connected.",
    },
];

const businessAndGovernanceSections: MissionConsoleSection[] = [
    {
        title: "Business Service Exposure",
        description:
            "Relate authorized risk context to affected business services.",
        emptyState: "No business service exposure is available.",
    },
    {
        title: "Crown Jewels",
        description:
            "Review critical business assets within the enterprise risk context.",
        emptyState: "No crown-jewel inventory is connected.",
    },
    {
        title: "Compliance Overview",
        description:
            "Review compliance context without deriving compliance status.",
        emptyState: "No compliance source is connected.",
    },
    {
        title: "Risk Trends",
        description:
            "Review approved historical risk context when available.",
        emptyState: "No risk trend source is connected.",
    },
    {
        title: "Executive Reporting",
        description:
            "Prepare governance context for authorized executive reporting.",
        emptyState: "No executive report source is connected.",
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

export default function RiskManagerOverviewPage() {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="info.main">
                    Enterprise risk governance
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Risk Manager Mission Console
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{ mt: 1, maxWidth: 790 }}
                >
                    Translate authorized cyber-risk context into business
                    impact, ownership, treatment and governance views. Risk and
                    enterprise data sources are not connected in this foundation.
                </Typography>
            </Box>

            <Box component="section" aria-labelledby="risk-work-title">
                <Typography
                    id="risk-work-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Enterprise risk work area
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
                    {riskSections.map((section) => (
                        <MissionConsoleSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </Box>
            </Box>

            <Box
                component="section"
                aria-labelledby="governance-context-title"
            >
                <Typography
                    id="governance-context-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Business and governance context
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
                    {businessAndGovernanceSections.map((section) => (
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
