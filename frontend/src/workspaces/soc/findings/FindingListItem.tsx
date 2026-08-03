import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Finding } from "./Finding";

interface FindingListItemProps {
    finding: Finding;
    selected: boolean;
    onSelect: (finding: Finding) => void;
}

export default function FindingListItem({
    finding,
    selected,
    onSelect,
}: FindingListItemProps) {
    return (
        <Paper
            component="button"
            type="button"
            variant="outlined"
            aria-pressed={selected}
            onClick={() => onSelect(finding)}
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
                        label={`Severity ${finding.severity}`}
                        size="small"
                        variant="outlined"
                    />

                    <Typography
                        variant="subtitle1"
                        sx={{ fontWeight: 600 }}
                    >
                        {finding.title}
                    </Typography>
                </Stack>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            sm: "repeat(4, minmax(0, 1fr))",
                        },
                        gap: 2,
                    }}
                >
                    <FindingAttribute
                        label="Asset"
                        value={finding.asset}
                    />
                    <FindingAttribute
                        label="Risk Score"
                        value={finding.riskScore}
                    />
                    <FindingAttribute
                        label="Confidence"
                        value={`${finding.confidence.score}%`}
                    />
                    <FindingAttribute
                        label="Status"
                        value={finding.status}
                    />
                </Box>
            </Stack>
        </Paper>
    );
}

interface FindingAttributeProps {
    label: string;
    value: string | number;
}

function FindingAttribute({
    label,
    value,
}: FindingAttributeProps) {
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
