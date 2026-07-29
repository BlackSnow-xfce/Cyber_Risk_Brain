import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

import Panel from "@/ui/panel/Panel";
import StatusBadge from "@/ui/badge/StatusBadge";

export default function TimelinePanel() {
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
                            Timeline
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            Decision history and events
                        </Typography>
                    </div>

                    <StatusBadge
                        status="info"
                        label="Live"
                    />
                </Stack>

                <Divider />

                <Stack spacing={2}>
                    <Typography color="text.secondary">
                        No events available.
                    </Typography>

                    <Typography variant="body2">
                        The Decision Engine will populate this
                        timeline with explainable events.
                    </Typography>
                </Stack>
            </Stack>
        </Panel>
    );
}