import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";
import StatusBadge, {
    type StatusType,
} from "@/ui/badge/StatusBadge";

interface KpiCardProps {
    title: string;
    value: string | number;
    status?: StatusType;
    statusLabel?: string;
}

export default function KpiCard({
    title,
    value,
    status,
    statusLabel,
}: KpiCardProps) {
    return (
        <Panel>
            <Stack spacing={2}>
                <Stack
                    direction="row"
                    sx={{
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {title}
                    </Typography>

                    {status && statusLabel ? (
                        <StatusBadge
                            status={status}
                            label={statusLabel}
                        />
                    ) : null}
                </Stack>

                <Typography
                    component="div"
                    variant="h4"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    {value}
                </Typography>
            </Stack>
        </Panel>
    );
}