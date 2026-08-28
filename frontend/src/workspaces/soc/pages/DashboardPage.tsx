import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { WorkspaceContext } from "@/context/WorkspaceContext";
import { WorkspaceId } from "@/types/workspace";
import type { IncidentCommandCenterResponse } from "@/workspaces/incident-response/IncidentCommandCenter";
import { getIncidentCommandCenter } from "@/workspaces/incident-response/IncidentCommandCenterApiClient";
import EnterpriseSOCDashboard from "../dashboard/EnterpriseSOCDashboard";
import { getFindingIncidents, type FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import { getFindings } from "../findings/FindingsApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

interface DashboardPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
    loadFindingIncidents?: (findingId: string) => Promise<readonly FindingIncidentReference[]>;
    loadIncident?: (incidentId: string) => Promise<IncidentCommandCenterResponse>;
}
type LoadState = "loading" | "ready" | "error";

export default function DashboardPage({ loadFindings = getFindings, loadFindingIncidents = getFindingIncidents, loadIncident = getIncidentCommandCenter }: DashboardPageProps) {
    const { search } = useLocation();
    const navigate = useNavigate();
    const workspaceContext = useContext(WorkspaceContext);
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [findingsState, setFindingsState] = useState<LoadState>("loading");
    const [incidentStatus, setIncidentStatus] = useState<string>();
    const loaders = useRef({ loadFindings, loadFindingIncidents, loadIncident });
    loaders.current = { loadFindings, loadFindingIncidents, loadIncident };
    const requestedFindingId = useMemo(() => new URLSearchParams(search).get("findingId"), [search]);
    const selectedFinding = useMemo(() => findings.find((finding) => finding.id === requestedFindingId) ?? null, [findings, requestedFindingId]);

    useEffect(() => {
        let current = true;
        setFindingsState("loading");
        void loaders.current.loadFindings().then((result) => {
            if (current) { setFindings(result); setFindingsState("ready"); }
        }).catch(() => { if (current) { setFindings([]); setFindingsState("error"); } });
        return () => { current = false; };
    }, []);

    useEffect(() => {
        let current = true;
        setIncidentStatus(undefined);
        if (findingsState !== "ready" || !selectedFinding) return () => { current = false; };
        void loaders.current.loadFindingIncidents(selectedFinding.id).then(async (relationships) => {
            if (!current) return;
            const relationship = relationships[0];
            if (!relationship) { setIncidentStatus("No linked incident"); return; }
            setIncidentStatus(relationship.lifecycle_status);
            try { await loaders.current.loadIncident(relationship.incident_id); } catch { /* Status remains canonical relationship state. */ }
        }).catch(() => { if (current) setIncidentStatus("Unavailable"); });
        return () => { current = false; };
    }, [findingsState, selectedFinding]);

    const openFindings = () => {
        workspaceContext?.setWorkspace(WorkspaceId.DECISION_CENTER);
        navigate(selectedFinding ? `/findings?findingId=${encodeURIComponent(selectedFinding.id)}` : "/findings");
    };

    return <EnterpriseSOCDashboard findings={findings} findingsState={findingsState} selectedFinding={selectedFinding} incidentStatus={incidentStatus} onOpenFindings={openFindings} />;
}
