import { Bot, ChevronDown, Search, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";

import type { FindingSummary } from "../findings/FindingSummary";
import "./EnterpriseSOCDashboard.css";

interface EnterpriseSOCDashboardProps {
    findings: readonly FindingSummary[];
    findingsState: "loading" | "ready" | "error";
    selectedFinding?: FindingSummary | null;
    incidentStatus?: string;
    hasLinkedIncident?: boolean;
    onOpenFindings: () => void;
    onOpenFinding?: () => void;
    onOpenThreatIntelligence?: () => void;
    onOpenIncident?: () => void;
    onOpenCommandCenter?: () => void;
}

export default function EnterpriseSOCDashboard({ findings, findingsState, selectedFinding, incidentStatus, hasLinkedIncident = false, onOpenFindings, onOpenFinding, onOpenThreatIntelligence, onOpenIncident, onOpenCommandCenter }: EnterpriseSOCDashboardProps) {
    const total = findingsState === "loading" ? "Loading" : findingsState === "error" ? "Unavailable" : String(findings.length);
    const severityCounts = findings.reduce<Record<string, number>>((counts, finding) => {
        counts[finding.vendorSeverity] = (counts[finding.vendorSeverity] ?? 0) + 1;
        return counts;
    }, {});
    return <main className="soc-enterprise-dashboard" aria-label="Enterprise SOC dashboard">
        <section className="dashboard-primary" aria-label="Primary dashboard metrics">
            <Metric title="Overall Risk Score" value="Unavailable" visual={<GaugeShell />} />
            <Metric title="Total Findings" value={total} detail="Canonical findings collection" action="View All Findings" onAction={onOpenFindings} />
            <Metric title="Active Investigations" value="Unavailable" detail={selectedFinding ? `${selectedFinding.title}${incidentStatus ? ` · ${incidentStatus}` : ""}` : undefined} action="View Incident" onAction={onOpenIncident} actionDisabled={!hasLinkedIncident} />
            <Metric title="Risk Trend" visual={<TrendShell />} />
            <Metric title="Exposed Assets" value="Unavailable" visual={<DonutShell variant="exposure" />} className="exposed-assets-panel" />
        </section>
        <section className="dashboard-secondary" aria-label="Secondary dashboard panels">
            <Panel title="Findings by Severity" action="View Finding" onAction={onOpenFinding} actionDisabled={!selectedFinding}><div className="severity-visual"><DonutShell variant="severity" /><div className="severity-list">{Object.entries(severityCounts).length ? Object.entries(severityCounts).map(([severity, count]) => <span key={severity}><i className={`severity-dot severity-${severity.toLowerCase()}`} />{severity}<strong>{count}</strong></span>) : <Empty label={findingsState === "error" ? "Unavailable" : "No findings"} />}</div></div></Panel>
            <Panel title="Top Risky Assets"><Empty label="Unavailable" /></Panel>
            <Panel title="AI Insights" action="View Threat Intelligence" onAction={onOpenThreatIntelligence} actionDisabled={!selectedFinding}><Empty label="Unavailable" /></Panel>
            <Panel title="AI Agents Status"><div className="status-visual"><DonutShell variant="status" /><Empty label="Not configured" /></div></Panel>
            <Panel title="Recent Decisions" action="Open Command Center" onAction={onOpenCommandCenter} actionDisabled={!hasLinkedIncident}><Empty label="Unavailable" /></Panel>
        </section>
        <section className="agents-split" aria-label="AI agents workspace">
            <div className="agents-list">
                <header><div><h2>AI Agents</h2><p>Manage and monitor your AI agents</p></div><button disabled>+ New Agent</button><button disabled>View Marketplace</button></header>
                <div className="agent-summary">{["Total Agents", "Active", "Idle", "Error", "Disabled"].map((label) => <span key={label}><strong>—</strong><small>{label}</small></span>)}</div>
                <div className="agent-filters"><button disabled><Search size={10} />Search agents…</button><button disabled>All Status <ChevronDown size={9} /></button><button disabled>All Types <ChevronDown size={9} /></button><button disabled><SlidersHorizontal size={9} />Filters</button></div>
                <table><thead><tr><th>Agent Name</th><th>Type</th><th>Status</th><th>Last Activity</th><th>Performance (7d)</th><th>Actions</th></tr></thead><tbody><tr><td colSpan={6}><Empty label="AI agents are not configured" /></td></tr></tbody></table>
                <footer>Showing 0 agents <span>1</span></footer>
            </div>
            <div className="agent-detail">
                <header><span className="agent-icon"><Bot size={18} /></span><div><h2>No agent selected</h2><p>AI agent inventory is not configured</p></div><button disabled>Configure</button><button disabled>Run Analysis</button></header>
                <nav>{["Overview", "Activity", "Performance", "Configuration", "Explainability", "History"].map((tab) => <span key={tab}>{tab}</span>)}</nav>
                <div className="agent-detail-grid"><Panel title="Agent Information"><Empty label="Not configured" /></Panel><div><Panel title="Performance"><Empty label="Unavailable" /></Panel><Panel title="Recent Activity"><Empty label="Unavailable" /></Panel></div><div><Panel title="Capabilities"><Empty label="Not configured" /></Panel><Panel title="Explainability"><Empty label="Unavailable" /></Panel></div></div>
            </div>
        </section>
    </main>;
}

function Metric({ title, value, detail, action, onAction, actionDisabled, visual, className }: { title: string; value?: string; detail?: string; action?: string; onAction?: () => void; actionDisabled?: boolean; visual?: ReactNode; className?: string }) {
    return <article className={`dashboard-panel metric-panel${className ? ` ${className}` : ""}`}><header><h2>{title}</h2><ChevronDown size={10} /></header>{visual}{value && <strong className="metric-value">{value}</strong>}{detail && <p>{detail}</p>}<div className="metric-space" />{action && <button disabled={actionDisabled} onClick={onAction}>{action}</button>}</article>;
}
function Panel({ title, children, action, onAction, actionDisabled }: { title: string; children: ReactNode; action?: string; onAction?: () => void; actionDisabled?: boolean }) { return <article className="dashboard-panel"><header><h2>{title}</h2><ChevronDown size={10} /></header>{children}{action && <button className="panel-action" disabled={actionDisabled} onClick={onAction}>{action}</button>}</article>; }
function Empty({ label }: { label: string }) { return <div className="dashboard-empty">{label}</div>; }
function GaugeShell() { return <div className="gauge-shell" role="img" aria-label="Overall risk score gauge unavailable"><span /></div>; }
function TrendShell() { return <div className="trend-shell" role="img" aria-label="Risk trend chart unavailable"><span className="trend-plot-area"><i className="trend-axis trend-axis-y" /><i className="trend-axis trend-axis-x" /><span className="trend-unavailable">Unavailable</span></span></div>; }
function DonutShell({ variant }: { variant: "exposure" | "severity" | "status" }) { return <div className={`donut-shell donut-shell-${variant}`} role="img" aria-label={`${variant} visualization`}><span /></div>; }
