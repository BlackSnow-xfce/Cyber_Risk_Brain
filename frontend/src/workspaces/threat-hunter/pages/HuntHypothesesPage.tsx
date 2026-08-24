import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { HuntHypothesisReference } from "../HuntHypothesis";
import {
    getHuntHypotheses,
    HuntHypothesisRequestError,
} from "../HuntHypothesisApiClient";
import type { HuntHypothesis } from "../HuntHypothesis";

export default function HuntHypothesesPage() {
    const [hypotheses, setHypotheses] = useState<HuntHypothesis[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let current = true;
        void getHuntHypotheses()
            .then((items) => {
                if (current) setHypotheses(items);
            })
            .catch((requestError: unknown) => {
                if (!current) return;
                setError(
                    requestError instanceof HuntHypothesisRequestError &&
                        requestError.status === 503
                        ? "The Hunt Hypothesis repository is not configured."
                        : "Hunt hypotheses could not be loaded.",
                );
            })
            .finally(() => {
                if (current) setLoading(false);
            });
        return () => {
            current = false;
        };
    }, []);

    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="warning.main">
                    Threat Hunter
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Hunt Hypotheses
                </Typography>
                <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 720 }}>
                    Review persisted, testable assumptions before collecting supporting evidence.
                </Typography>
            </Box>

            {loading && (
                <Panel component="section">
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                        <CircularProgress size={18} />
                        <Typography>Loading hunt hypotheses…</Typography>
                    </Stack>
                </Panel>
            )}
            {!loading && error && <Alert severity="error">{error}</Alert>}
            {!loading && !error && hypotheses.length === 0 && (
                <Alert severity="info">No persisted hunt hypotheses are available.</Alert>
            )}
            {!loading && !error && hypotheses.length > 0 && (
                <Stack spacing={2} component="section" aria-label="Hunt hypotheses">
                    <Alert severity="info">
                        Hypotheses are unconfirmed assumptions. References below are unresolved pointers.
                    </Alert>
                    {hypotheses.map((hypothesis) => (
                        <Panel key={hypothesis.hypothesis_id} component="article">
                            <Stack spacing={1.5}>
                                <Stack
                                    direction={{ xs: "column", sm: "row" }}
                                    spacing={1}
                                    sx={{ justifyContent: "space-between" }}
                                >
                                    <Box>
                                        <Typography variant="h6">{hypothesis.title}</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {hypothesis.hypothesis_id}
                                        </Typography>
                                    </Box>
                                    <Chip label={hypothesis.status} size="small" variant="outlined" />
                                </Stack>
                                <Typography>{hypothesis.statement}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Rationale: {hypothesis.rationale}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    Created {formatTimestamp(hypothesis.created_at)} by {hypothesis.created_by}
                                </Typography>
                                <ReferenceList
                                    label="Unresolved target references"
                                    references={hypothesis.target_references}
                                />
                                <ReferenceList
                                    label="Unresolved threat references"
                                    references={hypothesis.threat_references}
                                />
                            </Stack>
                        </Panel>
                    ))}
                </Stack>
            )}
        </Stack>
    );
}

interface ReferenceListProps {
    label: string;
    references: HuntHypothesisReference[];
}

function ReferenceList({ label, references }: ReferenceListProps) {
    return (
        <Box>
            <Typography variant="caption" color="text.secondary">
                {label}
            </Typography>
            {references.length === 0 ? (
                <Typography variant="body2">None</Typography>
            ) : (
                <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: "wrap" }}>
                    {references.map((reference) => (
                        <Chip
                            key={`${reference.reference_type}:${reference.reference_id}`}
                            label={`${reference.reference_type}: ${reference.reference_id}`}
                            size="small"
                        />
                    ))}
                </Stack>
            )}
        </Box>
    );
}

function formatTimestamp(value: string): string {
    const timestamp = new Date(value);
    return Number.isNaN(timestamp.getTime()) ? value : timestamp.toLocaleString();
}
