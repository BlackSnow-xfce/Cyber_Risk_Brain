import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type {
    HuntHypothesisReference,
    HuntHypothesisReferenceResolution,
    HuntHypothesisResolvedReference,
} from "../HuntHypothesis";
import {
    getHuntHypotheses,
    getHuntHypothesisReferenceResolution,
    HuntHypothesisRequestError,
} from "../HuntHypothesisApiClient";
import type { HuntHypothesis } from "../HuntHypothesis";

export default function HuntHypothesesPage() {
    const [hypotheses, setHypotheses] = useState<HuntHypothesis[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [resolutions, setResolutions] = useState<
        Record<string, HuntHypothesisReferenceResolution>
    >({});
    const [resolutionLoading, setResolutionLoading] = useState<string | null>(null);
    const [resolutionErrors, setResolutionErrors] = useState<Record<string, string>>({});

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

    function resolveReferences(hypothesisId: string) {
        setResolutionLoading(hypothesisId);
        setResolutionErrors((current) => {
            const next = { ...current };
            delete next[hypothesisId];
            return next;
        });
        void getHuntHypothesisReferenceResolution(hypothesisId)
            .then((result) => {
                setResolutions((current) => ({ ...current, [hypothesisId]: result }));
            })
            .catch(() => {
                setResolutionErrors((current) => ({
                    ...current,
                    [hypothesisId]: "Reference resolution could not be loaded.",
                }));
            })
            .finally(() => setResolutionLoading(null));
    }

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
                                <Box>
                                    <Button
                                        size="small"
                                        variant="outlined"
                                        disabled={resolutionLoading === hypothesis.hypothesis_id}
                                        onClick={() => resolveReferences(hypothesis.hypothesis_id)}
                                    >
                                        {resolutionLoading === hypothesis.hypothesis_id
                                            ? "Resolving references…"
                                            : "Resolve references"}
                                    </Button>
                                </Box>
                                {resolutionErrors[hypothesis.hypothesis_id] && (
                                    <Alert severity="error">
                                        {resolutionErrors[hypothesis.hypothesis_id]}
                                    </Alert>
                                )}
                                {resolutions[hypothesis.hypothesis_id] && (
                                    <ResolutionList
                                        resolution={resolutions[hypothesis.hypothesis_id]}
                                    />
                                )}
                            </Stack>
                        </Panel>
                    ))}
                </Stack>
            )}
        </Stack>
    );
}

function ResolutionList({
    resolution,
}: {
    resolution: HuntHypothesisReferenceResolution;
}) {
    return (
        <Box component="section" aria-label="Reference resolution">
            <Typography variant="subtitle2">Reference resolution</Typography>
            <Typography variant="caption" color="text.secondary">
                Identity resolution does not establish evidence or the truth of this hypothesis.
            </Typography>
            <Stack spacing={1} sx={{ mt: 1 }}>
                {resolution.references.map((reference) => (
                    <ResolvedReference
                        key={`${reference.reference_type}:${reference.reference_id}`}
                        reference={reference}
                    />
                ))}
            </Stack>
        </Box>
    );
}

function ResolvedReference({ reference }: { reference: HuntHypothesisResolvedReference }) {
    return (
        <Box>
            <Typography variant="body2">
                {reference.reference_type}: {reference.reference_id}
            </Typography>
            <Typography variant="caption" color="text.secondary">
                {resolutionLabel(reference)}
            </Typography>
        </Box>
    );
}

function resolutionLabel(reference: HuntHypothesisResolvedReference): string {
    const labels = {
        resolved: "Resolved identity",
        not_found: "Exact identity not found",
        source_unavailable: "Authoritative source unavailable",
        unsupported: "Reference type unsupported",
    } as const;
    const sourceContext = [reference.authoritative_source, reference.source_reference]
        .filter((item): item is string => item !== null)
        .join(" · ");
    return sourceContext
        ? `${labels[reference.resolution_status]} · ${sourceContext}`
        : labels[reference.resolution_status];
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
