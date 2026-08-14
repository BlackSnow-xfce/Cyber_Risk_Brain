import { useWorkspace } from "@/hooks/useWorkspace";

import ThreatHunterLayout from "./ThreatHunterLayout";
import ThreatHunterAreaPage from "./pages/ThreatHunterAreaPage";
import {
    isThreatHunterAreaId,
    threatHunterAreaRegistry,
    ThreatHunterOverviewPage,
} from "./pages";

export default function ThreatHunterWorkspace() {
    const { activeNavigationItemId } = useWorkspace();

    if (isThreatHunterAreaId(activeNavigationItemId)) {
        const area = threatHunterAreaRegistry[activeNavigationItemId];

        return (
            <ThreatHunterLayout>
                <ThreatHunterAreaPage
                    title={area.title}
                    description={area.description}
                />
            </ThreatHunterLayout>
        );
    }

    return (
        <ThreatHunterLayout>
            <ThreatHunterOverviewPage />
        </ThreatHunterLayout>
    );
}
