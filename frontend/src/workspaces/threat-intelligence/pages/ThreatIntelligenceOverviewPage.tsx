import { Activity, Bug, Crosshair, Radio, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { FindingSummary } from "@/workspaces/soc/findings/FindingSummary";
import { getFindings } from "@/workspaces/soc/findings/FindingsApiClient";
import { EnvironmentFindings } from "./ThreatIntelligenceEnvironmentPage";
import "./ThreatIntelligenceOverviewPage.css";

interface ThreatIntelligenceOverviewPageProps { loadFindings?: () => Promise<readonly FindingSummary[]>; }
const unavailableSnapshots = [{ label: "Active Campaigns", state: "Not connected", Icon: Crosshair }, { label: "Threat Actors", state: "Not connected", Icon: Activity }, { label: "New IOCs", state: "Not connected", Icon: Radio }, { label: "High Risk CVEs", state: "Unavailable", Icon: Bug }] as const;

export default function ThreatIntelligenceOverviewPage({ loadFindings = getFindings }: ThreatIntelligenceOverviewPageProps) {
    const navigate = useNavigate();
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    useEffect(() => { let active = true; loadFindings().then((result) => { if (active) setFindings(result); }).catch(() => { if (active) setError(true); }).finally(() => { if (active) setLoading(false); }); return () => { active = false; }; }, [loadFindings]);
    const findingsState = loading ? "Loading" : error ? "Unavailable" : String(findings.length);

    return <main className="ti-overview">
        <section className="ti-panel ti-snapshot" aria-labelledby="snapshot-title"><h1 id="snapshot-title" className="ti-overline">Intelligence Snapshot</h1><div className="ti-snapshot-grid">
            <article className="ti-snapshot-card"><span className="ti-icon"><ShieldCheck size={22} /></span><div><strong>{findingsState}</strong><span>Relevant Findings</span></div></article>
            {unavailableSnapshots.map(({ label, state, Icon }) => <article className="ti-snapshot-card" key={label}><span className="ti-icon"><Icon size={22} /></span><div><strong className="ti-state">{state}</strong><span>{label}</span></div></article>)}
        </div></section>
        <section className="ti-panel ti-environment" aria-labelledby="environment-title"><header><h2 id="environment-title">Our Environment</h2><p>Search and explore findings in our assets</p></header><EnvironmentFindings findings={findings} loading={loading} error={error} compact /><button className="ti-panel-action" type="button" onClick={() => navigate("/threat-intelligence/environment")}>View all results <span aria-hidden="true">→</span></button></section>
        <section className="ti-panel ti-landscape" aria-labelledby="landscape-title"><header><h2 id="landscape-title">Threat Landscape</h2><p>Current threat activity overview</p></header><div className="ti-map-stage" aria-label="Threat landscape unavailable"><div className="ti-map-shape" /><strong>Unavailable</strong><span>No geographic intelligence source is connected.</span></div></section>
        <UnavailablePanel className="ti-feeds" title="Intelligence Feeds" subtitle="Latest updates from configured sources" state="Not connected" />
        <UnavailablePanel className="ti-recent" title="Recent Intelligence" subtitle="Latest relevant intelligence for our environment" state="Unavailable" />
    </main>;
}

interface UnavailablePanelProps { className: string; title: string; subtitle: string; state: string; }
function UnavailablePanel({ className, title, subtitle, state }: UnavailablePanelProps) { return <section className={`ti-panel ti-unavailable ${className}`}><header><h2>{title}</h2><p>{subtitle}</p></header><div className="ti-list-stage"><strong>{state}</strong><span>No intelligence entries are available.</span></div></section>; }
