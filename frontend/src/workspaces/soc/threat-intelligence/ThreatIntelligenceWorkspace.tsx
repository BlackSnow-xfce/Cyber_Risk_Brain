import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import { useSOCWorkspace } from "../SOCWorkspaceContext";
import { threatIntelligenceRepository } from "./MockThreatIntelligenceRepository";
import ThreatIntelligenceDetailsPanel from "./ThreatIntelligenceDetailsPanel";
import ThreatIntelligenceList from "./ThreatIntelligenceList";
import ThreatIntelligenceToolbar from "./ThreatIntelligenceToolbar";

export default function ThreatIntelligenceWorkspace() {
    const {
        selectedThreatIntelligence,
        setSelectedThreatIntelligence,
    } = useSOCWorkspace();
    const threats =
        threatIntelligenceRepository.getThreatIntelligence();

    return (
        <Stack spacing={2}>
            <ThreatIntelligenceToolbar />

            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        xl: "minmax(0, 1.65fr) minmax(320px, 0.75fr)",
                    },
                    gap: 2,
                    alignItems: "start",
                    minWidth: 0,
                }}
            >
                <ThreatIntelligenceList
                    threats={threats}
                    selectedThreatId={
                        selectedThreatIntelligence?.id ?? null
                    }
                    onSelect={setSelectedThreatIntelligence}
                />
                <ThreatIntelligenceDetailsPanel
                    threat={selectedThreatIntelligence}
                />
            </Box>
        </Stack>
    );
}
