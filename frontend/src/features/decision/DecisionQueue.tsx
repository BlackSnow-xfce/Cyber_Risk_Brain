import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

export default function DecisionQueue() {
    return (
        <Panel>
            <Stack spacing={2}>
                <Typography variant="h6">
                    Decision Queue
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    Waiting for decisions from the Decision Engine.
                </Typography>
            </Stack>
        </Panel>
    );
}