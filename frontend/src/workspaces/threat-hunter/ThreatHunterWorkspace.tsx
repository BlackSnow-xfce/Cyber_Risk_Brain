import { useWorkspace } from "@/hooks/useWorkspace";
import { useLocation } from "react-router-dom";

import ThreatHunterLayout from "./ThreatHunterLayout";
import ThreatHunterAreaPage from "./pages/ThreatHunterAreaPage";
import {
    isThreatHunterAreaId,
    HuntHypothesesPage,
    threatHunterAreaRegistry,
    ThreatHunterOverviewPage,
} from "./pages";
import { threatHunterNavigation } from "./navigation";

export default function ThreatHunterWorkspace() {
    const { activeNavigationItemId } = useWorkspace();
    const { pathname } = useLocation();
    const routeAreaId = threatHunterAreaIdFromPathname(pathname);
    const isOverviewRoute = /^\/threat-hunting\/?$/.test(pathname);
    const selectedAreaId = isOverviewRoute
        ? null
        : routeAreaId ?? activeNavigationItemId;

    if (isThreatHunterAreaId(selectedAreaId)) {
        const area = threatHunterAreaRegistry[selectedAreaId];

        return (
            <ThreatHunterLayout>
                {selectedAreaId === "hypotheses" ? (
                    <HuntHypothesesPage />
                ) : (
                    <ThreatHunterAreaPage
                        title={area.title}
                        description={area.description}
                    />
                )}
            </ThreatHunterLayout>
        );
    }

    return (
        <ThreatHunterLayout>
            <ThreatHunterOverviewPage />
        </ThreatHunterLayout>
    );
}

function threatHunterAreaIdFromPathname(
    pathname: string,
) {
    const navigationItem = threatHunterNavigation.find(
        (item) => item.route === pathname,
    );

    return navigationItem && isThreatHunterAreaId(navigationItem.id)
        ? navigationItem.id
        : null;
}
