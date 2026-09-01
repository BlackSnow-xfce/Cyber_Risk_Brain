import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { ReactNode } from "react";

import type { FindingRiskContext } from "./FindingRiskContext";

interface FindingRiskContextSectionProps {
    context: FindingRiskContext | null;
    error: string | null;
    loading: boolean;
    onLoad: () => void;
}

interface AuthorityFieldProps {
    label: string;
    value: ReactNode;
    detail?: ReactNode;
    semanticStatus?: boolean;
    valueTone?: "primary" | "secondary";
}

const wrappingValueSx = { overflowWrap: "anywhere", minWidth: 0 } as const;

const positiveStatusValues = new Set(["READY", "AVAILABLE", "RESOLVED", "available", "resolved"]);
const incompleteStatusValues = new Set([
    "UNAVAILABLE",
    "NOT_FOUND",
    "NOT_EVALUATED",
    "UNKNOWN",
    "not_found",
    "not_evaluated",
    "unknown",
    "NO_DATA",
    "no_data",
]);

function statusColor(value: ReactNode) {
    if (typeof value !== "string") return undefined;
    if (positiveStatusValues.has(value)) return "success.main";
    if (incompleteStatusValues.has(value)) return "warning.main";
    return undefined;
}

function AuthorityField({ label, value, detail, semanticStatus = false, valueTone = "primary" }: AuthorityFieldProps) {
    const valueColor = semanticStatus ? statusColor(value) : undefined;
    const neutralValueColor = valueTone === "secondary" ? "text.secondary" : "text.primary";
    return (
        <Stack spacing={0.25} sx={{ minWidth: 0 }} data-authority-field={label}>
            <Typography variant="caption" color="info.main" sx={{ fontWeight: 600 }} data-color-token="info.main">{label}</Typography>
            <Typography
                component="div"
                variant="body2"
                color={valueColor ?? neutralValueColor}
                sx={wrappingValueSx}
                data-color-token={valueColor ?? neutralValueColor}
            >
                {value}
            </Typography>
            {detail !== undefined && (
                <Typography component="div" variant="caption" color="text.secondary" sx={wrappingValueSx} data-color-token="text.secondary">{detail}</Typography>
            )}
        </Stack>
    );
}

function AuthorityGroup({ label, children, structural = false }: { label: string; children: ReactNode; structural?: boolean }) {
    return (
        <Stack spacing={1} aria-label={label} sx={{ minWidth: 0 }}>
            <Typography
                variant="subtitle2"
                color={structural ? "info.main" : undefined}
                data-color-token={structural ? "info.main" : undefined}
            >
                {label}
            </Typography>
            {children}
        </Stack>
    );
}

function presentationLabel(identifier: string) {
    const [name, qualifier] = identifier.split(":", 2);
    const words = name.replaceAll("_", " ").replaceAll("-", " ");
    const label = `${words.charAt(0).toUpperCase()}${words.slice(1)}`;
    return qualifier ? `${label} — ${qualifier}` : label;
}

function inputLabel(reference: string) {
    const authority = reference.split(":", 1)[0];
    const labels: Readonly<Record<string, string>> = {
        finding: "Finding",
        "asset-context": "Asset context",
        "threat-intelligence": "Threat intelligence",
    };
    return labels[authority] ?? "Input";
}

export default function FindingRiskContextSection({ context, error, loading, onLoad }: FindingRiskContextSectionProps) {
    return (
        <Stack spacing={1.5} aria-label="Finding risk context">
            <Divider />
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="h6">Authoritative Risk Context</Typography>
                <Button size="small" variant="outlined" onClick={onLoad} disabled={loading}>
                    {loading ? "Loading" : "Load risk context"}
                </Button>
            </Stack>
            {loading && <CircularProgress size={18} />}
            {error && <Alert severity="error">{error}</Alert>}
            {context && (
                <Stack spacing={2}>
                    <AuthorityGroup label="What PredatorAI knows">
                        <Stack spacing={1.25}>
                            {context.source_facts.map((fact) => (
                                <Stack key={fact.name} spacing={0.75}>
                                    <AuthorityField label={presentationLabel(fact.name)} value={fact.value} />
                                    <AuthorityField label="Source" value={fact.source_reference} valueTone="secondary" />
                                </Stack>
                            ))}
                            {context.asset_context.status === "resolved" && (
                                <Stack spacing={0.75} aria-label="Canonical asset context">
                                    <AuthorityField label="Canonical asset" value={context.asset_context.canonical_asset_id} />
                                    <AuthorityField label="Asset criticality" value={context.asset_context.criticality} />
                                    <AuthorityField label="Source" value={context.asset_context.source_reference} valueTone="secondary" />
                                </Stack>
                            )}
                        </Stack>
                    </AuthorityGroup>

                    {context.business_context && context.business_impact_readiness && (
                        <>
                            <AuthorityGroup label="Authoritative Business Context">
                                {context.business_context.status === "RESOLVED" ? (
                                    <Stack spacing={1.25}>
                                        {context.business_impact_readiness.facts.map((fact) => (
                                            <Stack key={fact.name} spacing={0.75}>
                                                <AuthorityField label={presentationLabel(fact.name)} value={fact.value} />
                                                <AuthorityField label="Source" value={fact.source_reference} valueTone="secondary" />
                                            </Stack>
                                        ))}
                                    </Stack>
                                ) : (
                                    <Alert severity="warning">
                                        <Stack spacing={1}>
                                            <AuthorityField label="Status" value={context.business_context.status} semanticStatus />
                                            <AuthorityField label="Reason" value="No organizational facts were inferred." />
                                        </Stack>
                                    </Alert>
                                )}
                            </AuthorityGroup>
                            <AuthorityGroup label="Business-Impact Readiness">
                                <Stack spacing={1.25}>
                                    <AuthorityField label="Status" value={context.business_impact_readiness.status} semanticStatus />
                                    <AuthorityField label="Reason" value={context.business_impact_readiness.reason} />
                                    <AuthorityField label="Source" value={context.business_impact_readiness.source_type} detail={context.business_impact_readiness.source_reference} />
                                    <AuthorityField label="Completeness" value={context.business_impact_readiness.completeness_status} semanticStatus />
                                    {context.business_impact_readiness.missing_requirements.length > 0 && (
                                        <AuthorityGroup label="Missing requirements" structural>
                                            <Stack spacing={1}>
                                                {context.business_impact_readiness.missing_requirements.map((requirement) => (
                                                    <AuthorityField key={requirement} label="Requirement" value={presentationLabel(requirement)} detail={requirement} />
                                                ))}
                                            </Stack>
                                        </AuthorityGroup>
                                    )}
                                    <Alert severity="info">Business-impact readiness does not calculate Business Impact. Business impact remains unavailable.</Alert>
                                </Stack>
                            </AuthorityGroup>
                        </>
                    )}

                    {context.service_impact_profile && (
                        <AuthorityGroup label="Service Impact Profile">
                            <Stack spacing={1.25}>
                                <AuthorityField label="Status" value={context.service_impact_profile.status} semanticStatus />
                                {context.service_impact_profile.status === "RESOLVED" ? (
                                    <>
                                        <AuthorityField label="Canonical asset" value={context.service_impact_profile.canonical_asset_id} />
                                        <AuthorityField label="Business service" value={context.service_impact_profile.business_service} />
                                        <AuthorityField label="Confidentiality importance" value={context.service_impact_profile.confidentiality_importance} />
                                        <AuthorityField label="Integrity importance" value={context.service_impact_profile.integrity_importance} />
                                        <AuthorityField label="Availability importance" value={context.service_impact_profile.availability_importance} />
                                        <AuthorityField label="Source" value={context.service_impact_profile.source_reference} valueTone="secondary" />
                                    </>
                                ) : (
                                    <AuthorityField label="Reason" value="No CIA business importance was inferred." />
                                )}
                            </Stack>
                        </AuthorityGroup>
                    )}

                    {context.technical_effect && (
                        <AuthorityGroup label="Technical Effect">
                            <Stack spacing={1.25}>
                                <AuthorityField label="Status" value={context.technical_effect.status} semanticStatus />
                                <AuthorityField label="Reason" value="This technical projection is not Business Impact." />
                                {context.technical_effect.effects.map((effect) => (
                                    <Stack key={`${effect.cve_identifier}:${effect.source_reference}`} spacing={1} aria-label={`Technical effect ${effect.cve_identifier}`}>
                                        <AuthorityField label="CVE" value={effect.cve_identifier} />
                                        <AuthorityField label="CVSS version" value={effect.cvss_version} />
                                        <AuthorityField label="CVSS vector" value={effect.cvss_vector} />
                                        <AuthorityField label="Confidentiality" value={effect.confidentiality} />
                                        <AuthorityField label="Integrity" value={effect.integrity} />
                                        <AuthorityField label="Availability" value={effect.availability} />
                                        <AuthorityField label="Source" value={effect.source_type} detail={effect.source_reference} />
                                        <AuthorityField label="Observed" value={effect.observed_at} />
                                    </Stack>
                                ))}
                            </Stack>
                        </AuthorityGroup>
                    )}

                    {context.business_impact_classification_readiness && (
                        <AuthorityGroup label="Business-Impact Classification Readiness">
                            <Stack spacing={1.25}>
                                <AuthorityField label="Status" value={context.business_impact_classification_readiness.status} semanticStatus />
                                <AuthorityField label="Reason" value={context.business_impact_classification_readiness.reason} />
                                <AuthorityField label="Source" value={context.business_impact_classification_readiness.source_type} detail={context.business_impact_classification_readiness.source_reference} />
                                <AuthorityField label="Completeness" value={context.business_impact_classification_readiness.completeness_status} semanticStatus />
                                <Typography variant="body2">Readiness is not a Business Impact result.</Typography>
                                {context.business_impact_classification_readiness.missing_requirements.length > 0 && (
                                    <AuthorityGroup label="Missing requirements" structural>
                                        <Stack spacing={1}>
                                            {context.business_impact_classification_readiness.missing_requirements.map((requirement) => (
                                                <AuthorityField key={requirement} label="Requirement" value={presentationLabel(requirement)} detail={requirement} />
                                            ))}
                                        </Stack>
                                    </AuthorityGroup>
                                )}
                            </Stack>
                        </AuthorityGroup>
                    )}

                    <AuthorityGroup label="Threat Intelligence">
                        <Stack spacing={1.5}>
                            {context.threat_intelligence.relationships.map((relationship, index) => (
                                <Stack key={relationship.cve_identifier ?? `not-applicable-${index}`} spacing={1}>
                                    <AuthorityField label="CVE" value={relationship.cve_identifier ?? "No applicable CVE"} />
                                    <AuthorityField label="Applicability" value={relationship.applicability} semanticStatus />
                                    {relationship.intelligence && Object.entries({
                                        nvd: relationship.intelligence.nvd,
                                        cvss: relationship.intelligence.cvss,
                                        epss: relationship.intelligence.epss,
                                        cisa_kev: relationship.intelligence.cisa_kev,
                                        exploitation_evidence: relationship.intelligence.exploitation_evidence,
                                    }).map(([name, fact]) => (
                                        <Stack key={name} spacing={0.75} aria-label={presentationLabel(name)}>
                                            <AuthorityField label="Authority" value={presentationLabel(name)} />
                                            <AuthorityField label="Status" value={fact.status} semanticStatus />
                                            <AuthorityField label="Source" value={fact.provenance.source_type} detail={fact.provenance.source_reference} />
                                        </Stack>
                                    ))}
                                </Stack>
                            ))}
                        </Stack>
                    </AuthorityGroup>

                    <AuthorityGroup label="Correlation / Evidence">
                        <Stack spacing={1.5}>
                            <AuthorityGroup label="Correlation" structural>
                                <Stack spacing={1}>
                                    <AuthorityField label="Status" value={context.correlation.completeness_status} semanticStatus />
                                    <AuthorityField label="Source" value={context.correlation.source_type} detail={context.correlation.source_reference} />
                                </Stack>
                            </AuthorityGroup>
                            {context.evidence.map((evidence) => (
                                <AuthorityGroup key={evidence.identifier} label="Evidence" structural>
                                    <Stack spacing={1}>
                                        <AuthorityField label="Reference" value={evidence.identifier} valueTone="secondary" />
                                        <AuthorityField label="Kind" value={evidence.kind} />
                                        <AuthorityField label="Evidence type" value={evidence.evidence_type} />
                                        <AuthorityField label="Contract version" value={evidence.contract_version} />
                                        <AuthorityField label="Source" value={evidence.source_type} detail={evidence.source_reference} />
                                        {evidence.input_references.length > 0 && (
                                            <AuthorityGroup label="Inputs" structural>
                                                <Stack spacing={1}>
                                                    {evidence.input_references.map((reference) => (
                                                        <AuthorityField key={reference} label={inputLabel(reference)} value={reference} valueTone="secondary" />
                                                    ))}
                                                </Stack>
                                            </AuthorityGroup>
                                        )}
                                    </Stack>
                                </AuthorityGroup>
                            ))}
                        </Stack>
                    </AuthorityGroup>

                    <AuthorityGroup label="Information still missing">
                        <Stack spacing={1}>
                            {context.assessment.missing_inputs.map((input) => (
                                <AuthorityField key={input.name} label={presentationLabel(input.name)} value={input.state} semanticStatus />
                            ))}
                            {context.evidence_readiness.missing_requirements.map((requirement) => (
                                <Stack key={requirement} spacing={0.25}>
                                    <span hidden>{`Evidence requirement: ${requirement}`}</span>
                                    <AuthorityField label="Evidence requirement" value={presentationLabel(requirement)} detail={requirement} />
                                </Stack>
                            ))}
                        </Stack>
                    </AuthorityGroup>

                    <AuthorityGroup label="Finding Risk Priority">
                        {context.priority?.status === "PRIORITIZED" ? (
                            <Stack spacing={1.25}>
                                <AuthorityField label="Status" value={context.priority.status} semanticStatus />
                                <AuthorityField label="Priority band" value={context.priority.band} />
                                <AuthorityField label="Gated score" value={context.priority.score} />
                                <AuthorityField label="Reason" value={context.priority.reason} />
                                <AuthorityField label="Source" value={context.priority.source_type} detail={context.priority.source_reference} />
                                {context.priority.considered_evidence_ids.length > 0 && (
                                    <AuthorityGroup label="Evidence" structural>
                                        <Stack spacing={1}>
                                            {context.priority.considered_evidence_ids.map((identifier) => (
                                                <AuthorityField key={identifier} label="Reference" value={identifier} valueTone="secondary" />
                                            ))}
                                        </Stack>
                                    </AuthorityGroup>
                                )}
                                {context.priority.referenced_input_references.length > 0 && (
                                    <AuthorityGroup label="Inputs" structural>
                                        <Stack spacing={1}>
                                            {context.priority.referenced_input_references.map((reference) => (
                                                <AuthorityField key={reference} label={inputLabel(reference)} value={reference} valueTone="secondary" />
                                            ))}
                                        </Stack>
                                    </AuthorityGroup>
                                )}
                            </Stack>
                        ) : (
                            <Alert severity="warning">
                                <Stack spacing={1}>
                                    <AuthorityField label="Status" value={context.priority?.status ?? "UNAVAILABLE"} semanticStatus />
                                    <AuthorityField label="Reason" value={context.priority?.reason ?? "Priority is unavailable."} />
                                    {context.priority?.missing_requirements.map((requirement) => (
                                        <AuthorityField key={requirement} label="Missing requirement" value={presentationLabel(requirement)} detail={requirement} />
                                    ))}
                                    <AuthorityField label="Priority band" value="Not available" />
                                    <AuthorityField label="Score" value="Not available" />
                                </Stack>
                            </Alert>
                        )}
                    </AuthorityGroup>

                    {context.assessment.status === "INSUFFICIENT_CONTEXT" && (
                        <Alert severity="warning">PredatorAI refuses to calculate risk, priority, business impact, a decision, or recommendations. {context.refusal_reason} Score, priority, business impact, decision, and recommendations are not available.</Alert>
                    )}
                </Stack>
            )}
        </Stack>
    );
}
