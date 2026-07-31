export interface DecisionMetadata {
    id: string;

    key: string;

    version: number;

    tenantId: string;

    workspace: string;

    engineVersion: string;

    modelVersion: string;

    correlationId: string;

    createdAt: string;

    updatedAt: string;
}