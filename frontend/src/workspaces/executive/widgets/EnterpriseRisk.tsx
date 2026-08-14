import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

export default function EnterpriseRisk() {
    return (
        <Panel component="section">
            <Typography variant="h6">
                Enterprise Risk
            </Typography>

            <Typography color="text.secondary" sx={{ mt: 1 }}>
                No authorized enterprise risk source is connected.
            </Typography>
        </Panel>
    );
}
