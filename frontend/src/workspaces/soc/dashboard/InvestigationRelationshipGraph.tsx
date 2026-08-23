import { Bug, Database, Server, Siren } from "lucide-react";
import type { ReactNode } from "react";
import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

import "./SOCAnalystCockpit.css";

interface InvestigationRelationshipGraphProps {
    finding: FindingSummary | null;
    incident: FindingIncidentReference | null;
    onFinding: (id: string) => void;
    onThreatIntelligence: (id: string) => void;
    onIncident: (id: string) => void;
    selectedNode: "finding" | "threat-intelligence" | null;
}

export default function InvestigationRelationshipGraph({ finding, incident, onFinding, onThreatIntelligence, onIncident, selectedNode }: InvestigationRelationshipGraphProps) {
    const cve = finding?.title.match(/CVE-\d{4}-\d+/i)?.[0] ?? null;
    return <section className="soc-cockpit__graph" aria-label="Investigation path">
        <header className="soc-cockpit__section-heading"><div><span className="soc-cockpit__eyebrow">RELATIONSHIP VIEW</span><h2>Investigation relationship</h2></div><span className="soc-cockpit__state-chip">RELATED CONTEXT</span></header>
        <div className="soc-cockpit__graph-canvas">
            <svg className="soc-cockpit__edges" viewBox="0 0 700 260" role="img" aria-label="Finding related to threat intelligence, bound to asset, linked to incident">
                <path d="M150 130 H275" /><path d="M350 92 V112" /><path d="M425 145 H500" />
                <text x="205" y="119">RELATED</text><text x="365" y="105">BOUND</text><text x="455" y="134">LINKED</text>
            </svg>
            <RelationshipNode className="soc-cockpit__node--finding" icon={<Bug />} label="FINDING" value={finding?.title ?? "No finding"} status={finding ? "KNOWN" : "NOT AVAILABLE"} selected={selectedNode === "finding"} onClick={finding ? () => onFinding(finding.id) : undefined} />
            <RelationshipNode className="soc-cockpit__node--cve" icon={<Database />} label="Threat intelligence / CVE" value={cve ?? "Identifier unavailable"} status={cve ? "RELATED" : "NOT AVAILABLE"} selected={selectedNode === "threat-intelligence"} onClick={finding && cve ? () => onThreatIntelligence(finding.id) : undefined} />
            <RelationshipNode className="soc-cockpit__node--asset" icon={<Server />} label="CANONICAL ASSET" value={finding?.asset ?? "Asset unavailable"} status={finding ? "BOUND" : "NOT AVAILABLE"} />
            <RelationshipNode className="soc-cockpit__node--incident" icon={<Siren />} label="INCIDENT" value={incident?.incident_id ?? "No incident"} status={incident ? "LINKED" : "NOT AVAILABLE"} onClick={incident ? () => onIncident(incident.incident_id) : undefined} />
        </div>
    </section>;
}

function RelationshipNode({ className, icon, label, value, status, selected = false, onClick }: { className: string; icon: ReactNode; label: string; value: string; status: string; selected?: boolean; onClick?: () => void }) {
    const Tag = onClick ? "button" : "div";
    const interactionClass = onClick ? "soc-cockpit__node--interactive" : "soc-cockpit__node--static";
    return <Tag className={`soc-cockpit__node ${interactionClass} ${selected ? "soc-cockpit__node--selected" : ""} ${className}`} type={onClick ? "button" : undefined} aria-pressed={onClick ? selected : undefined} onClick={onClick}><span className="soc-cockpit__node-icon">{icon}</span><span className="soc-cockpit__node-label">{label}</span><strong>{value}</strong><span className="soc-cockpit__node-status">{status}</span></Tag>;
}
