import Stack from "@mui/material/Stack";

import ExecutiveDashboardLayout from "../ExecutiveDashboardLayout";

import AIExecutiveBrief from "../widgets/AIExecutiveBrief";
import EnterpriseRisk from "../widgets/EnterpriseRisk";
import BusinessImpact from "../widgets/BusinessImpact";

export default function ExecutiveOverviewPage() {
    return (
        <Stack spacing={3}>
            <AIExecutiveBrief />

            <ExecutiveDashboardLayout>
                <EnterpriseRisk />

                <BusinessImpact />
            </ExecutiveDashboardLayout>
        </Stack>
    );
}