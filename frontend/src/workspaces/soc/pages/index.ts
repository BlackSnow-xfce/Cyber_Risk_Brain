import AssetsPage from "./AssetsPage";
import DashboardPage from "./DashboardPage";
import ExposurePage from "./ExposurePage";
import ExplainabilityPage from "./ExplainabilityPage";
import FindingsPage from "./FindingsPage";
import InvestigationsPage from "./InvestigationsPage";
import ThreatIntelligencePage from "./ThreatIntelligencePage";

export const socPageRegistry = {
    dashboard: DashboardPage,
    findings: FindingsPage,
    investigations: InvestigationsPage,
    assets: AssetsPage,
    "threat-intelligence": ThreatIntelligencePage,
    explainability: ExplainabilityPage,
    exposure: ExposurePage,
};

export type SOCPageId = keyof typeof socPageRegistry;

export const defaultSOCPageId: SOCPageId = "dashboard";

export function isSOCPageId(
    pageId: string | null,
): pageId is SOCPageId {
    return pageId !== null && pageId in socPageRegistry;
}
