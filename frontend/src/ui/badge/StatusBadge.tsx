import Chip from "@mui/material/Chip";

export type StatusType =
    | "critical"
    | "high"
    | "medium"
    | "low"
    | "success"
    | "info";

interface StatusBadgeProps {
    label: string;
    status: StatusType;
}

const colors: Record<StatusType, "error" | "warning" | "success" | "info"> = {
    critical: "error",
    high: "warning",
    medium: "info",
    low: "success",
    success: "success",
    info: "info",
};

export default function StatusBadge({
    label,
    status,
}: StatusBadgeProps) {
    return (
        <Chip
            label={label}
            color={colors[status]}
            size="small"
            variant="filled"
        />
    );
}