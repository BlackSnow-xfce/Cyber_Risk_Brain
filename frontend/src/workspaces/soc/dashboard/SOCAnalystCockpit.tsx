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
    activeCve: string | null;
    findingsValue: string;
    findingsStatus: string;
    incidentContextValue: string;
    incidentContextStatus: string;
    findingsError: boolean;
    incidentContextError: boolean;
    incidentContextLoading: boolean;
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

export default function SOCAnalystCockpit({ finding, incident, activeCve, findingsValue, findingsStatus, incidentContextValue, incidentContextStatus, findingsError, incidentContextError, incidentContextLoading, toolbar, evidencePanel, relevantFindings, incidentContext, assetContext, onFinding, onThreatIntelligence, onIncident, onOpenFinding, onOpenThreatIntelligence, onCommandCenter }: SOCAnalystCockpitProps) {
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
            <div><span className="soc-cockpit__eyebrow">ACTIVE INVESTIGATION</span><h1>{finding?.title ?? "No active investigation"}</h1><div className="soc-cockpit__meta"><span>{finding?.vendorSeverity ?? "NOT AVAILABLE"}</span><span>{finding?.asset ?? "ASSET NOT AVAILABLE"}</span><span>{activeCve ?? "CVE NOT AVAILABLE"}</span><span>{incident ? "INCIDENT LINKED" : "INCIDENT NOT AVAILABLE"}</span><span>{activeCve ? "TI ON DEMAND" : "TI NOT AVAILABLE"}</span></div></div>
            <div className="soc-cockpit__header-actions">{toolbar}</div>
        </header>
        <section className="soc-cockpit__kpis" aria-label="Operational metrics">
            <h4 className="soc-cockpit__sr-only">{finding ? "1" : "0"}</h4>
            <Metric icon={<Bug />} label="Findings" value={findingsValue} status={findingsStatus} detail="Live feed" error={findingsError} />
            <Metric icon={<Activity />} label="Active investigation" value={finding ? "1" : "0"} status={finding ? "Focused" : "Not available"} detail="Current analyst context" />
            <Metric icon={<Database />} label="Asset" value={finding?.asset ?? "Not available"} status={finding ? "Bound" : "Not available"} detail="Canonical resource" />
            <Metric icon={<Database />} label="Threat intelligence" value={activeCve ?? "Not available"} status={activeCve ? "Related" : "Not available"} detail="On demand" />
            <Metric icon={<Siren />} label="Incident" value={incidentContextValue} status={incidentContextStatus} detail="Linked context" error={incidentContextError} />
        </section>
        <span className="soc-cockpit__sr-only">Situation overview</span>
        <span className="soc-cockpit__sr-only">PredatorAI Analyst Brief</span>
        <section aria-label="Operational status" className="soc-cockpit__sr-only">{findingsError || incidentContextError ? "Unavailable" : ""}</section>
        <section className="soc-cockpit__primary">
            <InvestigationRelationshipGraph finding={finding} incident={incident} onFinding={selectFinding} onThreatIntelligence={selectThreatIntelligence} onIncident={onIncident} selectedNode={selectedNode} />
            <InvestigationStateTimeline finding={Boolean(finding)} incident={Boolean(incident)} ti={Boolean(activeCve)} />
        </section>
        <section className="soc-cockpit__secondary">
            <div className="soc-cockpit__panel">{evidencePanel}</div>
            <div className="soc-cockpit__panel"><span className="soc-cockpit__eyebrow">AI ANALYSE &amp; HYPOTHESE</span><h2>PredatorAI Analysis &amp; Assessment</h2><PredatorAIAnalysisPanel finding={finding} incident={incident} loading={incidentContextLoading} /></div>
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
