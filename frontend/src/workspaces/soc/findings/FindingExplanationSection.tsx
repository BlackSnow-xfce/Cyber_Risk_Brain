import Alert from "@mui/material/Alert";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import AppButton from "@/ui/button/AppButton";

import type {
    FindingExplanationResult,
    FindingExplanationStatement,
} from "./FindingExplanation";
import { findingsDensity } from "./FindingsPresentationDensity";

interface FindingExplanationSectionProps {
    explanation: FindingExplanationResult | null;
    error: string | null;
    loading: boolean;
    onGenerate: () => void;
}

export default function FindingExplanationSection({
    explanation,
    error,
    loading,
    onGenerate,
}: FindingExplanationSectionProps) {
    const output = explanation?.model_output ?? null;

    return (
        <Stack spacing={2} data-findings-density="explanation" sx={{ "& .MuiChip-root": findingsDensity.chip, "& .MuiButton-root": findingsDensity.toolbarButton }}>
            <Divider />

            <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: "center", justifyContent: "space-between" }}
            >
                <Typography variant="subtitle2" sx={findingsDensity.sectionHeading}>AI Explanation</Typography>
                <AppButton onClick={onGenerate} disabled={loading}>
                    {loading ? "Generating…" : "Generate AI Explanation"}
                </AppButton>
            </Stack>

            {loading && (
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <CircularProgress size={18} />
                    <Typography variant="body2">Generating explanation…</Typography>
                </Stack>
            )}

            {error && <Alert severity="error">{error}</Alert>}

            {explanation && (
                <Stack spacing={2}>
                    <ExplanationMetadata explanation={explanation} />

                    {explanation.generation_status !== "GENERATED" && (
                        <Alert severity="warning">
                            Explanation status: {explanation.generation_status}
                        </Alert>
                    )}

                    {output && (
                        <>
                            <ExplanationGroup
                                title="Summary"
                                statements={[output.summary]}
                            />
                            <ExplanationGroup
                                title="Technical Reasoning"
                                statements={output.technical_reasoning}
                            />
                            <ExplanationGroup
                                title="Organizational Relevance"
                                statements={output.organizational_relevance}
                            />
                            <ExplanationGroup
                                title="Uncertainty"
                                statements={[output.uncertainty_statement]}
                            />
                        </>
                    )}

                    <Stack spacing={1}>
                        <Typography variant="subtitle2" sx={findingsDensity.subsectionHeading}>Missing Context</Typography>
                        <Stack
                            direction="row"
                            spacing={1}
                            useFlexGap
                            sx={{ flexWrap: "wrap" }}
                        >
                            {explanation.missing_context.length === 0 ? (
                                <Typography variant="body2" color="text.secondary" sx={findingsDensity.helpText}>
                                    None reported.
                                </Typography>
                            ) : (
                                explanation.missing_context.map((item) => (
                                    <Chip
                                        key={item.name}
                                        size="small"
                                        variant="outlined"
                                        label={`${item.name}: ${item.state}`}
                                    />
                                ))
                            )}
                        </Stack>
                    </Stack>
                </Stack>
            )}
        </Stack>
    );
}

function ExplanationMetadata({
    explanation,
}: {
    explanation: FindingExplanationResult;
}) {
    return (
        <Stack
            direction="row"
            spacing={1}
            useFlexGap
            sx={{ flexWrap: "wrap" }}
        >
            <Chip size="small" label={`Status ${explanation.generation_status}`} />
            <Chip size="small" label={`Provider ${explanation.provider_id ?? "Unavailable"}`} />
            <Chip size="small" label={`Model ${explanation.model_id ?? "Unavailable"}`} />
            <Chip size="small" label={`Contract ${explanation.input_contract_version}`} />
            {explanation.source_references.map((reference) => (
                <Chip
                    key={reference}
                    size="small"
                    variant="outlined"
                    label={`Source ${reference}`}
                />
            ))}
        </Stack>
    );
}

interface ExplanationGroupProps {
    title: string;
    statements: readonly FindingExplanationStatement[];
}

function ExplanationGroup({ title, statements }: ExplanationGroupProps) {
    if (statements.length === 0) {
        return null;
    }

    return (
        <Stack spacing={1}>
            <Typography variant="subtitle2" sx={findingsDensity.subsectionHeading}>{title}</Typography>
            {statements.map((statement, statementIndex) => (
                <Stack
                    key={`${title}-${statement.kind}-${statementIndex}`}
                    spacing={1}
                    sx={{ pl: 1.5, borderLeft: "2px solid", borderColor: "divider" }}
                >
                    <Chip
                        size="small"
                        variant="outlined"
                        label={statement.kind}
                        sx={{ alignSelf: "flex-start" }}
                    />
                    <Typography variant="body2" sx={findingsDensity.primaryValue}>{statement.text}</Typography>
                    {statement.basis_fact_ids.length > 0 && (
                        <Stack
                            direction="row"
                            spacing={0.5}
                            useFlexGap
                            sx={{ flexWrap: "wrap" }}
                        >
                            {statement.basis_fact_ids.map((factId) => (
                                <Chip
                                    key={factId}
                                    size="small"
                                    label={factId}
                                    variant="outlined"
                                />
                            ))}
                        </Stack>
                    )}
                </Stack>
            ))}
        </Stack>
    );
}
