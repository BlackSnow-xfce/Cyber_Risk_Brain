import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

export default function AIExecutiveBrief() {
    return (
        <Panel component="section">
            <Typography variant="h6">
                Executive Briefing
            </Typography>

            <Typography color="text.secondary" sx={{ mt: 1 }}>
                No authorized executive briefing source is connected.
            </Typography>
        </Panel>
    );
}
