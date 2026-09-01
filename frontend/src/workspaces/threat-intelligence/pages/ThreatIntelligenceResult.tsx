import type { ReactNode } from "react";

import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { SystemStyleObject, Theme } from "@mui/system";

import Panel from "@/ui/panel/Panel";

import type {
    ExploitationEvidence,
    ThreatIntelligenceFact,
    VulnerabilityThreatIntelligence,
} from "../ThreatIntelligence";

interface ThreatIntelligenceResultProps {
    intelligence: VulnerabilityThreatIntelligence;
    presentationDensity?: ThreatIntelligencePresentationDensity;
}

export interface ThreatIntelligencePresentationDensity {
    subsectionHeading: SystemStyleObject<Theme>;
    fieldLabel: SystemStyleObject<Theme>;
    primaryValue: SystemStyleObject<Theme>;
    helpText: SystemStyleObject<Theme>;
    reference: SystemStyleObject<Theme>;
    chip: SystemStyleObject<Theme>;
}

export default function ThreatIntelligenceResult({
    intelligence,
    presentationDensity,
}: ThreatIntelligenceResultProps) {
    return (
        <Stack spacing={2} aria-label="Threat intelligence result">
            <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={1}
                sx={{ alignItems: { md: "center" }, justifyContent: "space-between" }}
            >
                <Box>
                    <Typography variant="overline" color="secondary.light" sx={presentationDensity?.fieldLabel} data-ti-density-role={presentationDensity ? "field-label" : undefined}>
                        Vulnerability intelligence
                    </Typography>
                    <Typography variant={presentationDensity ? "subtitle2" : "h5"} sx={presentationDensity?.subsectionHeading} data-ti-density-role={presentationDensity ? "subsection-heading" : undefined}>{intelligence.cve_identifier}</Typography>
                </Box>
                <Chip
                    label={`Contract ${intelligence.contract_version}`}
                    variant="outlined"
                    sx={presentationDensity?.chip}
                    data-ti-density-role={presentationDensity ? "chip" : undefined}
                />
            </Stack>

            <FactPanel title="NVD" fact={intelligence.nvd} presentationDensity={presentationDensity}>
                {intelligence.nvd.value && (
                    <FieldList presentationDensity={presentationDensity}
                        fields={[
                            ["Summary", intelligence.nvd.value.summary],
                            ["Published", intelligence.nvd.value.published_at],
                            ["Last modified", intelligence.nvd.value.last_modified_at],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel title="CVSS" fact={intelligence.cvss} presentationDensity={presentationDensity}>
                {intelligence.cvss.value && (
                    <FieldList presentationDensity={presentationDensity}
                        fields={[
                            ["Base score", String(intelligence.cvss.value.base_score)],
                            ["Severity", intelligence.cvss.value.severity],
                            ["Version", intelligence.cvss.value.version],
                            ["Vector", intelligence.cvss.value.vector],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel title="EPSS" fact={intelligence.epss} presentationDensity={presentationDensity}>
                {intelligence.epss.value && (
                    <FieldList presentationDensity={presentationDensity}
                        fields={[
                            ["Probability", String(intelligence.epss.value.probability)],
                            [
                                "Percentile",
                                intelligence.epss.value.percentile === null
                                    ? null
                                    : String(intelligence.epss.value.percentile),
                            ],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel title="CISA KEV" fact={intelligence.cisa_kev} presentationDensity={presentationDensity}>
                {intelligence.cisa_kev.value && (
                    <FieldList presentationDensity={presentationDensity}
                        fields={[
                            [
                                "Catalog membership",
                                intelligence.cisa_kev.value.known_exploited
                                    ? "Yes (true)"
                                    : "No (false)",
                            ],
                            ["Date added", intelligence.cisa_kev.value.date_added],
                            ["Due date", intelligence.cisa_kev.value.due_date],
                            [
                                "Required action",
                                intelligence.cisa_kev.value.required_action,
                            ],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel
                title="Exploitation Evidence"
                fact={intelligence.exploitation_evidence}
                presentationDensity={presentationDensity}
            >
                {intelligence.exploitation_evidence.value?.map((evidence) => (
                    <EvidenceItem
                        key={`${evidence.evidence_type}:${evidence.provenance.source_reference}`}
                        evidence={evidence}
                        presentationDensity={presentationDensity}
                    />
                ))}
            </FactPanel>
        </Stack>
    );
}

interface FactPanelProps {
    title: string;
    fact: ThreatIntelligenceFact<unknown>;
    children?: ReactNode;
    presentationDensity?: ThreatIntelligencePresentationDensity;
}

function FactPanel({ title, fact, children, presentationDensity }: FactPanelProps) {
    return (
        <Panel component="section">
            <Stack spacing={1.5}>
                <Stack
                    direction="row"
                    spacing={1}
                    useFlexGap
                    sx={{ alignItems: "center", flexWrap: "wrap" }}
                >
                    <Typography variant={presentationDensity ? "subtitle2" : "h6"} sx={presentationDensity?.subsectionHeading} data-ti-density-role={presentationDensity ? "subsection-heading" : undefined}>{title}</Typography>
                    <Chip label={`Status: ${fact.status}`} size="small" sx={presentationDensity?.chip} data-ti-density-role={presentationDensity ? "chip" : undefined} />
                    <Chip
                        label={`Source: ${fact.provenance.source_type}`}
                        size="small"
                        variant="outlined"
                        sx={presentationDensity?.chip}
                        data-ti-density-role={presentationDensity ? "chip" : undefined}
                    />
                </Stack>
                {fact.value === null ? (
                    <Typography variant={presentationDensity ? "body2" : undefined} color="text.secondary" sx={presentationDensity?.helpText} data-ti-density-role={presentationDensity ? "help-text" : undefined}>
                        No value supplied by the backend.
                    </Typography>
                ) : (
                    children
                )}
                <Typography variant="caption" color="text.secondary" sx={presentationDensity ? [presentationDensity.reference, { overflowWrap: "anywhere", minWidth: 0 }] : undefined} data-ti-density-role={presentationDensity ? "reference" : undefined}>
                    Source reference: {fact.provenance.source_reference}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={presentationDensity ? [presentationDensity.reference, { overflowWrap: "anywhere", minWidth: 0 }] : undefined} data-ti-density-role={presentationDensity ? "reference" : undefined}>
                    Observed at: {fact.observed_at ?? "Not provided"}
                </Typography>
            </Stack>
        </Panel>
    );
}

interface FieldListProps {
    fields: ReadonlyArray<readonly [string, string | null]>;
    presentationDensity?: ThreatIntelligencePresentationDensity;
}

function FieldList({ fields, presentationDensity }: FieldListProps) {
    return (
        <Stack spacing={1}>
            {fields.map(([label, value]) => (
                <Box key={label}>
                    <Typography variant="caption" color="text.secondary" sx={presentationDensity?.fieldLabel} data-ti-density-role={presentationDensity ? "field-label" : undefined}>
                        {label}
                    </Typography>
                    <Typography variant={presentationDensity ? "body2" : undefined} sx={{ ...presentationDensity?.primaryValue, overflowWrap: "anywhere" }} data-ti-density-role={presentationDensity ? "primary-value" : undefined}>
                        {value ?? "Not provided"}
                    </Typography>
                </Box>
            ))}
        </Stack>
    );
}

function EvidenceItem({ evidence, presentationDensity }: { evidence: ExploitationEvidence; presentationDensity?: ThreatIntelligencePresentationDensity }) {
    return (
        <Stack spacing={0.5}>
            <Typography variant={presentationDensity ? "body2" : undefined} sx={presentationDensity?.primaryValue} data-ti-density-role={presentationDensity ? "primary-value" : undefined}>{evidence.evidence_type}</Typography>
            <Typography variant={presentationDensity ? "body2" : undefined} color="text.secondary" sx={presentationDensity?.helpText} data-ti-density-role={presentationDensity ? "help-text" : undefined}>{evidence.description}</Typography>
            <Typography variant="caption" color="text.secondary" sx={presentationDensity ? [presentationDensity.reference, { overflowWrap: "anywhere", minWidth: 0 }] : undefined} data-ti-density-role={presentationDensity ? "reference" : undefined}>
                Evidence source: {evidence.provenance.source_type} —{" "}
                {evidence.provenance.source_reference}
            </Typography>
        </Stack>
    );
}
