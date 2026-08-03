import type { ElementType } from "react";

import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DashboardWidget from "@/components/dashboard/DashboardWidget";
import MetricRow from "@/components/dashboard/ui/MetricRow/MetricRow";
import type { StatusType } from "@/components/dashboard/ui/StatusBadge/StatusBadge";

export type PipelineStageStatus = "Completed" | "Active" | "Pending";

interface PipelineCardProps {
    icon: ElementType;
    title: string;
    description: string;
    countLabel: string;
    status: PipelineStageStatus;
    items: readonly string[];
}

const statusTypes: Record<PipelineStageStatus, StatusType> = {
    Completed: "healthy",
    Active: "live",
    Pending: "offline",
};

export default function PipelineCard({
    icon: Icon,
    title,
    description,
    countLabel,
    status,
    items,
}: PipelineCardProps) {
    return (
        <DashboardWidget
            title={title}
            subtitle={description}
            status={statusTypes[status]}
            statusLabel={status}
        >
            <Stack spacing={1}>
                <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: "center" }}
                >
                    <Icon fontSize="small" color="action" />
                    <Typography variant="subtitle2">{countLabel}</Typography>
                </Stack>

                {items.map((item) => (
                    <MetricRow key={item} label="Type" value={item} />
                ))}
            </Stack>
        </DashboardWidget>
    );
}
