import type { Finding } from "./Finding";

export interface FindingRepository {
    getFindings: () => readonly Finding[];
}
