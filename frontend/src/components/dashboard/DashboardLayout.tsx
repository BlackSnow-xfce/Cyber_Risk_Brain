import Box from "@mui/material/Box";

import DashboardGrid from "./DashboardGrid";

import DecisionCenterPanel from "./panels/DecisionCenterPanel";
import ExplainabilityPanel from "./panels/ExplainabilityPanel";
import RiskOverviewPanel from "./panels/RiskOverviewPanel";
import ThreatIntelligencePanel from "./panels/ThreatIntelligencePanel";
import TimelinePanel from "./panels/TimelinePanel";

export default function DashboardLayout() {
    return (
        <DashboardGrid>
            <Box sx={{ gridColumn: "1 / -1" }}>
                <DecisionCenterPanel />
            </Box>

            <Box sx={{ gridColumn: "span 6" }}>
                <RiskOverviewPanel />
            </Box>

            <Box sx={{ gridColumn: "span 6" }}>
                <ExplainabilityPanel />
            </Box>

            <Box sx={{ gridColumn: "span 6" }}>
                <ThreatIntelligencePanel />
            </Box>

            <Box sx={{ gridColumn: "span 6" }}>
                <TimelinePanel />
            </Box>
        </DashboardGrid>
    );
}