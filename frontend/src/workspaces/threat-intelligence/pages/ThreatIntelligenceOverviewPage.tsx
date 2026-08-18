import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import IntelligenceStateCard from "./IntelligenceStateCard";
import ThreatIntelligencePageHeader from "./ThreatIntelligencePageHeader";

const overviewSections = [
    {
        title: "Active Threats",
        description: "No active-threat feed is connected to a PredatorAI backend contract.",
        status: "No data" as const,
    },
    {
        title: "Known Exploited Vulnerabilities",
        description: "CISA KEV intelligence is not available through the current backend API.",
        status: "Unavailable" as const,
    },
    {
        title: "High EPSS Vulnerabilities",
        description: "EPSS data is not available through the current backend API.",
        status: "Unavailable" as const,
    },
    {
        title: "Emerging Threats",
        description: "No emerging-threat source is connected.",
        status: "No data" as const,
    },
    {
        title: "Threat Intelligence Sources",
        description: "NVD, EPSS and CISA KEV require a future backend read contract.",
        status: "Unavailable" as const,
    },
    {
        title: "Environment Relevance",
        description: "Threat-intelligence correlation with internal findings is not evaluated.",
        status: "Not evaluated" as const,
    },
];

export default function ThreatIntelligenceOverviewPage() {
    return (
        <Stack spacing={3}>
            <ThreatIntelligencePageHeader
                eyebrow="Analyst intelligence workspace"
                title="Threat Intelligence Overview"
                description="Assess available intelligence, its provenance and its relevance to the environment. Sources that are not connected remain explicitly visible."
            />
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
                {overviewSections.map((section) => (
                    <IntelligenceStateCard key={section.title} {...section} />
                ))}
            </Box>
        </Stack>
    );
}
