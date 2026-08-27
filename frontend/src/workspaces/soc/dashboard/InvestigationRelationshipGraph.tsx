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
    return <section className="soc-cockpit__graph" aria-label="Investigation path">
        <header className="soc-cockpit__section-heading"><div><span className="soc-cockpit__eyebrow">RELATIONSHIP VIEW</span><h2>Investigation relationship</h2></div><span className="soc-cockpit__state-chip">RELATED CONTEXT</span></header>
        <div className="soc-cockpit__graph-canvas">
            <svg className="soc-cockpit__edges" viewBox="0 0 700 260" role="img" aria-label="Canonical investigation relationships">
                {finding?.asset && <><path data-relationship="finding-asset" d="M150 150 C230 150 250 150 275 150" /><text x="195" y="139">OBSERVED ON</text></>}
                {finding && incident && <><path data-relationship="finding-incident" d="M150 165 C310 235 430 215 500 165" /><text x="315" y="220">{incident.relationship_role}</text></>}
            </svg>
            <RelationshipNode className="soc-cockpit__node--finding" icon={<Bug />} label="FINDING" value={finding?.title ?? "No finding"} status={finding ? "KNOWN" : "NOT AVAILABLE"} selected={selectedNode === "finding"} onClick={finding ? () => onFinding(finding.id) : undefined} />
            <RelationshipNode className="soc-cockpit__node--cve" icon={<Database />} label="THREAT INTELLIGENCE" value="Relationship unavailable" status="NOT AVAILABLE" selected={selectedNode === "threat-intelligence"} onClick={finding ? () => onThreatIntelligence(finding.id) : undefined} />
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
