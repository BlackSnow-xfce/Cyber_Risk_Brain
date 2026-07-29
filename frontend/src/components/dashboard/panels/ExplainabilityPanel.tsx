import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

import Panel from "@/ui/panel/Panel";
import StatusBadge from "@/ui/badge/StatusBadge";

export default function ExplainabilityPanel() {
    return (
        <Panel sx={{ minHeight: 320 }}>
            <Stack spacing={3}>
                <Stack
                    direction="row"
                    sx={{
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <div>
                        <Typography
                            component="h2"
                            variant="h5"
                            sx={{ fontWeight: 700 }}
                        >
                            Explainability
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            Transparent decision reasoning
                        </Typography>
                    </div>

                    <StatusBadge
                        status="info"
                        label="Ready"
                    />
                </Stack>

                <Divider />

                <Stack spacing={2}>
                    <Typography color="text.secondary">
                        Decision Reasoning
                    </Typography>

                    <Typography variant="body2">
                        Waiting for Decision Engine...
                    </Typography>

                    <Divider />

                    <Typography color="text.secondary">
                        Confidence
                    </Typography>

                    <Typography variant="body2">
                        —
                    </Typography>

                    <Divider />

                    <Typography color="text.secondary">
                        Business Context
                    </Typography>

                    <Typography variant="body2">
                        —
                    </Typography>
                </Stack>
            </Stack>
        </Panel>
    );
}