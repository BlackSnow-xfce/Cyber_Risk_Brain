import { useWorkspace } from "@/hooks/useWorkspace";

import RiskManagerLayout from "./RiskManagerLayout";
import RiskManagerAreaPage from "./pages/RiskManagerAreaPage";
import {
    isRiskManagerAreaId,
    riskManagerAreaRegistry,
    RiskManagerOverviewPage,
} from "./pages";

export default function RiskManagerWorkspace() {
    const { activeNavigationItemId } = useWorkspace();

    if (isRiskManagerAreaId(activeNavigationItemId)) {
        const area = riskManagerAreaRegistry[activeNavigationItemId];

        return (
            <RiskManagerLayout>
                <RiskManagerAreaPage
                    title={area.title}
                    description={area.description}
                />
            </RiskManagerLayout>
        );
    }

    return (
        <RiskManagerLayout>
            <RiskManagerOverviewPage />
        </RiskManagerLayout>
    );
}
