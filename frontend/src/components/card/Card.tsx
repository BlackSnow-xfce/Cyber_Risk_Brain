import "./Card.css";
import type { PropsWithChildren, ReactNode } from "react";

interface CardProps extends PropsWithChildren {
    title?: string;
    subtitle?: string;
    actions?: ReactNode;
    className?: string;
}

export default function Card({
    title,
    subtitle,
    actions,
    className = "",
    children,
}: CardProps) {
    return (
        <section className={`pa-card ${className}`.trim()}>
            {(title || subtitle || actions) && (
                <header className="pa-card__header">
                    <div className="pa-card__titles">
                        {title && (
                            <h3 className="pa-card__title">
                                {title}
                            </h3>
                        )}

                        {subtitle && (
                            <p className="pa-card__subtitle">
                                {subtitle}
                            </p>
                        )}
                    </div>

                    {actions && (
                        <div className="pa-card__actions">
                            {actions}
                        </div>
                    )}
                </header>
            )}

            <div className="pa-card__content">
                {children}
            </div>
        </section>
    );
}