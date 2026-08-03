import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import { useSOCWorkspace } from "../SOCWorkspaceContext";
import InvestigationDetailsPanel from "./InvestigationDetailsPanel";
import { investigationRepository } from "./MockInvestigationRepository";
import InvestigationsList from "./InvestigationsList";
import InvestigationsToolbar from "./InvestigationsToolbar";

export default function InvestigationsWorkspace() {
    const { selectedInvestigation, setSelectedInvestigation } =
        useSOCWorkspace();
    const investigations = investigationRepository.getInvestigations();

    return (
        <Stack spacing={2}>
            <InvestigationsToolbar />

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
                <InvestigationsList
                    investigations={investigations}
                    selectedInvestigationId={
                        selectedInvestigation?.id ?? null
                    }
                    onSelect={setSelectedInvestigation}
                />
                <InvestigationDetailsPanel
                    investigation={selectedInvestigation}
                />
            </Box>
        </Stack>
    );
}
