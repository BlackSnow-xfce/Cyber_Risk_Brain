import { useWorkspace } from "@/hooks/useWorkspace";
import { useLocation } from "react-router-dom";

import ThreatIntelligenceLayout from "./ThreatIntelligenceLayout";
import ThreatIntelligenceExplorerPage from "./pages/ThreatIntelligenceExplorerPage";
import ThreatIntelligenceOverviewPage from "./pages/ThreatIntelligenceOverviewPage";
import ThreatIntelligenceEnvironmentPage from "./pages/ThreatIntelligenceEnvironmentPage";

export default function ThreatIntelligenceWorkspace() {
    const { activeNavigationItemId } = useWorkspace();
    const { pathname } = useLocation();
    const routeAreaId = areaIdFromPathname(pathname);
    const isOverviewRoute = /^\/threat-intelligence\/?$/.test(pathname);

    let page = <ThreatIntelligenceOverviewPage />;
    const selectedAreaId = isOverviewRoute ? null : routeAreaId ?? activeNavigationItemId;

    if (selectedAreaId === "explorer") {
        page = <ThreatIntelligenceExplorerPage />;
    } else if (selectedAreaId === "our-environment") {
        page = <ThreatIntelligenceEnvironmentPage />;
    }

    return <ThreatIntelligenceLayout>{page}</ThreatIntelligenceLayout>;
}

function areaIdFromPathname(pathname: string): string | null {
    if (/^\/threat-intelligence\/explorer\/?$/.test(pathname)) return "explorer";
    if (/^\/threat-intelligence\/environment\/?$/.test(pathname)) return "our-environment";
    return null;
}
