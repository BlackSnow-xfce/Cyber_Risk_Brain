import Box from "@mui/material/Box";

import DecisionCenterPanel from "@/components/dashboard/panels/DecisionCenterPanel";
import ExplainabilityPanel from "@/components/dashboard/panels/ExplainabilityPanel";
import RiskOverviewPanel from "@/components/dashboard/panels/RiskOverviewPanel";
import ThreatIntelligencePanel from "@/components/dashboard/panels/ThreatIntelligencePanel";
import TimelinePanel from "@/components/dashboard/panels/TimelinePanel";

export default function DashboardLayout() {
    return (
        <Box
            component="main"
            sx={{
                display: "grid",
                gridTemplateColumns: {
                    xs: "minmax(0, 1fr)",
                    xl: "minmax(0, 7fr) minmax(320px, 3fr)",
                },
                gap: 2,
                alignItems: "start",
                width: "100%",
                minWidth: 0,
            }}
        >
            <Box
                component="section"
                aria-label="Decision workspace"
                sx={{
                    minWidth: 0,
                }}
            >
                <DecisionCenterPanel />
            </Box>

            <Box
                component="aside"
                aria-label="Cyber reasoning insights"
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    minWidth: 0,
                }}
            >
                <RiskOverviewPanel />

                <ThreatIntelligencePanel />

                <ExplainabilityPanel />

                <TimelinePanel />
            </Box>
        </Box>
    );
}