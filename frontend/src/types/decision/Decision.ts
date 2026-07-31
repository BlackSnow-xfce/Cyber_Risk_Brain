import type {
    DecisionMetadata,
    DecisionStatus,
} from "./metadata";

import type {
    DecisionSummary,
} from "./summary";

import type {
    DecisionRecommendation,
} from "./recommendation";

import type {
    DecisionContext,
} from "./context";

import type {
    RiskAssessment,
    ConfidenceAssessment,
} from "./risk";

import type {
    EvidenceCollection,
} from "./evidence";

import type {
    Explainability,
} from "./explainability";

import type {
    BusinessImpact,
} from "./impact";

import type {
    DecisionActions,
} from "./actions";

import type {
    DecisionTimeline,
} from "./timeline";

import type {
    DecisionReferences,
} from "./references";

import type {
    DecisionAudit,
} from "./audit";

export interface Decision {
    metadata: DecisionMetadata;

    status: DecisionStatus;

    summary: DecisionSummary;

    recommendation: DecisionRecommendation;

    context: DecisionContext;

    risk: RiskAssessment;

    confidence: ConfidenceAssessment;

    evidence: EvidenceCollection;

    explainability: Explainability;

    impact: BusinessImpact;

    actions: DecisionActions;

    timeline: DecisionTimeline;

    references: DecisionReferences;

    audit: DecisionAudit;
}