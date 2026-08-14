import { useWorkspace } from "@/hooks/useWorkspace";

import IncidentResponseLayout from "./IncidentResponseLayout";
import IncidentResponseAreaPage from "./pages/IncidentResponseAreaPage";
import {
    incidentResponseAreaRegistry,
    IncidentResponseOverviewPage,
    isIncidentResponseAreaId,
} from "./pages";

export default function IncidentResponseWorkspace() {
    const { activeNavigationItemId } = useWorkspace();

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
