import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { FindingSummary } from "./FindingSummary";
import { findingsDensity } from "./FindingsPresentationDensity";

interface FindingListItemProps {
    finding: FindingSummary;
    selected: boolean;
    onSelect: (finding: FindingSummary) => void;
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
                        label={`Severity ${finding.vendorSeverity}`}
                        size="small"
                        variant="outlined"
                        sx={findingsDensity.chip}
                    />

                    <Typography
                        variant="subtitle2"
                        sx={findingsDensity.subsectionHeading}
                        data-findings-typography="subsection-heading"
                    >
                        {finding.title}
                    </Typography>
                </Stack>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            sm: "repeat(2, minmax(0, 1fr))",
                        },
                        gap: 2,
                    }}
                >
                    <FindingAttribute
                        label="Asset"
                        value={finding.asset}
                    />
                    <FindingAttribute
                        label="Source"
                        value={finding.source}
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
                sx={findingsDensity.fieldLabel}
                data-findings-typography="field-label"
            >
                {label}
            </Typography>

            <Typography variant="body2" sx={findingsDensity.primaryValue} data-findings-typography="primary-value">{value}</Typography>
        </Box>
    );
}
