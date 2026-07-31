import type { ConfidenceLevel } from "../enums";

export interface ConfidenceAssessment {
    score: number;

    level: ConfidenceLevel;

    evidenceCoverage: number;

    sourceCoverage: number;

    evidenceQuality: number;

    modelConfidence: number;

    missingEvidence: string[];

    conflictingEvidence: string[];

    calculatedAt: string;
}