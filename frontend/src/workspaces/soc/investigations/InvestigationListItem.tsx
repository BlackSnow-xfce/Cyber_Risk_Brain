import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Investigation } from "./Investigation";

interface InvestigationListItemProps {
    investigation: Investigation;
    selected: boolean;
    onSelect: (investigation: Investigation) => void;
}

export default function InvestigationListItem({
    investigation,
    selected,
    onSelect,
}: InvestigationListItemProps) {
    return (
        <Paper
            component="button"
            type="button"
            variant="outlined"
            aria-pressed={selected}
            onClick={() => onSelect(investigation)}
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
                        label={`Priority ${investigation.recommendation.priority}`}
                        size="small"
                        variant="outlined"
                    />

                    <Box>
                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            Investigation ID {investigation.id}
                        </Typography>

                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            {investigation.title}
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
                    <InvestigationAttribute
                        label="Assigned Analyst"
                        value={investigation.assignedAnalyst}
                    />
                    <InvestigationAttribute
                        label="Status"
                        value={investigation.status}
                    />
                    <InvestigationAttribute
                        label="Last Updated"
                        value={investigation.lastUpdated}
                    />
                </Box>
            </Stack>
        </Paper>
    );
}

interface InvestigationAttributeProps {
    label: string;
    value: string;
}

function InvestigationAttribute({
    label,
    value,
}: InvestigationAttributeProps) {
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
