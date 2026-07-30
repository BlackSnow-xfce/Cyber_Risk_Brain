import Chip from "@mui/material/Chip";

interface ImpactBadgeProps {
    label: string;
    severity?: "low" | "medium" | "high" | "critical";
}

const severityColor: Record<
    NonNullable<ImpactBadgeProps["severity"]>,
    "success" | "warning" | "error"
> = {
    low: "success",
    medium: "warning",
    high: "error",
    critical: "error",
};

export default function ImpactBadge({
    label,
    severity = "medium",
}: ImpactBadgeProps) {
    return (
        <Chip
            label={label}
            color={severityColor[severity]}
            size="small"
            sx={{
                fontWeight: 600,
                borderRadius: 2,
            }}
        />
    );
}