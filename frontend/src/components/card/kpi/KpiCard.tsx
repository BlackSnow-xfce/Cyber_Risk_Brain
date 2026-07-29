import Card from "../Card";
import "./KpiCard.css";

interface KpiCardProps {
    title: string;
    value: string | number;
    change?: string;
    trend?: "up" | "down" | "neutral";
}

export default function KpiCard({
    title,
    value,
    change,
    trend = "neutral",
}: KpiCardProps) {
    return (
        <Card className="pa-kpi-card">
            <div className="pa-kpi-card__label">
                {title}
            </div>

            <div className="pa-kpi-card__value">
                {value}
            </div>

            {change && (
                <div className={`pa-kpi-card__trend pa-kpi-card__trend--${trend}`}>
                    {change}
                </div>
            )}
        </Card>
    );
}
