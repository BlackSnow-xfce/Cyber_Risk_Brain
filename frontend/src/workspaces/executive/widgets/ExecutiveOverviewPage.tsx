import Stack from "@mui/material/Stack";

import AIExecutiveBrief from "../widgets/AIExecutiveBrief";
import EnterpriseRisk from "../widgets/EnterpriseRisk";

export default function ExecutiveOverviewPage() {
    return (
        <Stack spacing={3}>
            <AIExecutiveBrief />

            <EnterpriseRisk />
        </Stack>
    );
}