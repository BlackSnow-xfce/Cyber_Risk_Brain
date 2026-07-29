import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

import Panel from "@/ui/panel/Panel";
import AppButton from "@/ui/button/AppButton";
import StatusBadge from "@/ui/badge/StatusBadge";

export default function DecisionCenterPanel() {
    return (
        <Panel sx={{ minHeight: 520 }}>
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
                            Decision Workspace
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            Explainable AI-driven cyber decisions
                        </Typography>
                    </div>

                    <StatusBadge
                        status="info"
                        label="Waiting"
                    />
                </Stack>

                <Divider />

                <Stack spacing={3}>
                    <div>
                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            Highest Priority Decision
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            No active decision available.
                        </Typography>
                    </div>

                    <div>
                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            AI Recommendation
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            Waiting for Decision Engine...
                        </Typography>
                    </div>

                    <div>
                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            Evidence
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            No evidence available.
                        </Typography>
                    </div>

                    <div>
                        <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 600 }}
                        >
                            Business Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            No business context available.
                        </Typography>
                    </div>
                </Stack>

                <Divider />

                <Stack
                    direction="row"
                    spacing={2}
                >
                    <AppButton>
                        Open Decision Workspace
                    </AppButton>

                    <AppButton
                        variant="outlined"
                    >
                        Refresh
                    </AppButton>
                </Stack>
            </Stack>
        </Panel>
    );
}