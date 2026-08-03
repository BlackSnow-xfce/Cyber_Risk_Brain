import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import { useSOCWorkspace } from "../SOCWorkspaceContext";
import ExposureDetailsPanel from "./ExposureDetailsPanel";
import ExposureList from "./ExposureList";
import ExposureToolbar from "./ExposureToolbar";
import { exposureRepository } from "./MockExposureRepository";

export default function ExposureWorkspace() {
    const { selectedExposure, setSelectedExposure } =
        useSOCWorkspace();
    const exposures = exposureRepository.getExposures();

    return (
        <Stack spacing={2}>
            <ExposureToolbar />

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
                <ExposureList
                    exposures={exposures}
                    selectedExposureId={selectedExposure?.id ?? null}
                    onSelect={setSelectedExposure}
                />
                <ExposureDetailsPanel exposure={selectedExposure} />
            </Box>
        </Stack>
    );
}
