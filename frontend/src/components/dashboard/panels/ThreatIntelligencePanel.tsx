import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

import Panel from "@/ui/panel/Panel";
import StatusBadge from "@/ui/badge/StatusBadge";

export default function ThreatIntelligencePanel() {
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
                            Threat Intelligence
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            External intelligence feeds
                        </Typography>
                    </div>

                    <StatusBadge
                        status="info"
                        label="Online"
                    />
                </Stack>

                <Divider />

                <Stack spacing={2}>
                    <Stack
                        direction="row"
                        sx={{ justifyContent: "space-between" }}
                    >
                        <Typography color="text.secondary">
                            EPSS
                        </Typography>

                        <Typography>—</Typography>
                    </Stack>

                    <Stack
                        direction="row"
                        sx={{ justifyContent: "space-between" }}
                    >
                        <Typography color="text.secondary">
                            CISA KEV
                        </Typography>

                        <Typography>—</Typography>
                    </Stack>

                    <Stack
                        direction="row"
                        sx={{ justifyContent: "space-between" }}
                    >
                        <Typography color="text.secondary">
                            Exploit Status
                        </Typography>

                        <Typography>—</Typography>
                    </Stack>

                    <Stack
                        direction="row"
                        sx={{ justifyContent: "space-between" }}
                    >
                        <Typography color="text.secondary">
                            Threat Level
                        </Typography>

                        <Typography>—</Typography>
                    </Stack>
                </Stack>
            </Stack>
        </Panel>
    );
}