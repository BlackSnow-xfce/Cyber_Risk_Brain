import { useWorkspace } from "@/hooks/useWorkspace";
import { useLocation } from "react-router-dom";

import IncidentResponseLayout from "./IncidentResponseLayout";
import IncidentResponseAreaPage from "./pages/IncidentResponseAreaPage";
import IncidentCommandCenterPage from "./pages/IncidentCommandCenterPage";
import {
    incidentResponseAreaRegistry,
    IncidentResponseOverviewPage,
    isIncidentResponseAreaId,
} from "./pages";

export default function IncidentResponseWorkspace() {
    const { activeNavigationItemId } = useWorkspace();
    const { pathname } = useLocation();

    if (/^\/incident-response\/incidents\/[^/]+\/command-center\/?$/.test(pathname)) {
        return <IncidentResponseLayout><IncidentCommandCenterPage /></IncidentResponseLayout>;
    }

    if (activeNavigationItemId === "command-center") {
        return <IncidentResponseLayout><IncidentCommandCenterPage /></IncidentResponseLayout>;
    }

    if (isIncidentResponseAreaId(activeNavigationItemId)) {
        const area = incidentResponseAreaRegistry[activeNavigationItemId];

        return (
            <IncidentResponseLayout>
                <IncidentResponseAreaPage
                    title={area.title}
                    description={area.description}
                />
            </IncidentResponseLayout>
        );
    }

    return (
        <IncidentResponseLayout>
            <IncidentResponseOverviewPage />
        </IncidentResponseLayout>
    );
}
