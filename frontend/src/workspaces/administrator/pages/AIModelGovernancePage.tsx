import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type {
    AIModelGovernanceVisibility,
    AIModelRegistrationVisibility,
    AIProviderGovernanceVisibility,
    GovernanceOperatorSession,
} from "../AIModelGovernance";
import {
    getAIModelGovernance,
    getGovernanceOperatorSession,
    updateAIModelSelection,
} from "../AIModelGovernanceApiClient";

const SELECTION_PERMISSION = "ai_model_selection:update";

export default function AIModelGovernancePage() {
    const [governance, setGovernance] = useState<AIModelGovernanceVisibility | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [session, setSession] = useState<GovernanceOperatorSession | null>(null);
    const [savingCapability, setSavingCapability] = useState<string | null>(null);
    const [selectionMessage, setSelectionMessage] = useState<string | null>(null);
    const [selectionError, setSelectionError] = useState<string | null>(null);

    useEffect(() => {
        let current = true;
        void getAIModelGovernance()
            .then((value) => {
                if (current) setGovernance(value);
            })
            .catch(() => {
                if (current) setError(true);
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
        void getGovernanceOperatorSession()
            .then((value) => {
                if (current) setSession(value);
            })
            .catch(() => {
                if (current) setSession(null);
            });
        return () => {
            current = false;
        };
    }, []);

    async function changeSelection(
        capability: string,
        registration: AIModelRegistrationVisibility,
    ) {
        if (!session) return;
        setSavingCapability(capability);
        setSelectionMessage(null);
        setSelectionError(null);
        try {
            const updated = await updateAIModelSelection(
                capability,
                registration.provider,
                registration.model_id,
                session.csrf_token,
            );
            setGovernance(updated);
            setSelectionMessage(`${formatLabel(capability)} selection saved.`);
        } catch {
            setSelectionError(`${formatLabel(capability)} selection was rejected by governance.`);
        } finally {
            setSavingCapability(null);
        }
    }

    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="text.secondary">
                    Administrator · Read-only governance
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    AI Model Governance
                </Typography>
                <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 820 }}>
                    Live server-side registry state. Registration, capability authority,
                    activation and technical execution availability are separate controls.
                </Typography>
            </Box>

            {loading && (
                <Panel component="section">
                    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                        <CircularProgress size={22} />
                        <Typography>Loading governed model registry…</Typography>
                    </Stack>
                </Panel>
            )}

            {!loading && error && (
                <Alert severity="error">
                    The governed model registry could not be loaded. No local fallback data is shown.
                </Alert>
            )}

            {!loading && !error && governance?.providers.length === 0 && (
                <Panel component="section">
                    <Typography variant="h6">No governed provider families are available</Typography>
                    <Typography color="text.secondary" sx={{ mt: 1 }}>
                        The server returned an empty governance registry projection.
                    </Typography>
                </Panel>
            )}

            {!loading && !error && governance && governance.providers.length > 0 && (
                <>
                    {selectionMessage && <Alert severity="success">{selectionMessage}</Alert>}
                    {selectionError && <Alert severity="error">{selectionError}</Alert>}
                    <CapabilitySelections
                        governance={governance}
                        authorized={session?.granted_permissions.includes(SELECTION_PERMISSION) ?? false}
                        savingCapability={savingCapability}
                        onChange={changeSelection}
                    />
                    <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                        {governance.capabilities.map((capability) => (
                            <Chip key={capability} label={formatLabel(capability)} variant="outlined" />
                        ))}
                    </Stack>
                    <Box
                        component="section"
                        aria-label="Governed AI providers"
                        sx={{
                            display: "grid",
                            gridTemplateColumns: { xs: "1fr", xl: "repeat(2, minmax(0, 1fr))" },
                            gap: 2,
                        }}
                    >
                        {governance.providers.map((provider) => (
                            <ProviderCard key={provider.provider} provider={provider} />
                        ))}
                    </Box>
                </>
            )}
        </Stack>
    );
}

interface CapabilitySelectionsProps {
    governance: AIModelGovernanceVisibility;
    authorized: boolean;
    savingCapability: string | null;
    onChange: (
        capability: string,
        registration: AIModelRegistrationVisibility,
    ) => Promise<void>;
}

function CapabilitySelections({
    governance,
    authorized,
    savingCapability,
    onChange,
}: CapabilitySelectionsProps) {
    const registrations = governance.providers.flatMap((provider) => provider.registrations);
    return (
        <Panel component="section">
            <Stack spacing={2}>
                <Typography variant="h6">Active governed selections</Typography>
                {!authorized && (
                    <Alert severity="info">
                        An authenticated Local Operator with AI model selection authority is required to change selections.
                    </Alert>
                )}
                {governance.capabilities.map((capability) => {
                    const active = registrations.find((registration) =>
                        registration.capabilities.some((item) => item.capability === capability && item.active),
                    );
                    return (
                        <FormControl key={capability} fullWidth disabled={!authorized || savingCapability !== null}>
                            <InputLabel>{formatLabel(capability)}</InputLabel>
                            <Select
                                label={formatLabel(capability)}
                                value={active ? registrationKey(active) : ""}
                                onChange={(event) => {
                                    const registration = registrations.find(
                                        (item) => registrationKey(item) === event.target.value,
                                    );
                                    if (registration) void onChange(capability, registration);
                                }}
                            >
                                {registrations.map((registration) => {
                                    const state = registration.capabilities.find(
                                        (item) => item.capability === capability,
                                    );
                                    const reason = selectionReason(registration, state);
                                    return (
                                        <MenuItem
                                            key={registrationKey(registration)}
                                            value={registrationKey(registration)}
                                            disabled={reason !== null}
                                        >
                                            {registration.provider} / {registration.model_id}
                                            {reason ? ` — ${reason}` : ""}
                                        </MenuItem>
                                    );
                                })}
                            </Select>
                            {savingCapability === capability && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                                    Saving governed selection…
                                </Typography>
                            )}
                        </FormControl>
                    );
                })}
            </Stack>
        </Panel>
    );
}

function selectionReason(
    registration: AIModelRegistrationVisibility,
    capability: AIModelRegistrationVisibility["capabilities"][number] | undefined,
) {
    if (registration.status !== "enabled") return "Disabled";
    if (!capability?.authorized) return "Not authorized for capability";
    if (!capability.adapter_available) return "No live adapter";
    if (!capability.execution_available) return "Server configuration unavailable";
    return null;
}

function registrationKey(registration: AIModelRegistrationVisibility) {
    return `${registration.provider}:${registration.model_id}`;
}

function ProviderCard({ provider }: { provider: AIProviderGovernanceVisibility }) {
    return (
        <Panel component="article">
            <Stack spacing={2}>
                <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between" }}>
                    <Typography variant="h6">{provider.provider}</Typography>
                    <Chip
                        size="small"
                        label={provider.governance_status === "registered" ? "Registered" : "Foundation only"}
                        color={provider.governance_status === "registered" ? "primary" : "default"}
                        variant="outlined"
                    />
                </Stack>
                {provider.registrations.length === 0 ? (
                    <Typography color="text.secondary">
                        No model identity is registered. This provider is not configured or executable.
                    </Typography>
                ) : provider.registrations.map((registration) => (
                    <Registration key={`${registration.provider}:${registration.model_id}`} registration={registration} />
                ))}
            </Stack>
        </Panel>
    );
}

function Registration({ registration }: { registration: AIModelRegistrationVisibility }) {
    return (
        <Stack spacing={1.5}>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center" }}>
                <Typography sx={{ fontWeight: 700 }}>{registration.model_id}</Typography>
                <Chip size="small" label={registration.status} color={registration.status === "enabled" ? "success" : "default"} />
                <Chip size="small" label={formatLabel(registration.governance_status)} variant="outlined" />
            </Stack>
            <Typography variant="body2" color="text.secondary">
                Policy: {registration.policy_reference} · Execution binding: {registration.execution_binding}
            </Typography>
            {registration.capabilities.map((capability) => (
                <Box key={capability.capability} sx={{ p: 1.5, border: "1px solid", borderColor: "divider", borderRadius: 1.5 }}>
                    <Typography sx={{ fontWeight: 600 }}>{formatLabel(capability.capability)}</Typography>
                    <Typography variant="body2" color="text.secondary">
                        Authorized: {yesNo(capability.authorized)} · Live adapter: {yesNo(capability.adapter_available)} · Executable now: {yesNo(capability.execution_available)}
                    </Typography>
                </Box>
            ))}
        </Stack>
    );
}

function formatLabel(value: string) {
    return value.split("_").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function yesNo(value: boolean) {
    return value ? "Yes" : "No";
}
