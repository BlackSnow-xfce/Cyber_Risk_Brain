import { getFindingRiskContext, getFindings } from "@/workspaces/soc/findings/FindingsApiClient";
import type { FindingRiskContext } from "@/workspaces/soc/findings/FindingRiskContext";
import type { FindingSummary } from "@/workspaces/soc/findings/FindingSummary";

export interface RiskManagerRecord {
    finding: FindingSummary;
    context: FindingRiskContext | null;
    error: string | null;
}

export interface RiskManagerProjection {
    records: readonly RiskManagerRecord[];
    totalFindings: number;
    assessedFindings: number;
    criticalFindings: number;
    highFindings: number;
    unresolvedContexts: number;
    businessServices: readonly string[];
}

const riskBandRank: Readonly<Record<string, number>> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
    informational: 4,
};

export async function loadRiskManagerProjection(): Promise<RiskManagerProjection> {
    const findings = await getFindings();
    const results = await Promise.all(
        findings.map(async (finding): Promise<RiskManagerRecord> => {
            try {
                return {
                    finding,
                    context: await getFindingRiskContext(finding.id),
                    error: null,
                };
            } catch (error) {
                return {
                    finding,
                    context: null,
                    error: error instanceof Error ? error.message : "Risk context unavailable.",
                };
            }
        }),
    );

    const records = [...results].sort((left, right) => {
        const leftBand = left.context?.priority?.band ?? "unavailable";
        const rightBand = right.context?.priority?.band ?? "unavailable";
        const leftRank = riskBandRank[leftBand] ?? Number.MAX_SAFE_INTEGER;
        const rightRank = riskBandRank[rightBand] ?? Number.MAX_SAFE_INTEGER;
        if (leftRank !== rightRank) return leftRank - rightRank;
        return left.finding.title.localeCompare(right.finding.title);
    });

    const services = new Set<string>();
    let assessedFindings = 0;
    let criticalFindings = 0;
    let highFindings = 0;
    let unresolvedContexts = 0;

    for (const record of records) {
        const context = record.context;
        if (!context) {
            unresolvedContexts += 1;
            continue;
        }
        if (context.assessment.status === "ASSESSED") assessedFindings += 1;
        if (context.priority?.band === "critical") criticalFindings += 1;
        if (context.priority?.band === "high") highFindings += 1;
        if (context.business_context?.status === "RESOLVED" && context.business_context.business_service) {
            services.add(context.business_context.business_service);
        }
    }

    return {
        records,
        totalFindings: records.length,
        assessedFindings,
        criticalFindings,
        highFindings,
        unresolvedContexts,
        businessServices: [...services].sort(),
    };
}

export function technicalBand(record: RiskManagerRecord): string {
    return record.context?.priority?.band?.toUpperCase() ?? "NOT AVAILABLE";
}

export function riskScore(record: RiskManagerRecord): string {
    const score = record.context?.priority?.score ?? record.context?.assessment.score;
    return score === null || score === undefined ? "—" : String(score);
}

export function businessService(record: RiskManagerRecord): string {
    return record.context?.business_context?.business_service ?? "NOT AVAILABLE";
}

export function serviceCriticality(record: RiskManagerRecord): string {
    return record.context?.business_context?.service_criticality ?? "NOT AVAILABLE";
}

export function evidenceStatus(record: RiskManagerRecord): string {
    return record.context?.evidence_readiness.status ?? "UNAVAILABLE";
}

export function missingEvidence(record: RiskManagerRecord): readonly string[] {
    return record.context?.priority?.missing_requirements ?? record.context?.evidence_readiness.missing_requirements ?? [];
}
