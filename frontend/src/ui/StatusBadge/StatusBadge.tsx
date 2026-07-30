import "./StatusBadge.css";

type Status =
    | "healthy"
    | "live"
    | "ready"
    | "warning"
    | "critical"
    | "offline";

interface StatusBadgeProps {
    status: Status;
    label?: string;
}

export default function StatusBadge({
    status,
    label,
}: StatusBadgeProps) {
    return (
        <span className={`status-badge status-badge--${status}`}>
            {label ?? status.toUpperCase()}
        </span>
    );
}