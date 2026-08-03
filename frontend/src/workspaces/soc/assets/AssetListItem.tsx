import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Asset } from "./Asset";

interface AssetListItemProps {
    asset: Asset;
    selected: boolean;
    onSelect: (asset: Asset) => void;
}

export default function AssetListItem({
    asset,
    selected,
    onSelect,
}: AssetListItemProps) {
    return (
        <Paper
            component="button"
            type="button"
            variant="outlined"
            aria-pressed={selected}
            onClick={() => onSelect(asset)}
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
                        label={`Criticality ${asset.severity}`}
                        size="small"
                        variant="outlined"
                    />

                    <Box>
                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            Asset Type {asset.type}
                        </Typography>

                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            {asset.title}
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
                    <AssetAttribute label="Owner" value={asset.owner} />
                    <AssetAttribute
                        label="Risk Score"
                        value={asset.riskScore}
                    />
                    <AssetAttribute label="Status" value={asset.status} />
                </Box>
            </Stack>
        </Paper>
    );
}

interface AssetAttributeProps {
    label: string;
    value: string | number;
}

function AssetAttribute({ label, value }: AssetAttributeProps) {
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
