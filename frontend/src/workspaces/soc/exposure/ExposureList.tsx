import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Exposure } from "./Exposure";
import ExposureListItem from "./ExposureListItem";

interface ExposureListProps {
    exposures: readonly Exposure[];
    selectedExposureId: string | null;
    onSelect: (exposure: Exposure) => void;
}

export default function ExposureList({
    exposures,
    selectedExposureId,
    onSelect,
}: ExposureListProps) {
    return (
        <Panel component="section" aria-labelledby="exposure-list-title">
            <Stack spacing={2}>
                <Typography
                    id="exposure-list-title"
                    variant="h6"
                >
                    Exposure List
                </Typography>

                {exposures.map((exposure) => (
                    <ExposureListItem
                        key={exposure.id}
                        exposure={exposure}
                        selected={exposure.id === selectedExposureId}
                        onSelect={onSelect}
                    />
                ))}
            </Stack>
        </Panel>
    );
}
