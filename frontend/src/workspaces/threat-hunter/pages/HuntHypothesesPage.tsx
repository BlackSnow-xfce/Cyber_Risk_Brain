import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type {
    HuntHypothesisReference,
    HuntHypothesisReferenceResolution,
    HuntHypothesisResolvedReference,
    LocalOperatorSession,
} from "../HuntHypothesis";
import {
    activateHuntHypothesis,
    createHuntHypothesis,
    getHuntHypotheses,
    getHuntHypothesisReferenceResolution,
    getLocalOperatorSession,
    HuntHypothesisRequestError,
    LOCAL_OPERATOR_BOOTSTRAP_URL,
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
    const [operatorSession, setOperatorSession] = useState<LocalOperatorSession | null>(null);
    const [sessionLoading, setSessionLoading] = useState(true);
    const [creationOpen, setCreationOpen] = useState(false);
    const [creationError, setCreationError] = useState<string | null>(null);
    const [activationLoading, setActivationLoading] = useState<string | null>(null);
    const [activationErrors, setActivationErrors] = useState<Record<string, string>>({});
    const [activationRefreshWarnings, setActivationRefreshWarnings] = useState<
        Record<string, string>
    >({});
    const [activationSuccess, setActivationSuccess] = useState<string | null>(null);

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

    useEffect(() => {
        let current = true;
        void getLocalOperatorSession()
            .then((session) => {
                if (current) setOperatorSession(session);
            })
            .catch(() => {
                if (current) setOperatorSession(null);
            })
            .finally(() => {
                if (current) setSessionLoading(false);
            });
        return () => {
            current = false;
        };
    }, []);

    async function createHypothesis(input: Parameters<typeof createHuntHypothesis>[0]) {
        if (!operatorSession) return false;
        setCreationError(null);
        try {
            await createHuntHypothesis(input, operatorSession.csrf_token);
            setHypotheses(await getHuntHypotheses());
            setCreationOpen(false);
            return true;
        } catch {
            setCreationError("The hypothesis could not be created.");
            return false;
        }
    }

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

    async function activateHypothesis(hypothesisId: string) {
        if (!operatorSession) return;
        setActivationLoading(hypothesisId);
        setActivationSuccess(null);
        setActivationErrors((current) => {
            const next = { ...current };
            delete next[hypothesisId];
            return next;
        });
        try {
            const activated = await activateHuntHypothesis(
                hypothesisId,
                operatorSession.csrf_token,
            );
            setHypotheses((current) => current.map((hypothesis) =>
                hypothesis.hypothesis_id === activated.hypothesis_id
                    ? activated
                    : hypothesis
            ));
            setActivationSuccess(hypothesisId);
            setActivationRefreshWarnings((current) => {
                const next = { ...current };
                delete next[hypothesisId];
                return next;
            });
            try {
                setHypotheses(await getHuntHypotheses());
            } catch {
                setActivationRefreshWarnings((current) => ({
                    ...current,
                    [hypothesisId]:
                        "The hypothesis was activated, but the collection could not be refreshed.",
                }));
            }
        } catch {
            setActivationErrors((current) => ({
                ...current,
                [hypothesisId]: "The hypothesis could not be activated.",
            }));
        } finally {
            setActivationLoading(null);
        }
    }

    const canActivate = operatorSession?.granted_permissions.includes(
        "hunt_hypothesis:activate",
    ) ?? false;

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
                <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                    {!sessionLoading && operatorSession && (
                        <Button variant="contained" onClick={() => setCreationOpen(true)}>
                            Create hypothesis
                        </Button>
                    )}
                    {!sessionLoading && !operatorSession && (
                        <Button variant="outlined" href={LOCAL_OPERATOR_BOOTSTRAP_URL}>
                            Authenticate Local Operator
                        </Button>
                    )}
                </Stack>
            </Box>

            <Alert severity="info">
                A hypothesis is an unconfirmed investigative assumption and does not
                constitute evidence or confirmed compromise.
            </Alert>

            {creationError && <Alert severity="error">{creationError}</Alert>}

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
                                {hypothesis.status === "active" && (
                                    <Alert severity="info">
                                        Active means released for investigation only. It does not
                                        establish truth, evidence, successful execution or compromise.
                                    </Alert>
                                )}
                                <ReferenceList
                                    label="Unresolved target references"
                                    references={hypothesis.target_references}
                                />
                                <ReferenceList
                                    label="Unresolved threat references"
                                    references={hypothesis.threat_references}
                                />
                                <Stack direction="row" spacing={1}>
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
                                    {hypothesis.status === "draft" && canActivate && (
                                        <Button
                                            size="small"
                                            variant="contained"
                                            disabled={activationLoading === hypothesis.hypothesis_id}
                                            onClick={() => void activateHypothesis(hypothesis.hypothesis_id)}
                                        >
                                            {activationLoading === hypothesis.hypothesis_id
                                                ? "Activating..."
                                                : "Activate for investigation"}
                                        </Button>
                                    )}
                                </Stack>
                                {activationErrors[hypothesis.hypothesis_id] && (
                                    <Alert severity="error">
                                        {activationErrors[hypothesis.hypothesis_id]}
                                    </Alert>
                                )}
                                {activationSuccess === hypothesis.hypothesis_id && (
                                    <Alert severity="success">
                                        The hypothesis is active for investigation. This is not
                                        evidence or confirmation of compromise.
                                    </Alert>
                                )}
                                {activationRefreshWarnings[hypothesis.hypothesis_id] && (
                                    <Alert severity="warning">
                                        {activationRefreshWarnings[hypothesis.hypothesis_id]}
                                    </Alert>
                                )}
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
            <CreateHypothesisDialog
                open={creationOpen}
                onClose={() => {
                    setCreationOpen(false);
                    setCreationError(null);
                }}
                onSubmit={createHypothesis}
            />
        </Stack>
    );
}

const TARGET_TYPES = ["asset", "service", "finding"] as const;
const THREAT_TYPES = ["cve", "threat_intelligence", "technique", "tactic"] as const;

function CreateHypothesisDialog({
    open,
    onClose,
    onSubmit,
}: {
    open: boolean;
    onClose: () => void;
    onSubmit: (input: Parameters<typeof createHuntHypothesis>[0]) => Promise<boolean>;
}) {
    const [title, setTitle] = useState("");
    const [statement, setStatement] = useState("");
    const [rationale, setRationale] = useState("");
    const [targetReferences, setTargetReferences] = useState<HuntHypothesisReference[]>([]);
    const [threatReferences, setThreatReferences] = useState<HuntHypothesisReference[]>([]);
    const [targetType, setTargetType] = useState<(typeof TARGET_TYPES)[number]>("asset");
    const [targetId, setTargetId] = useState("");
    const [threatType, setThreatType] = useState<(typeof THREAT_TYPES)[number]>("cve");
    const [threatId, setThreatId] = useState("");
    const [validationError, setValidationError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    function addReference(
        reference: HuntHypothesisReference,
        references: HuntHypothesisReference[],
        update: (value: HuntHypothesisReference[]) => void,
        clear: () => void,
    ) {
        const normalized = { ...reference, reference_id: reference.reference_id.trim() };
        if (!normalized.reference_id) {
            setValidationError("Reference IDs must not be empty.");
            return;
        }
        if (references.some((item) =>
            item.reference_type === normalized.reference_type &&
            item.reference_id === normalized.reference_id
        )) {
            setValidationError("Duplicate reference pointers are not allowed.");
            return;
        }
        setValidationError(null);
        update([...references, normalized]);
        clear();
    }

    function reset() {
        setTitle("");
        setStatement("");
        setRationale("");
        setTargetReferences([]);
        setThreatReferences([]);
        setTargetId("");
        setThreatId("");
        setValidationError(null);
    }

    async function submit() {
        if (!title.trim() || !statement.trim() || !rationale.trim()) {
            setValidationError("Title, statement and rationale are required.");
            return;
        }
        setSubmitting(true);
        try {
            const succeeded = await onSubmit({
                title: title.trim(),
                statement: statement.trim(),
                rationale: rationale.trim(),
                target_references: targetReferences,
                threat_references: threatReferences,
            });
            if (succeeded) reset();
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
            <DialogTitle>Create hunt hypothesis</DialogTitle>
            <DialogContent>
                <Stack spacing={2} sx={{ pt: 1 }}>
                    <Alert severity="warning">
                        A hypothesis is an unconfirmed investigative assumption and does
                        not constitute evidence or confirmed compromise.
                    </Alert>
                    <TextField label="Title" slotProps={{ htmlInput: { "aria-label": "Title" } }} value={title} onChange={(event) => setTitle(event.target.value)} required />
                    <TextField label="Statement" slotProps={{ htmlInput: { "aria-label": "Statement" } }} value={statement} onChange={(event) => setStatement(event.target.value)} required multiline minRows={2} />
                    <TextField label="Rationale" slotProps={{ htmlInput: { "aria-label": "Rationale" } }} value={rationale} onChange={(event) => setRationale(event.target.value)} required multiline minRows={2} />
                    <ReferenceEditor
                        label="Target references"
                        types={TARGET_TYPES}
                        selectedType={targetType}
                        referenceId={targetId}
                        references={targetReferences}
                        onTypeChange={(value) => setTargetType(value as (typeof TARGET_TYPES)[number])}
                        onIdChange={setTargetId}
                        onAdd={() => addReference(
                            { reference_type: targetType, reference_id: targetId },
                            targetReferences,
                            setTargetReferences,
                            () => setTargetId(""),
                        )}
                        onRemove={(index) => setTargetReferences(targetReferences.filter((_, current) => current !== index))}
                    />
                    <ReferenceEditor
                        label="Threat references"
                        types={THREAT_TYPES}
                        selectedType={threatType}
                        referenceId={threatId}
                        references={threatReferences}
                        onTypeChange={(value) => setThreatType(value as (typeof THREAT_TYPES)[number])}
                        onIdChange={setThreatId}
                        onAdd={() => addReference(
                            { reference_type: threatType, reference_id: threatId },
                            threatReferences,
                            setThreatReferences,
                            () => setThreatId(""),
                        )}
                        onRemove={(index) => setThreatReferences(threatReferences.filter((_, current) => current !== index))}
                    />
                    {validationError && <Alert severity="error">{validationError}</Alert>}
                </Stack>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => { reset(); onClose(); }}>Cancel</Button>
                <Button variant="contained" disabled={submitting} onClick={() => void submit()}>
                    {submitting ? "Creatingâ€¦" : "Create draft"}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

function ReferenceEditor({
    label, types, selectedType, referenceId, references,
    onTypeChange, onIdChange, onAdd, onRemove,
}: {
    label: string;
    types: readonly string[];
    selectedType: string;
    referenceId: string;
    references: HuntHypothesisReference[];
    onTypeChange: (value: string) => void;
    onIdChange: (value: string) => void;
    onAdd: () => void;
    onRemove: (index: number) => void;
}) {
    return (
        <Box>
            <Typography variant="subtitle2">{label}</Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1 }}>
                <TextField select label="Reference type" value={selectedType} onChange={(event) => onTypeChange(event.target.value)} sx={{ minWidth: 190 }}>
                    {types.map((type) => <MenuItem key={type} value={type}>{type}</MenuItem>)}
                </TextField>
                <TextField label="Reference ID" slotProps={{ htmlInput: { "aria-label": "Reference ID" } }} value={referenceId} onChange={(event) => onIdChange(event.target.value)} fullWidth />
                <Button variant="outlined" onClick={onAdd}>Add</Button>
            </Stack>
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
                {references.map((reference, index) => (
                    <Chip
                        key={`${reference.reference_type}:${reference.reference_id}`}
                        label={`${reference.reference_type}: ${reference.reference_id}`}
                        onDelete={() => onRemove(index)}
                    />
                ))}
            </Stack>
        </Box>
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
