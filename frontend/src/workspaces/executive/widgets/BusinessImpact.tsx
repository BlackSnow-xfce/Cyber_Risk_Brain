import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

export default function BusinessImpact() {
    return (
        <Panel component="section">
            <Typography variant="h6">
                Business Impact
            </Typography>

            <Typography color="text.secondary" sx={{ mt: 1 }}>
                No authorized business-impact source is connected.
            </Typography>
        </Panel>
    );
}
