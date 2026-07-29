import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

const sources = [
    "Defender",
    "Wiz",
    "Tenable",
    "MISP",
    "Threat Intelligence",
];

type StatusItemProps = {
    label: string;
    value: string;
};

function StatusItem({
    label,
    value,
}: StatusItemProps) {
    return (
        <Box>
            <Typography
                variant="caption"
                color="text.secondary"
            >
                {label}
            </Typography>

            <Typography
                variant="body1"
                sx={{
                    fontWeight: 600,
                }}
            >
                {value}
            </Typography>
        </Box>
    );
}

export default function ContextBar() {
    return (
        <Panel>
            <Stack spacing={3}>
                <Box>
                    <Typography
                        variant="overline"
                        color="text.secondary"
                    >
                        PredatorAI Reasoning Engine
                    </Typography>

                    <Typography variant="h5">
                        Decision Workspace
                    </Typography>
                </Box>

                <Divider />

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit, minmax(170px, 1fr))",
                        gap: 3,
                    }}
                >
                    <StatusItem
                        label="Backend"
                        value="Connected"
                    />

                    <StatusItem
                        label="Decision Engine"
                        value="Ready"
                    />

                    <StatusItem
                        label="Open Decisions"
                        value="—"
                    />

                    <StatusItem
                        label="Highest Risk"
                        value="—"
                    />

                    <StatusItem
                        label="Last Analysis"
                        value="—"
                    />
                </Box>

                <Divider />

                <Box>
                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        Data Sources
                    </Typography>

                    <Stack
                        direction="row"
                        spacing={2}
                        useFlexGap
                        sx={{
                            mt: 1,
                            flexWrap: "wrap",
                        }}
                    >
                        {sources.map((source) => (
                            <Typography
                                key={source}
                                variant="body2"
                                color="text.secondary"
                            >
                                {source}
                            </Typography>
                        ))}
                    </Stack>
                </Box>
            </Stack>
        </Panel>
    );
}