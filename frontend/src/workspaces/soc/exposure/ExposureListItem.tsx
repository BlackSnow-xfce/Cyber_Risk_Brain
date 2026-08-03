import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Exposure } from "./Exposure";

interface ExposureListItemProps {
    exposure: Exposure;
    selected: boolean;
    onSelect: (exposure: Exposure) => void;
}

export default function ExposureListItem({
    exposure,
    selected,
    onSelect,
}: ExposureListItemProps) {
    return (
        <Paper
            component="button"
            type="button"
            variant="outlined"
            aria-pressed={selected}
            onClick={() => onSelect(exposure)}
            sx={{
                p: 2,
                borderRadius: 2,
                width: "100%",
                color: "text.primary",
                textAlign: "left",
                font: "inherit",
                cursor: "pointer",
            }}
        >
            <Stack spacing={2}>
                <Stack
                    direction="row"
                    spacing={1}
                    useFlexGap
                    sx={{
                        alignItems: "center",
                        flexWrap: "wrap",
                    }}
                >
                    <Chip
                        label={`Severity ${exposure.severity}`}
                        size="small"
                        variant="outlined"
                    />

                    <Box>
                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            Exposure Type {exposure.type}
                        </Typography>

                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            {exposure.title}
                        </Typography>
                    </Box>
                </Stack>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            sm: "repeat(3, minmax(0, 1fr))",
                        },
                        gap: 2,
                    }}
                >
                    <ExposureAttribute
                        label="Internet Facing"
                        value={exposure.internetFacing}
                    />
                    <ExposureAttribute
                        label="Risk Score"
                        value={exposure.riskScore}
                    />
                    <ExposureAttribute
                        label="Status"
                        value={exposure.status}
                    />
                </Box>
            </Stack>
        </Paper>
    );
}

interface ExposureAttributeProps {
    label: string;
    value: string | number;
}

function ExposureAttribute({
    label,
    value,
}: ExposureAttributeProps) {
    return (
        <Box>
            <Typography
                variant="caption"
                color="text.secondary"
            >
                {label}
            </Typography>

            <Typography variant="body2">{value}</Typography>
        </Box>
    );
}
