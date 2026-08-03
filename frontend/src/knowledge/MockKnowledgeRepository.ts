import type { KnowledgeItem } from "./KnowledgeItem";
import type { KnowledgeRepository } from "./KnowledgeRepository";

const knowledgeItems: readonly KnowledgeItem[] = [
    {
        id: "knowledge-mitre-t1190",
        type: "MITRE_TECHNIQUE",
        source: "MITRE",
        title: "Exploit Public-Facing Application",
        description:
            "Adversaries may exploit weaknesses in internet-facing systems to gain initial access.",
        reference: {
            externalId: "T1190",
            url: "https://attack.mitre.org/techniques/T1190/",
            version: "Enterprise",
            publishedAt: "2020-01-30T00:00:00.000Z",
        },
        confidence: 100,
        tags: ["initial-access", "public-facing", "exploitation"],
    },
    {
        id: "knowledge-cve-2024-3400",
        type: "CVE",
        source: "NVD",
        title: "CVE-2024-3400",
        description:
            "A command injection vulnerability affects specific PAN-OS GlobalProtect configurations.",
        reference: {
            externalId: "CVE-2024-3400",
            url: "https://nvd.nist.gov/vuln/detail/CVE-2024-3400",
            version: "1.0",
            publishedAt: "2024-04-12T00:00:00.000Z",
        },
        confidence: 100,
        tags: ["cve", "command-injection", "network-security"],
    },
    {
        id: "knowledge-kev-cve-2024-3400",
        type: "KEV",
        source: "CISA",
        title: "Known Exploited Vulnerability Entry",
        description:
            "CVE-2024-3400 is cataloged as a vulnerability with evidence of active exploitation.",
        reference: {
            externalId: "CVE-2024-3400",
            url: "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            version: "2024",
            publishedAt: "2024-04-12T00:00:00.000Z",
        },
        confidence: 100,
        tags: ["kev", "active-exploitation", "cisa"],
    },
    {
        id: "knowledge-epss-cve-2024-3400",
        type: "EPSS",
        source: "FIRST",
        title: "Exploit Prediction Context",
        description:
            "EPSS provides a probability-based context for exploitation activity associated with the vulnerability.",
        reference: {
            externalId: "CVE-2024-3400",
            url: "https://www.first.org/epss/",
            version: "3",
            publishedAt: "2024-04-13T00:00:00.000Z",
        },
        confidence: 95,
        tags: ["epss", "exploit-probability", "vulnerability"],
    },
    {
        id: "knowledge-asset-business-critical",
        type: "ASSET_CLASSIFICATION",
        source: "Asset Inventory",
        title: "Business-Critical Asset Classification",
        description:
            "Assets supporting essential digital services are classified as business critical.",
        reference: {
            externalId: "ASSET-CLASS-BUSINESS-CRITICAL",
            url: "urn:predatorai:knowledge:asset-classification",
            version: "1.0",
            publishedAt: "2026-01-01T00:00:00.000Z",
        },
        confidence: 100,
        tags: ["asset", "business-critical", "classification"],
    },
    {
        id: "knowledge-detection-public-exploit",
        type: "DETECTION_RULE",
        source: "Internal",
        title: "Public Exploit Exposure Detection",
        description:
            "Detects externally reachable assets associated with known exploitation context.",
        reference: {
            externalId: "DET-PUBLIC-EXPLOIT-001",
            url: "urn:predatorai:knowledge:detection-rule:public-exploit",
            version: "1.0",
            publishedAt: "2026-02-01T00:00:00.000Z",
        },
        confidence: 96,
        tags: ["detection", "external-exposure", "exploit"],
    },
    {
        id: "knowledge-playbook-critical-exposure",
        type: "PLAYBOOK",
        source: "Internal",
        title: "Critical External Exposure Review",
        description:
            "Defines the documented review procedure for critical internet-facing exposure.",
        reference: {
            externalId: "PB-CRITICAL-EXPOSURE-001",
            url: "urn:predatorai:knowledge:playbook:critical-exposure",
            version: "1.0",
            publishedAt: "2026-02-15T00:00:00.000Z",
        },
        confidence: 100,
        tags: ["playbook", "exposure", "soc-review"],
    },
];

export class MockKnowledgeRepository implements KnowledgeRepository {
    getKnowledgeItems(): readonly KnowledgeItem[] {
        return knowledgeItems;
    }
}

export const knowledgeRepository: KnowledgeRepository =
    new MockKnowledgeRepository();
