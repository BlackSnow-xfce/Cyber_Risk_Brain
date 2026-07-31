export interface ThreatContext {
    cves: string[];

    kevListed: boolean;

    epss?: number;

    cvss?: number;

    attackPaths: string[];

    mitreTechniques: string[];

    exploitAvailable: boolean;
}