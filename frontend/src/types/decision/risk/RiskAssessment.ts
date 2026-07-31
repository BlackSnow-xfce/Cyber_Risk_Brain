import type {
    Priority,
    RiskBand,
    Severity,
    Urgency,
} from "../enums";

export interface RiskAssessment {
    score: number;

    band: RiskBand;

    severity: Severity;

    priority: Priority;

    urgency: Urgency;

    likelihood: number;

    impact: number;

    trend: number;

    calculatedAt: string;

    engineVersion: string;
}