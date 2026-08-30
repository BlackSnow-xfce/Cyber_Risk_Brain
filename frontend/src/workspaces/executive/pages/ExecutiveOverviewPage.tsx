import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Banknote, BarChart3, Building2, FileText, Gavel, Landmark, ListTree, Scale, ShieldCheck, Users } from "lucide-react";
import "./ExecutiveOverviewPage.css";

interface Kpi { label: string; icon: LucideIcon; tone: string }
interface EmptyTableProps { title: string; description: string; columns: string[]; emptyTitle: string; icon: LucideIcon }

const kpis: Kpi[] = [
    { label: "Enterprise Risk Posture", icon: ShieldCheck, tone: "violet" },
    { label: "Critical Exposure", icon: AlertTriangle, tone: "red" },
    { label: "Business Services at Risk", icon: Building2, tone: "orange" },
    { label: "Decisions Required", icon: Gavel, tone: "amber" },
];
const impacts = [
    { label: "People Impact", icon: Users, tone: "violet" }, { label: "Financial Impact", icon: Banknote, tone: "green" },
    { label: "Operational Impact", icon: BarChart3, tone: "orange" }, { label: "Compliance Impact", icon: Scale, tone: "blue" },
];

function Badge() { return <span className="executive-overview__badge">Not connected</span>; }
function PanelHeader({ title, description }: { title: string; description: string }) {
    return <header className="executive-overview__panel-header"><div><h2>{title}</h2><p>{description}</p></div><Badge /></header>;
}
function EmptyTable({ title, description, columns, emptyTitle, icon: Icon }: EmptyTableProps) {
    return <section className="executive-overview__panel executive-overview__table-panel">
        <PanelHeader title={title} description={description} />
        <div className="executive-overview__table" role="table" aria-label={title}>
            <div className="executive-overview__table-head" role="row">{columns.map((column) => <span role="columnheader" key={column}>{column}</span>)}</div>
            <div className="executive-overview__empty" role="row"><Icon aria-hidden="true" /><strong>{emptyTitle}</strong><span>Not connected to an authorized source.</span></div>
        </div>
    </section>;
}
function KpiCard({ label, icon: Icon, tone }: Kpi) {
    return <article className={`executive-overview__kpi executive-overview__kpi--${tone}`}>
        <div className="executive-overview__kpi-icon"><Icon aria-hidden="true" /></div><div><h2>{label}</h2><strong>Unavailable</strong><span>Not connected</span></div>
        <div className="executive-overview__neutral-scale" aria-hidden="true"><i /><i /><i /></div>
    </article>;
}

export default function ExecutiveOverviewPage() {
    return <main className="executive-overview">
        <header className="executive-overview__hero"><span className="executive-overview__legacy-name">Executive Mission Console</span><p className="executive-overview__overline">Strategic cyber risk overview</p><h1>Executive Cyber Risk Dashboard</h1><p>Enterprise risk posture, business impact and strategic priorities are shown only when connected to authorized sources.</p></header>
        <section className="executive-overview__kpis" aria-label="Executive risk indicators">
            {kpis.map((kpi) => <KpiCard {...kpi} key={kpi.label} />)}
            <article className="executive-overview__kpi executive-overview__kpi--green"><div className="executive-overview__trend-icon" aria-hidden="true"><i /><i /></div><div><h2>Risk Trend</h2><strong>Unavailable</strong><span>Not connected</span></div><div className="executive-overview__neutral-scale" aria-hidden="true"><i /><i /><i /></div></article>
        </section>
        <div className="executive-overview__grid">
            <section className="executive-overview__panel executive-overview__risk"><PanelHeader title="Enterprise Risk Overview" description="Enterprise cyber-risk distribution by risk level." /><div className="executive-overview__risk-content"><div className="executive-overview__ring"><span><strong>Unavailable</strong><small>Not connected</small></span></div><ul>{["Critical", "High", "Medium", "Low", "Informational"].map((label) => <li key={label}><i /><span>{label}</span><strong>Unavailable</strong></li>)}</ul></div></section>
            <EmptyTable title="Decision Priorities" description="Executive decisions from an authorized prioritization source." columns={["Priority", "Risk / Topic", "Business Impact", "Action Required", "Target"]} emptyTitle="No decision data available." icon={ListTree} />
            <section className="executive-overview__panel executive-overview__impact"><PanelHeader title="Business Impact" description="Authorized business-impact assessments." /><div className="executive-overview__impact-items">{impacts.map(({ label, icon: Icon, tone }) => <div className={`executive-overview__impact-item executive-overview__impact-item--${tone}`} key={label}><Icon /><strong>Unavailable</strong><span>{label}</span></div>)}</div></section>
            <EmptyTable title="Critical Business Services" description="Business services from an authorized inventory." columns={["Service", "Criticality", "Current Risk", "Trend", "Status"]} emptyTitle="No business services available." icon={Building2} />
            <EmptyTable title="Investment & Remediation Priorities" description="Approved security investment and remediation priorities." columns={["Priority", "Initiative / Control", "Risk Reduction", "Investment", "Target"]} emptyTitle="No investment data available." icon={Landmark} />
            <section className="executive-overview__panel executive-overview__briefing"><PanelHeader title="Executive Briefing" description="Authorized executive briefing and key takeaways." /><div className="executive-overview__empty"><FileText /><strong>No executive briefing available.</strong><span>Not connected to an authorized source.</span></div></section>
            <section className="executive-overview__panel executive-overview__progress"><PanelHeader title="Security Program Progress" description="Authorized security-program reporting." /><div className="executive-overview__progress-content"><div className="executive-overview__ring executive-overview__ring--small"><span><strong>Unavailable</strong><small>Not connected</small></span></div><ul>{["Program Completion", "Controls Implementation", "Risk Reduction", "Milestones Achieved"].map((label) => <li key={label}><span>{label}</span><i /><strong>Unavailable</strong></li>)}</ul></div></section>
            <section className="executive-overview__panel executive-overview__reporting"><PanelHeader title="Board Reporting" description="Board-ready reports from an authorized repository." /><div className="executive-overview__empty"><FileText /><strong>No board report available.</strong><span>Not connected to an authorized source.</span></div></section>
        </div>
        <footer className="executive-overview__footer"><span>i</span><p>Information is displayed only when connected to authorized data sources. PredatorAI does not infer, estimate or generate executive risk data.</p><strong>Status: Fail-Closed.</strong></footer>
    </main>;
}
