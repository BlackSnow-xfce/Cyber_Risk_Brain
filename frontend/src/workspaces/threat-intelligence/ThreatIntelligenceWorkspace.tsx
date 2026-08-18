import { useWorkspace } from "@/hooks/useWorkspace";

import ThreatIntelligenceLayout from "./ThreatIntelligenceLayout";
import ThreatIntelligenceExplorerPage from "./pages/ThreatIntelligenceExplorerPage";
import ThreatIntelligenceOverviewPage from "./pages/ThreatIntelligenceOverviewPage";
import ThreatIntelligenceEnvironmentPage from "./pages/ThreatIntelligenceEnvironmentPage";

export default function ThreatIntelligenceWorkspace() {
    const { activeNavigationItemId } = useWorkspace();

    let page = <ThreatIntelligenceOverviewPage />;

    if (activeNavigationItemId === "explorer") {
        page = <ThreatIntelligenceExplorerPage />;
    } else if (activeNavigationItemId === "our-environment") {
        page = <ThreatIntelligenceEnvironmentPage />;
    }

    return <ThreatIntelligenceLayout>{page}</ThreatIntelligenceLayout>;
}
