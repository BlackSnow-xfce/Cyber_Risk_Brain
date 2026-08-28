import { Bot, ChevronDown, Search, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";

import type { FindingSummary } from "../findings/FindingSummary";
import "./EnterpriseSOCDashboard.css";

interface EnterpriseSOCDashboardProps {
    findings: readonly FindingSummary[];
    findingsState: "loading" | "ready" | "error";
    selectedFinding?: FindingSummary | null;
    incidentStatus?: string;
    onOpenFindings: () => void;
}

const unavailableMetrics = [
    ["Overall Risk Score", "Unavailable"],
    ["Active Investigations", "Unavailable"],
    ["Risk Trend", "Unavailable"],
    ["Exposed Assets", "Unavailable"],
] as const;

export default function EnterpriseSOCDashboard({ findings, findingsState, selectedFinding, incidentStatus, onOpenFindings }: EnterpriseSOCDashboardProps) {
    const total = findingsState === "loading" ? "Loading" : findingsState === "error" ? "Unavailable" : String(findings.length);
    const severityCounts = findings.reduce<Record<string, number>>((counts, finding) => {
        counts[finding.vendorSeverity] = (counts[finding.vendorSeverity] ?? 0) + 1;
        return counts;
    }, {});
    return <main className="soc-enterprise-dashboard" aria-label="Enterprise SOC dashboard">
        <section className="dashboard-primary" aria-label="Primary dashboard metrics">
            <Metric title={unavailableMetrics[0][0]} value={unavailableMetrics[0][1]} />
            <Metric title="Total Findings" value={total} detail="Canonical findings collection" action="View All Findings" onAction={onOpenFindings} />
            <Metric title={unavailableMetrics[1][0]} value={unavailableMetrics[1][1]} detail={selectedFinding ? `${selectedFinding.title}${incidentStatus ? ` · ${incidentStatus}` : ""}` : undefined} />
            <Metric title={unavailableMetrics[2][0]} value={unavailableMetrics[2][1]} />
            <Metric title={unavailableMetrics[3][0]} value={unavailableMetrics[3][1]} />
        </section>
        <section className="dashboard-secondary" aria-label="Secondary dashboard panels">
            <Panel title="Findings by Severity"><div className="severity-list">{Object.entries(severityCounts).length ? Object.entries(severityCounts).map(([severity, count]) => <span key={severity}><i className={`severity-dot severity-${severity.toLowerCase()}`} />{severity}<strong>{count}</strong></span>) : <Empty label={findingsState === "error" ? "Unavailable" : "No findings"} />}</div></Panel>
            <Panel title="Top Risky Assets"><Empty label="Unavailable" /></Panel>
            <Panel title="AI Insights"><Empty label="Unavailable" /></Panel>
            <Panel title="AI Agents Status"><Empty label="Not configured" /></Panel>
            <Panel title="Recent Decisions"><Empty label="Unavailable" /></Panel>
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

function Metric({ title, value, detail, action, onAction }: { title: string; value: string; detail?: string; action?: string; onAction?: () => void }) {
    return <article className="dashboard-panel metric-panel"><header><h2>{title}</h2><ChevronDown size={10} /></header><strong className="metric-value">{value}</strong>{detail && <p>{detail}</p>}<div className="metric-space" />{action && <button onClick={onAction}>{action}</button>}</article>;
}
function Panel({ title, children }: { title: string; children: ReactNode }) { return <article className="dashboard-panel"><header><h2>{title}</h2><ChevronDown size={10} /></header>{children}</article>; }
function Empty({ label }: { label: string }) { return <div className="dashboard-empty">{label}</div>; }
