import { useRef, useState, type ReactNode } from "react";
import { Activity, Bug, Database, Siren } from "lucide-react";
import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";
import InvestigationStateTimeline from "./InvestigationStateTimeline";
import PredatorAIAnalysisPanel from "./PredatorAIAnalysisPanel";
import RecommendedInvestigationPanel from "./RecommendedInvestigationPanel";
import InvestigationRelationshipGraph from "./InvestigationRelationshipGraph";
import "./SOCAnalystCockpit.css";

interface SOCAnalystCockpitProps {
    finding: FindingSummary | null;
    incident: FindingIncidentReference | null;
    commandCenterStatus: string;
    evidenceAvailable: boolean;
    incidentContextValue: string;
    incidentContextStatus: string;
    findingsError: boolean;
    incidentContextError: boolean;
    toolbar: ReactNode;
    evidencePanel: ReactNode;
    relevantFindings: ReactNode;
    incidentContext: ReactNode;
    assetContext: ReactNode;
    onFinding: (id: string) => void;
    onThreatIntelligence: (id: string) => void;
    onIncident: (id: string) => void;
    onOpenFinding: (id: string) => void;
    onOpenThreatIntelligence: (id: string) => void;
    onCommandCenter: (id: string) => void;
}

export default function SOCAnalystCockpit({ finding, incident, commandCenterStatus, evidenceAvailable, incidentContextValue, incidentContextStatus, findingsError, incidentContextError, toolbar, evidencePanel, relevantFindings, incidentContext, assetContext, onFinding, onThreatIntelligence, onIncident, onOpenFinding, onOpenThreatIntelligence, onCommandCenter }: SOCAnalystCockpitProps) {
    const [selectedNode, setSelectedNode] = useState<"finding" | "threat-intelligence" | null>(null);
    const [panelFeedbackActive, setPanelFeedbackActive] = useState(false);
    const panelFeedbackTimer = useRef<number | null>(null);
    const triggerPanelFeedback = () => {
        setPanelFeedbackActive(false);
        window.requestAnimationFrame(() => setPanelFeedbackActive(true));
        if (panelFeedbackTimer.current !== null) {
            window.clearTimeout(panelFeedbackTimer.current);
        }
        panelFeedbackTimer.current = window.setTimeout(() => {
            setPanelFeedbackActive(false);
            panelFeedbackTimer.current = null;
        }, 850);
    };
    const selectFinding = (id: string) => { setSelectedNode("finding"); triggerPanelFeedback(); onFinding(id); };
    const selectThreatIntelligence = (id: string) => { setSelectedNode("threat-intelligence"); triggerPanelFeedback(); onThreatIntelligence(id); };
    return <main className="soc-cockpit" aria-label="Analyst workspace">
        <header className="soc-cockpit__header">
            <span className="soc-cockpit__sr-only">SOC Analyst</span>
            <span className="soc-cockpit__sr-only">SOC Analyst Dashboard</span>
            <div><span className="soc-cockpit__eyebrow">ACTIVE INVESTIGATION</span><h1>{finding?.title ?? "No active investigation"}</h1><div className="soc-cockpit__meta"><span>{finding?.id ?? "FINDING NOT AVAILABLE"}</span><span>{finding?.vendorSeverity ?? "SEVERITY NOT AVAILABLE"}</span><span>{finding?.asset ?? "ASSET NOT AVAILABLE"}</span><span>{incident ? "INCIDENT LINKED" : "INCIDENT NOT AVAILABLE"}</span></div></div>
            <div className="soc-cockpit__header-actions">{toolbar}</div>
        </header>
        <section className="soc-cockpit__kpis" aria-label="Operational metrics">
            <Metric icon={<Bug />} label="Finding" value={finding?.id ?? "Not available"} status={finding?.source ?? "Not available"} detail="Canonical identity" error={findingsError} />
            <Metric icon={<Activity />} label="Vendor severity" value={finding?.vendorSeverity ?? "Not available"} status="Vendor supplied" detail="Canonical finding" />
            <Metric icon={<Database />} label="Observed asset" value={finding?.asset ?? "Not available"} status={finding?.asset ? "Observed identifier" : "Not available"} detail="Canonical finding" />
            <Metric icon={<Siren />} label="Incident" value={incidentContextValue} status={incidentContextStatus} detail="Linked context" error={incidentContextError} />
            <Metric icon={<Siren />} label="Command Center" value={commandCenterStatus} status="Canonical incident read" detail="Loaded state" error={incidentContextError} />
        </section>
        <span className="soc-cockpit__sr-only">Situation overview</span>
        <span className="soc-cockpit__sr-only">PredatorAI Analyst Brief</span>
        <section aria-label="Operational status" className="soc-cockpit__sr-only">{findingsError || incidentContextError ? "Unavailable" : ""}</section>
        <section className="soc-cockpit__primary">
            <InvestigationRelationshipGraph finding={finding} incident={incident} onFinding={selectFinding} onThreatIntelligence={selectThreatIntelligence} onIncident={onIncident} selectedNode={selectedNode} />
            <InvestigationStateTimeline finding={Boolean(finding)} incident={Boolean(incident)} evidence={evidenceAvailable} />
        </section>
        <section className="soc-cockpit__secondary">
            <div className="soc-cockpit__panel">{evidencePanel}</div>
            <div className="soc-cockpit__panel"><span className="soc-cockpit__eyebrow">AI ANALYSIS</span><h2>PredatorAI Analysis &amp; Assessment</h2><PredatorAIAnalysisPanel /></div>
            <div className={`soc-cockpit__panel${panelFeedbackActive ? " soc-cockpit__panel--updated" : ""}`}><span className="soc-cockpit__eyebrow">RECOMMENDED INVESTIGATION</span><h2>Next analyst actions</h2><RecommendedInvestigationPanel finding={finding} incident={incident} onFinding={onOpenFinding} onTi={onOpenThreatIntelligence} onIncident={onIncident} onCommandCenter={onCommandCenter} /></div>
        </section>
        <section className="soc-cockpit__bottom" aria-label="Operational intelligence">
            <div className="soc-cockpit__panel"><h2>Relevant Findings</h2>{relevantFindings}</div>
            <div className="soc-cockpit__panel"><h2>Incident Context</h2>{incidentContext}</div>
            <div className="soc-cockpit__panel"><h2>Asset / TI Context</h2>{assetContext}</div>
        </section>
    </main>;
}

function Metric({ icon, label, value, status, detail, error = false }: { icon: ReactNode; label: string; value: string; status: string; detail: string; error?: boolean }) {
    return <article className={`soc-cockpit__metric${error ? " soc-cockpit__metric--error" : ""}`}><div className="soc-cockpit__metric-head"><span>{label}</span>{icon}</div><strong>{value}</strong><small>{status} · {detail}</small></article>;
}
