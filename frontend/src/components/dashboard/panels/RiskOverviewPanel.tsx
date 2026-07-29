import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

import Panel from "@/ui/panel/Panel";
import StatusBadge from "@/ui/badge/StatusBadge";

export default function RiskOverviewPanel() {
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
                            Risk Overview
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            Current enterprise posture
                        </Typography>
                    </div>

                    <StatusBadge
                        status="low"
                        label="Healthy"
                    />
                </Stack>

                <Divider />

                <Stack spacing={2}>
                    <Stack
                        direction="row"
                        sx={{
                            justifyContent: "space-between",
                        }}
                    >
                        <Typography color="text.secondary">
                            Critical Risks
                        </Typography>

                        <Typography sx={{ fontWeight: 700 }}>
                            —
                        </Typography>
                    </Stack>

                    <Stack
                        direction="row"
                        sx={{
                            justifyContent: "space-between",
                        }}
                    >
                        <Typography color="text.secondary">
                            High Risks
                        </Typography>

                        <Typography sx={{ fontWeight: 700 }}>
                            —
                        </Typography>
                    </Stack>

                    <Stack
                        direction="row"
                        sx={{
                            justifyContent: "space-between",
                        }}
                    >
                        <Typography color="text.secondary">
                            Assets at Risk
                        </Typography>

                        <Typography sx={{ fontWeight: 700 }}>
                            —
                        </Typography>
                    </Stack>

                    <Stack
                        direction="row"
                        sx={{
                            justifyContent: "space-between",
                        }}
                    >
                        <Typography color="text.secondary">
                            Active Decisions
                        </Typography>

                        <Typography sx={{ fontWeight: 700 }}>
                            —
                        </Typography>
                    </Stack>
                </Stack>
            </Stack>
        </Panel>
    );
}