import { useLocation } from "react-router-dom";
import { useWorkspace } from "@/hooks/useWorkspace";

import AdministratorLayout from "./AdministratorLayout";
import AdministratorAreaPage from "./pages/AdministratorAreaPage";
import {
    administratorAreaRegistry,
    AdministratorOverviewPage,
    AIModelGovernancePage,
    isAdministratorAreaId,
} from "./pages";

export default function AdministratorWorkspace() {
    const { activeNavigationItemId } = useWorkspace();
    const { pathname } = useLocation();

    if (pathname === "/administration/ai-models") {
        return (
            <AdministratorLayout>
                <AIModelGovernancePage />
            </AdministratorLayout>
        );
    }

    if (isAdministratorAreaId(activeNavigationItemId)) {
        const area = administratorAreaRegistry[activeNavigationItemId];

        return (
            <AdministratorLayout>
                <AdministratorAreaPage
                    title={area.title}
                    description={area.description}
                />
            </AdministratorLayout>
        );
    }

    return (
        <AdministratorLayout>
            <AdministratorOverviewPage />
        </AdministratorLayout>
    );
}
