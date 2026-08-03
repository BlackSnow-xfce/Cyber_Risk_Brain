import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import { useSOCWorkspace } from "../SOCWorkspaceContext";
import FindingDetailsPanel from "./FindingDetailsPanel";
import { findingRepository } from "./MockFindingRepository";
import FindingsList from "./FindingsList";
import FindingsToolbar from "./FindingsToolbar";

export default function FindingsWorkspace() {
    const { selectedFinding, setSelectedFinding } =
        useSOCWorkspace();
    const findings = findingRepository.getFindings();

    return (
        <Stack spacing={2}>
            <FindingsToolbar />

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
                <FindingsList
                    findings={findings}
                    selectedFindingId={selectedFinding?.id ?? null}
                    onSelect={setSelectedFinding}
                />
                <FindingDetailsPanel finding={selectedFinding} />
            </Box>
        </Stack>
    );
}
