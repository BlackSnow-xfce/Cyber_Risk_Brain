import "./MetricRow.css";

interface MetricRowProps {
    label: string;
    value: string | number;
}

export default function MetricRow({
    label,
    value,
}: MetricRowProps) {
    return (
        <div className="metric-row">
            <span className="metric-row__label">
                {label}
            </span>

            <strong className="metric-row__value">
                {value}
            </strong>
        </div>
    );
}