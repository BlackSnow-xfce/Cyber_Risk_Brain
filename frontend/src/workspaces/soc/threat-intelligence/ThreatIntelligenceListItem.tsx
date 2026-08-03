import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { ThreatIntelligence } from "./ThreatIntelligence";

interface ThreatIntelligenceListItemProps {
    threat: ThreatIntelligence;
    selected: boolean;
    onSelect: (threat: ThreatIntelligence) => void;
}

export default function ThreatIntelligenceListItem({
    threat,
    selected,
    onSelect,
}: ThreatIntelligenceListItemProps) {
    return (
        <Paper
            component="button"
            type="button"
            variant="outlined"
            aria-pressed={selected}
            onClick={() => onSelect(threat)}
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
                        label={`Severity ${threat.severity}`}
                        size="small"
                        variant="outlined"
                    />

                    <Box>
                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            Threat Type {threat.type}
                        </Typography>

                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            {threat.title}
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
                    <ThreatAttribute
                        label="Source"
                        value={threat.source}
                    />
                    <ThreatAttribute
                        label="Confidence"
                        value={`${threat.confidence.score}%`}
                    />
                    <ThreatAttribute
                        label="Last Updated"
                        value={threat.lastUpdated}
                    />
                </Box>
            </Stack>
        </Paper>
    );
}

interface ThreatAttributeProps {
    label: string;
    value: string;
}

function ThreatAttribute({ label, value }: ThreatAttributeProps) {
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
