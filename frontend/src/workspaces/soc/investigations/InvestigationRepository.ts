import type { Investigation } from "./Investigation";

export interface InvestigationRepository {
    getInvestigations: () => readonly Investigation[];
}
