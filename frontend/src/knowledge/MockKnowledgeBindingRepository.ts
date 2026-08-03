import type { KnowledgeBinding } from "./KnowledgeBinding";
import type { KnowledgeBindingRepository } from "./KnowledgeBindingRepository";

const knowledgeBindings: readonly KnowledgeBinding[] = [
    {
        id: "binding-mitre-t1190-finding-001",
        knowledgeItemId: "knowledge-mitre-t1190",
        entityId: "finding-001",
        type: "SUPPORTS",
        strength: "Strong",
        confidence: 98,
        rationale:
            "The finding concerns exploitation of an internet-facing application.",
        createdAt: "2026-08-03T12:00:00.000Z",
    },
    {
        id: "binding-cve-2024-3400-finding-001",
        knowledgeItemId: "knowledge-cve-2024-3400",
        entityId: "finding-001",
        evidenceId: "evidence-finding-001-cve",
        type: "EXPLAINS",
        strength: "Strong",
        confidence: 100,
        rationale:
            "The CVE record explains the vulnerability evidence associated with the finding.",
        createdAt: "2026-08-03T12:01:00.000Z",
    },
    {
        id: "binding-kev-cve-2024-3400-finding-001",
        knowledgeItemId: "knowledge-kev-cve-2024-3400",
        entityId: "finding-001",
        evidenceId: "evidence-finding-001-cve",
        type: "ENRICHES",
        strength: "Strong",
        confidence: 100,
        rationale:
            "The KEV entry adds confirmed exploitation context to the vulnerability evidence.",
        createdAt: "2026-08-03T12:02:00.000Z",
    },
    {
        id: "binding-epss-cve-2024-3400-finding-001",
        knowledgeItemId: "knowledge-epss-cve-2024-3400",
        entityId: "finding-001",
        evidenceId: "evidence-finding-001-cve",
        type: "ENRICHES",
        strength: "Medium",
        confidence: 95,
        rationale:
            "The EPSS context enriches the vulnerability evidence with exploitation probability context.",
        createdAt: "2026-08-03T12:03:00.000Z",
    },
    {
        id: "binding-business-critical-asset-001",
        knowledgeItemId: "knowledge-asset-business-critical",
        entityId: "asset-001",
        evidenceId: "evidence-asset-001-inventory",
        type: "CLASSIFIES",
        strength: "Strong",
        confidence: 100,
        rationale:
            "The asset inventory evidence identifies the asset as supporting critical digital services.",
        createdAt: "2026-08-03T12:04:00.000Z",
    },
    {
        id: "binding-detection-investigation-001",
        knowledgeItemId: "knowledge-detection-public-exploit",
        entityId: "investigation-001",
        evidenceId: "evidence-investigation-001-scan",
        type: "MAPS_TO",
        strength: "Medium",
        confidence: 96,
        rationale:
            "The detection rule maps to the vulnerability scan evidence in the investigation.",
        createdAt: "2026-08-03T12:05:00.000Z",
    },
    {
        id: "binding-playbook-investigation-001",
        knowledgeItemId: "knowledge-playbook-critical-exposure",
        entityId: "investigation-001",
        type: "REQUIRES_VALIDATION",
        strength: "Medium",
        confidence: 90,
        rationale:
            "The investigation context is relevant to the playbook but requires analyst validation before use.",
        createdAt: "2026-08-03T12:06:00.000Z",
    },
    {
        id: "binding-kev-threat-001",
        knowledgeItemId: "knowledge-kev-cve-2024-3400",
        entityId: "threat-001",
        evidenceId: "evidence-threat-001-kev",
        type: "ENRICHES",
        strength: "Strong",
        confidence: 100,
        rationale:
            "The KEV entry enriches the threat intelligence with confirmed exploitation context.",
        createdAt: "2026-08-03T12:07:00.000Z",
    },
    {
        id: "binding-mitre-t1190-exposure-001",
        knowledgeItemId: "knowledge-mitre-t1190",
        entityId: "exposure-001",
        evidenceId: "evidence-exposure-001-facing",
        type: "SUPPORTS",
        strength: "Strong",
        confidence: 97,
        rationale:
            "The MITRE technique is relevant to the confirmed public application exposure.",
        createdAt: "2026-08-03T12:08:00.000Z",
    },
];

export class MockKnowledgeBindingRepository
    implements KnowledgeBindingRepository
{
    getBindings(): readonly KnowledgeBinding[] {
        return knowledgeBindings;
    }

    getBindingsByEntityId(entityId: string): readonly KnowledgeBinding[] {
        return knowledgeBindings.filter(
            (binding) => binding.entityId === entityId,
        );
    }

    getBindingsByKnowledgeItemId(
        knowledgeItemId: string,
    ): readonly KnowledgeBinding[] {
        return knowledgeBindings.filter(
            (binding) => binding.knowledgeItemId === knowledgeItemId,
        );
    }
}

export const knowledgeBindingRepository: KnowledgeBindingRepository =
    new MockKnowledgeBindingRepository();
