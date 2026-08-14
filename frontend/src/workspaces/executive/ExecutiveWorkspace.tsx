import { useWorkspace } from "@/hooks/useWorkspace";

import ExecutiveLayout from "./ExecutiveLayout";
import ExecutiveAreaPage from "./pages/ExecutiveAreaPage";
import {
    executiveAreaRegistry,
    ExecutiveOverviewPage,
    isExecutiveAreaId,
} from "./pages";

export default function ExecutiveWorkspace() {
    const { activeNavigationItemId } = useWorkspace();

    if (isExecutiveAreaId(activeNavigationItemId)) {
        const area = executiveAreaRegistry[activeNavigationItemId];

        return (
            <ExecutiveLayout>
                <ExecutiveAreaPage
                    title={area.title}
                    description={area.description}
                />
            </ExecutiveLayout>
        );
    }

    return (
        <ExecutiveLayout>
            <ExecutiveOverviewPage />
        </ExecutiveLayout>
    );
}
