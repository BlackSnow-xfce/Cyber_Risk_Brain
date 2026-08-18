import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import DashboardWidget from "@/components/dashboard/DashboardWidget";
import Panel from "@/ui/panel/Panel";

import {
    getFindings,
} from "../findings/FindingsApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

interface DashboardPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
}

export default function DashboardPage({
    loadFindings = getFindings,
}: DashboardPageProps) {
    const navigate = useNavigate();
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [findingsLoading, setFindingsLoading] = useState(true);
    const [findingsError, setFindingsError] = useState(false);

    useEffect(() => {
        let active = true;

        loadFindings()
            .then((loadedFindings) => {
                if (active) {
                    setFindings(loadedFindings);
                }
            })
            .catch(() => {
                if (active) {
                    setFindingsError(true);
                }
            })
            .finally(() => {
                if (active) {
                    setFindingsLoading(false);
                }
            });

        return () => {
            active = false;
        };
    }, [loadFindings]);

    const findingsValue = findingsLoading
        ? "…"
        : findingsError
            ? "—"
            : String(findings.length);
    const findingsStatus = findingsLoading
        ? "Loading"
        : findingsError
            ? "Unavailable"
            : "Live";

    return (
        <Stack spacing={2} component="main">
            <Box component="header">
                <Typography
                    variant="overline"
                    color="primary.main"
                >
                    Security Operations
                </Typography>
                <Typography variant="h3" sx={{ mt: 0.25 }}>
                    SOC Analyst
                </Typography>
                <Typography
                    color="text.secondary"
                    sx={{ mt: 0.5, maxWidth: 760 }}
                >
                    Monitor findings, investigate active context and move from
                    security observations to the right operational workspace.
                </Typography>
            </Box>

            <Box
                component="section"
                aria-label="Operational status"
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        md: "repeat(3, minmax(0, 1fr))",
                    },
                    gap: 1.5,
                }}
            >
                <OperationalStatusCard
                    title="Findings"
                    value={findingsValue}
                    description="Live feed"
                    label={findingsStatus}
                    color={findingsError ? "default" : "success"}
                />
                <OperationalStatusCard
                    title="Threat Intelligence"
                    value="—"
                    description="On-demand context"
                    label="Ready"
                    color="info"
                />
                <OperationalStatusCard
                    title="Incident Context"
                    value="—"
                    description="Requires incident reference"
                    label="Not available"
                    color="default"
                />
            </Box>

            <Box
                component="section"
                aria-label="Analyst workspace"
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        xl: "minmax(0, 7fr) minmax(320px, 3fr)",
                    },
                    gap: 1.5,
                    alignItems: "start",
                }}
            >
                <DashboardWidget
                    title="Analyst Workspace"
                    subtitle="Operational findings and investigation context"
                >
                    <Stack spacing={1}>
                        <FindingsWorkspaceSlot
                            findings={findings}
                            loading={findingsLoading}
                            error={findingsError}
                        />
                        <WorkspaceSlot label="Investigation context" value="Not available" />
                        <WorkspaceSlot label="Prioritization" value="Not available" />
                    </Stack>
                    <Button
                        variant="contained"
                        onClick={() => navigate("/findings")}
                        sx={{ alignSelf: "flex-start", mt: 0.5 }}
                    >
                        Open Findings
                    </Button>
                </DashboardWidget>

                <DashboardWidget
                    title="Context & Insights"
                    subtitle="Evidence-aware analyst context"
                >
                    <Stack
                        spacing={1}
                    >
                        <ContextSlot label="Threat intelligence" />
                        <ContextSlot label="Evidence" />
                        <ContextSlot label="Explainability" />
                        <ContextSlot label="Incident context" />
                    </Stack>
                </DashboardWidget>
            </Box>
        </Stack>
    );
}

interface OperationalStatusCardProps {
    title: string;
    value: string;
    description: string;
    label: string;
    color: "default" | "info" | "success";
}

function OperationalStatusCard({
    title,
    value,
    description,
    label,
    color,
}: OperationalStatusCardProps) {
    return (
        <Panel component="article">
            <Stack spacing={1}>
                <Stack
                    direction="row"
                    spacing={1}
                    sx={{
                        alignItems: "center",
                        justifyContent: "space-between",
                    }}
                >
                    <Typography variant="body2" color="text.secondary">
                        {title}
                    </Typography>
                    <Chip label={label} size="small" color={color} variant="outlined" />
                </Stack>
                <Typography variant="h4" sx={{ fontWeight: 700, lineHeight: 1 }}>
                    {value}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {description}
                </Typography>
            </Stack>
        </Panel>
    );
}

function WorkspaceSlot({ label, value }: { label: string; value: string }) {
    return (
        <Panel
            sx={{
                px: 1.5,
                py: 1.25,
                backgroundColor: "background.default",
            }}
        >
            <Stack
                direction="row"
                sx={{ justifyContent: "space-between", alignItems: "center" }}
            >
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {value}
                </Typography>
            </Stack>
        </Panel>
    );
}

interface FindingsWorkspaceSlotProps {
    findings: readonly FindingSummary[];
    loading: boolean;
    error: boolean;
}

function FindingsWorkspaceSlot({
    findings,
    loading,
    error,
}: FindingsWorkspaceSlotProps) {
    return (
        <Panel
            sx={{
                px: 1.5,
                py: 1.25,
                backgroundColor: "background.default",
            }}
        >
            <Stack spacing={1}>
                <Stack
                    direction="row"
                    sx={{ justifyContent: "space-between", alignItems: "center" }}
                >
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Findings
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {loading ? "Loading" : error ? "Not available" : `${findings.length} loaded`}
                    </Typography>
                </Stack>

                {loading && <CircularProgress size={18} />}
                {error && (
                    <Typography variant="caption" color="text.secondary">
                        Live findings could not be loaded.
                    </Typography>
                )}
                {!loading && !error && findings.length === 0 && (
                    <Typography variant="caption" color="text.secondary">
                        No live findings available.
                    </Typography>
                )}
                {!loading && !error && findings.length > 0 && (
                    <Stack spacing={0.75}>
                        {findings.slice(0, 3).map((finding) => (
                            <FindingSummaryRow key={finding.id} finding={finding} />
                        ))}
                    </Stack>
                )}
            </Stack>
        </Panel>
    );
}

function FindingSummaryRow({ finding }: { finding: FindingSummary }) {
    return (
        <Box
            sx={{
                display: "grid",
                gridTemplateColumns: "minmax(0, 1fr) auto",
                gap: 1,
                alignItems: "center",
                borderTop: "1px solid",
                borderColor: "divider",
                pt: 0.75,
            }}
        >
            <Box sx={{ minWidth: 0 }}>
                <Typography
                    variant="caption"
                    sx={{
                        display: "block",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    {finding.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {finding.source} · {finding.id}
                </Typography>
            </Box>
            <Chip
                label={finding.vendorSeverity}
                size="small"
                variant="outlined"
            />
        </Box>
    );
}

function ContextSlot({ label }: { label: string }) {
    return (
        <Stack
            direction="row"
            sx={{
                justifyContent: "space-between",
                alignItems: "center",
                borderBottom: "1px solid",
                borderColor: "divider",
                pb: 1,
            }}
        >
            <Typography variant="body2">{label}</Typography>
            <Chip label="Not available" size="small" variant="outlined" />
        </Stack>
    );
}
