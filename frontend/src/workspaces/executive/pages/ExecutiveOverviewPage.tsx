import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import ExecutiveDashboardLayout from "../ExecutiveDashboardLayout";

interface MissionConsoleSection {
    title: string;
    description: string;
    emptyState: string;
}

interface MissionConsoleSectionCardProps {
    section: MissionConsoleSection;
}

const decisionSections: MissionConsoleSection[] = [
    {
        title: "Enterprise Risk Overview",
        description:
            "Review enterprise cyber-risk context for strategic oversight.",
        emptyState: "No enterprise risk source is connected.",
    },
    {
        title: "Strategic Decisions",
        description:
            "Review decisions that require executive ownership or direction.",
        emptyState: "No strategic decisions are available.",
    },
    {
        title: "Investment Priorities",
        description:
            "Review approved security investment context and priorities.",
        emptyState: "No investment planning source is connected.",
    },
    {
        title: "Executive Briefing",
        description:
            "Review an authorized strategic briefing when one is available.",
        emptyState: "No executive briefing is available.",
    },
];

const enterpriseSections: MissionConsoleSection[] = [
    {
        title: "Business Impact",
        description:
            "Review existing business-impact context without deriving it in the UI.",
        emptyState: "No business-impact source is connected.",
    },
    {
        title: "Critical Business Services",
        description:
            "Review critical services associated with enterprise risk context.",
        emptyState: "No business-service inventory is connected.",
    },
    {
        title: "Risk Portfolio",
        description:
            "Review the authorized portfolio of enterprise cyber risks.",
        emptyState: "No risk portfolio is available.",
    },
    {
        title: "Security Program Progress",
        description:
            "Review approved security-program progress when available.",
        emptyState: "No security-program source is connected.",
    },
    {
        title: "Board Reporting",
        description:
            "Review board-ready reporting from an authorized source.",
        emptyState: "No board report is available.",
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

export default function ExecutiveOverviewPage() {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="warning.main">
                    Strategic cyber leadership
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Executive Mission Console
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{ mt: 1, maxWidth: 800 }}
                >
                    Maintain strategic awareness of enterprise risk, business
                    impact, investment priorities and decisions without exposing
                    operational security detail. Executive data sources are not
                    connected in this foundation.
                </Typography>
            </Box>

            <Box component="section" aria-labelledby="executive-decisions-title">
                <Typography
                    id="executive-decisions-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Decision and investment agenda
                </Typography>

                <ExecutiveDashboardLayout>
                    {decisionSections.map((section) => (
                        <MissionConsoleSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </ExecutiveDashboardLayout>
            </Box>

            <Box component="section" aria-labelledby="enterprise-context-title">
                <Typography
                    id="enterprise-context-title"
                    variant="h6"
                    sx={{ mb: 1.5 }}
                >
                    Enterprise and governance context
                </Typography>

                <ExecutiveDashboardLayout>
                    {enterpriseSections.map((section) => (
                        <MissionConsoleSectionCard
                            key={section.title}
                            section={section}
                        />
                    ))}
                </ExecutiveDashboardLayout>
            </Box>
        </Stack>
    );
}
