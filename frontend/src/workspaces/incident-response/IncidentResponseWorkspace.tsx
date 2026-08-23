import { useLocation } from "react-router-dom";

import IncidentResponseLayout from "./IncidentResponseLayout";
import IncidentResponseAreaPage from "./pages/IncidentResponseAreaPage";
import IncidentCommandCenterPage from "./pages/IncidentCommandCenterPage";
import {
    incidentResponseAreaRegistry,
    IncidentResponseOverviewPage,
    IncidentQueuePage,
    isIncidentResponseAreaId,
} from "./pages";

export default function IncidentResponseWorkspace() {
    const { pathname } = useLocation();

    if (/^\/incident-response\/incidents\/[^/]+\/command-center\/?$/.test(pathname)) {
        return <IncidentResponseLayout><IncidentCommandCenterPage /></IncidentResponseLayout>;
    }

    const areaId = incidentResponseAreaFromPath(pathname);
    if (areaId === "incident-queue") {
        return <IncidentResponseLayout><IncidentQueuePage /></IncidentResponseLayout>;
    }
    if (areaId && isIncidentResponseAreaId(areaId)) {
        const area = incidentResponseAreaRegistry[areaId];

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

function incidentResponseAreaFromPath(pathname: string): string | null {
    if (/^\/incident-response\/queue\/?$/.test(pathname)) return "incident-queue";
    if (/^\/incident-response\/?$/.test(pathname)) return "overview";
    const match = pathname.match(/^\/incident-response\/([^/]+)\/?$/);
    return match?.[1] ?? null;
}
