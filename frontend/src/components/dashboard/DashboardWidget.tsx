import type { PropsWithChildren } from "react";

import Typography from "@mui/material/Typography";

import Card from "@/components/card/Card";
import StatusBadge, {
    type StatusType,
} from "@/components/dashboard/ui/StatusBadge/StatusBadge";

import "./DashboardWidget.css";

interface DashboardWidgetProps extends PropsWithChildren {
    title: string;
    subtitle?: string;
    status?: StatusType;
    statusLabel?: string;
    className?: string;
}

export default function DashboardWidget({
    title,
    subtitle,
    status,
    statusLabel,
    className,
    children,
}: DashboardWidgetProps) {
    return (
        <Card className={`dashboard-widget ${className ?? ""}`.trim()}>
            <header className="dashboard-widget__header">
                <div>
                    <h3 className="dashboard-widget__title">
                        {title}
                    </h3>

                    {subtitle && (
                        <Typography
                            component="p"
                            className="dashboard-widget__subtitle"
                        >
                            {subtitle}
                        </Typography>
                    )}
                </div>

                {status && (
                    <StatusBadge
                        status={status}
                        label={statusLabel}
                    />
                )}
            </header>

            <div className="dashboard-widget__divider" />

            <section className="dashboard-widget__content">
                {children}
            </section>
        </Card>
    );
}
