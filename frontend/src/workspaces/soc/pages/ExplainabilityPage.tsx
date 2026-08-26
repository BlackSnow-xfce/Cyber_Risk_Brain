import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Component, type ErrorInfo, type ReactNode } from "react";

import ExplainabilityWorkspace from "../explainability/ExplainabilityWorkspace";

export default function ExplainabilityPage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">Explainability</Typography>
                <Typography color="text.secondary">
                    Analyze the complete cyber-reasoning decision chain.
                </Typography>
            </Stack>
            <ExplainabilityRenderBoundary>
                <ExplainabilityWorkspace />
            </ExplainabilityRenderBoundary>
        </Stack>
    );
}

interface ExplainabilityRenderBoundaryProps {
    children: ReactNode;
}

interface ExplainabilityRenderBoundaryState {
    failed: boolean;
}

class ExplainabilityRenderBoundary extends Component<
    ExplainabilityRenderBoundaryProps,
    ExplainabilityRenderBoundaryState
> {
    state: ExplainabilityRenderBoundaryState = { failed: false };

    static getDerivedStateFromError(): ExplainabilityRenderBoundaryState {
        return { failed: true };
    }

    componentDidCatch(_error: Error, _info: ErrorInfo) {
        // The controlled state intentionally does not expose internal errors.
    }

    render() {
        if (this.state.failed) {
            return (
                <Alert severity="error" aria-label="Explainability error">
                    Explainability could not be rendered. No explanation or
                    security conclusion was generated.
                </Alert>
            );
        }
        return this.props.children;
    }
}
