# PredatorAI v3 – Domain Dependencies

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument definiert die zulässigen und verbotenen fachlichen Abhängigkeiten zwischen den zwölf kanonischen PredatorAI-Domänen. Es konsolidiert die Aggregate Boundaries und die 39 Beziehungen aus `.ai/architecture/AGGREGATE-RELATIONSHIPS.md` zu verbindlichen Domain-Regeln.

Die Regeln beschreiben ausschließlich fachliche Zulässigkeit. Sie definieren keine Kommunikation, Datenübertragung, technische Kopplung oder Implementierung.

## Dependency Direction

Eine Abhängigkeit zeigt immer von der fachlich nutzenden Source Domain zur autoritativen Target Domain:

```text
Source Domain ──depends on──► Target Domain
```

Die Target Domain behält ihre vollständige Ownership. Eine erlaubte Abhängigkeit berechtigt weder zur Mutation noch zur Duplikation oder Umdeutung der autoritativen fachlichen Aussage.

## Fachliche Layer

Die Layer sind topologische fachliche Abhängigkeitsstufen. Sie sind keine Software-, Modul-, Deployment- oder Team-Layer. Eine Domain darf ausschließlich von einer Domain eines niedrigeren Layers abhängen.

| Layer | Bezeichnung | Domains | Regel |
|---|---|---|---|
| L0 | Source Integration | Data Integration | Besitzt keine fachliche Domain-Abhängigkeit. |
| L1 | Authoritative Context | Enterprise Context; Threat Intelligence | Darf ausschließlich L0 nutzen. |
| L2 | Observation and Access Control | Security Observation; Identity and Access | Darf ausschließlich L0 oder L1 nutzen, soweit durch Aggregate-Beziehungen belegt. |
| L3 | Investigation, Governance and Platform Control | Threat Hunting; Governance and Compliance; Platform Operations | Darf ausschließlich L0 bis L2 nutzen, soweit belegt. |
| L4 | Decision Evidence | Decision Evidence | Darf ausschließlich L0 bis L3 nutzen, soweit belegt. |
| L5 | Cyber Decision | Cyber Decision | Darf ausschließlich L0 bis L4 nutzen, soweit belegt. |
| L6 | Response and Enterprise Steering | Incident Response; Enterprise Risk | Darf ausschließlich L0 bis L5 nutzen, soweit belegt. |

Eine niedrigere Layernummer bedeutet nicht höhere fachliche Wichtigkeit. Sie beschreibt ausschließlich, dass die dortige fachliche Aussage ohne Abhängigkeit auf einen höheren Layer autoritativ bleiben muss.

## Domain Rules

### Data Integration

**Domain Name:** Data Integration  
**Layer:** L0 – Source Integration  
**Allowed Dependencies:** Keine  
**Forbidden Dependencies:** Enterprise Context; Threat Intelligence; Security Observation; Identity and Access; Threat Hunting; Governance and Compliance; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** Keine ausgehende fachliche Domain-Abhängigkeit.  
**Begründung:** Data Integration verantwortet technische Quellzuordnung und Aufnahme. Würde sie von der fachlichen Interpretation höherer Domänen abhängen, entstünde eine Rückreferenz und die Quell-Lineage wäre nicht mehr unabhängig autoritativ.

### Enterprise Context

**Domain Name:** Enterprise Context  
**Layer:** L1 – Authoritative Context  
**Allowed Dependencies:** Data Integration  
**Forbidden Dependencies:** Threat Intelligence; Security Observation; Identity and Access; Threat Hunting; Governance and Compliance; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L1 → L0  
**Begründung:** Enterprise Context darf kontrollierte Quellherkunft nutzen, muss aber unabhängig von Beobachtung, Entscheidung, Governance und operativen Arbeitsabläufen autoritativ bleiben.

### Threat Intelligence

**Domain Name:** Threat Intelligence  
**Layer:** L1 – Authoritative Context  
**Allowed Dependencies:** Data Integration  
**Forbidden Dependencies:** Enterprise Context; Security Observation; Identity and Access; Threat Hunting; Governance and Compliance; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L1 → L0  
**Begründung:** Threat Intelligence darf ihre kontrollierte externe Herkunft nutzen. Interne Beobachtungen, Hunts oder Decisions dürfen die autoritative Intelligence-Aussage nicht rückwärts bestimmen.

### Security Observation

**Domain Name:** Security Observation  
**Layer:** L2 – Observation and Access Control  
**Allowed Dependencies:** Enterprise Context; Threat Intelligence  
**Forbidden Dependencies:** Data Integration; Identity and Access; Threat Hunting; Governance and Compliance; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L2 → L1  
**Begründung:** Security Observation darf beobachtete Zustände mit autoritativem Unternehmens- und Bedrohungskontext einordnen. Sie darf nicht von späteren Untersuchungs-, Evidence-, Decision-, Response- oder Risk-Grenzen abhängen.

### Identity and Access

**Domain Name:** Identity and Access  
**Layer:** L2 – Observation and Access Control  
**Allowed Dependencies:** Enterprise Context  
**Forbidden Dependencies:** Data Integration; Threat Intelligence; Security Observation; Threat Hunting; Governance and Compliance; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L2 → L1  
**Begründung:** Identity and Access darf autoritativen organisatorischen Kontext referenzieren. Fachliche Security-, Decision-, Risk- oder Betriebszustände dürfen Identität und Autorisierungsregeln nicht rückwärts besitzen oder bestimmen.

### Threat Hunting

**Domain Name:** Threat Hunting  
**Layer:** L3 – Investigation, Governance and Platform Control  
**Allowed Dependencies:** Security Observation; Threat Intelligence  
**Forbidden Dependencies:** Data Integration; Enterprise Context; Identity and Access; Governance and Compliance; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L3 → L2 oder L1  
**Begründung:** Threat Hunting untersucht autoritative Beobachtungen mithilfe autoritativer Intelligence. Eine direkte Abhängigkeit auf spätere Evidence-, Decision- oder Response-Grenzen würde den dokumentierten azyklischen Untersuchungsweg umkehren.

### Governance and Compliance

**Domain Name:** Governance and Compliance  
**Layer:** L3 – Investigation, Governance and Platform Control  
**Allowed Dependencies:** Enterprise Context; Security Observation  
**Forbidden Dependencies:** Data Integration; Threat Intelligence; Identity and Access; Threat Hunting; Platform Operations; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L3 → L2 oder L1  
**Begründung:** Governance and Compliance darf Geltungsbereich und autoritative Beobachtungen nutzen. Evidence, Decisions und Risks dürfen Anforderungen konsumieren, aber die geltenden Vorgaben nicht rückwärts definieren.

### Platform Operations

**Domain Name:** Platform Operations  
**Layer:** L3 – Investigation, Governance and Platform Control  
**Allowed Dependencies:** Data Integration; Identity and Access  
**Forbidden Dependencies:** Enterprise Context; Threat Intelligence; Security Observation; Threat Hunting; Governance and Compliance; Decision Evidence; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L3 → L2 oder L0  
**Begründung:** Platform Operations darf autorisierte Betriebsgrenzen und den Integrationszustand nutzen. Fachliche Cyber-, Decision- und Risk-Daten sind keine Voraussetzung für Plattformbetrieb und dürfen nicht zur betrieblichen Ownership werden.

### Decision Evidence

**Domain Name:** Decision Evidence  
**Layer:** L4 – Decision Evidence  
**Allowed Dependencies:** Threat Intelligence; Security Observation; Threat Hunting; Governance and Compliance  
**Forbidden Dependencies:** Data Integration; Enterprise Context; Identity and Access; Platform Operations; Cyber Decision; Incident Response; Enterprise Risk  
**Dependency Direction:** L4 → L3, L2 oder L1  
**Begründung:** Decision Evidence benötigt autoritative fachliche Quellen, um provenance-pflichtige Nachweise zu bilden. Sie darf nicht von der Decision oder späteren Response- und Risk-Grenzen abhängen, damit Evidence keine rückwirkend erzeugte Entscheidungsbegründung wird.

### Cyber Decision

**Domain Name:** Cyber Decision  
**Layer:** L5 – Cyber Decision  
**Allowed Dependencies:** Enterprise Context; Governance and Compliance; Decision Evidence  
**Forbidden Dependencies:** Data Integration; Threat Intelligence; Security Observation; Identity and Access; Threat Hunting; Platform Operations; Incident Response; Enterprise Risk  
**Dependency Direction:** L5 → L4, L3 oder L1  
**Begründung:** Cyber Decision nutzt den autoritativen Unternehmenskontext, geltende Vorgaben und überprüfbare Evidence. Direkte Rückabhängigkeiten auf Response oder Enterprise Risk würden `DecisionResult` als Single Source of Truth verletzen.

### Incident Response

**Domain Name:** Incident Response  
**Layer:** L6 – Response and Enterprise Steering  
**Allowed Dependencies:** Enterprise Context; Security Observation; Decision Evidence; Cyber Decision  
**Forbidden Dependencies:** Data Integration; Threat Intelligence; Identity and Access; Threat Hunting; Governance and Compliance; Platform Operations; Enterprise Risk  
**Dependency Direction:** L6 → L5, L4, L2 oder L1  
**Begründung:** Incident Response koordiniert einen Vorfall anhand autoritativer Kontexte, Beobachtungen, Nachweise und Decisions. Keine dieser Target-Grenzen darf von der Vorfallskoordination rückwärts abhängig werden.

### Enterprise Risk

**Domain Name:** Enterprise Risk  
**Layer:** L6 – Response and Enterprise Steering  
**Allowed Dependencies:** Enterprise Context; Governance and Compliance; Cyber Decision  
**Forbidden Dependencies:** Data Integration; Threat Intelligence; Security Observation; Identity and Access; Threat Hunting; Platform Operations; Decision Evidence; Incident Response  
**Dependency Direction:** L6 → L5, L3 oder L1  
**Begründung:** Enterprise Risk steuert langlebige Unternehmensrisiken anhand autoritativer Business-Kontexte, Vorgaben und Decisions. Eine Rückabhängigkeit dieser Quellen auf das Risk-Portfolio würde Ownership umkehren und Zyklen erzeugen.

## Vollständige Domain-Dependency-Matrix

Zeilen sind Source Domains, Spalten sind Target Domains.

* `ALLOWED`: mindestens eine bestehende Aggregate-Beziehung belegt diese Richtung.
* `FORBIDDEN`: keine fachliche Abhängigkeit in dieser Richtung zulässig.
* `SELF`: keine domänenübergreifende Abhängigkeit; interne Konsistenz bleibt innerhalb der Domain Boundaries.

| Source \ Target | DI | EC | TI | SO | IA | TH | GC | PO | DE | CD | IR | ER |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DI | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| EC | ALLOWED | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| TI | ALLOWED | FORBIDDEN | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| SO | FORBIDDEN | ALLOWED | ALLOWED | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| IA | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| TH | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED | FORBIDDEN | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| GC | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| PO | ALLOWED | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| DE | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED | FORBIDDEN | ALLOWED | ALLOWED | FORBIDDEN | SELF | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| CD | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | SELF | FORBIDDEN | FORBIDDEN |
| IR | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED | SELF | FORBIDDEN |
| ER | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | SELF |

### Abkürzungen

| Kürzel | Domain |
|---|---|
| DI | Data Integration |
| EC | Enterprise Context |
| TI | Threat Intelligence |
| SO | Security Observation |
| IA | Identity and Access |
| TH | Threat Hunting |
| GC | Governance and Compliance |
| PO | Platform Operations |
| DE | Decision Evidence |
| CD | Cyber Decision |
| IR | Incident Response |
| ER | Enterprise Risk |

## Rückführung auf Aggregate Relationships

Die 39 Aggregate-Beziehungen bilden 25 eindeutige gerichtete Domain-Abhängigkeiten. Jede `ALLOWED`-Zelle der Matrix entspricht mindestens einer dieser Beziehungen. Mehrere Aggregate-Beziehungen dürfen dieselbe Domain-Richtung belegen, ohne eine zusätzliche Domain-Abhängigkeit zu erzeugen.

`FORBIDDEN` bedeutet nicht, dass eine Domain niemals dargestellt oder autorisiert werden darf. Es bedeutet ausschließlich, dass die Source keine fachliche Abhängigkeit auf die Target-Ownership besitzen darf. Presentation, Zugriffskontrolle und technische Kommunikation werden durch dieses Dokument nicht modelliert.

## Zyklus- und Layerprüfung

Der Domain-Graph ist azyklisch. Für jede erlaubte Kante gilt:

```text
Layer(Source) > Layer(Target)
```

Damit existieren:

* keine Abhängigkeiten innerhalb derselben fachlichen Layerstufe,
* keine Rückreferenzen von einem niedrigeren zu einem höheren Layer,
* keine wechselseitigen Domain-Abhängigkeiten,
* und kein gerichteter Zyklus über mehrere Domänen.

## Verbotene Rückreferenzen

Insbesondere verboten bleiben:

* Data Integration → fachlich interpretierende Domänen,
* Enterprise Context oder Threat Intelligence → Security Observation und spätere Layer,
* Security Observation → Threat Hunting, Decision Evidence, Cyber Decision, Incident Response oder Enterprise Risk,
* Decision Evidence → Cyber Decision, Incident Response oder Enterprise Risk,
* Cyber Decision → Incident Response oder Enterprise Risk,
* Incident Response ↔ Enterprise Risk in beiden Richtungen,
* sowie jede fachliche Abhängigkeit auf Platform Operations, sofern sie nicht selbst Source ist.

Diese Verbote schützen Quellownership, verhindern nachträgliche Plausibilisierung und halten `DecisionResult`, Evidence, Explainability und Execution Trace entsprechend ADR-0001 bis ADR-0006 getrennt.

## Nicht Bestandteil

Dieses Dokument definiert keine APIs, DTOs, Events, Commands, Queries, Services, Repositorys, Persistenz, Datenbanken, Messaging, ACLs, Datenflüsse, Netzwerkkommunikation, Transaktionen, Module, Packages, Deployments, Attribute, Methoden, Geschäftslogik, UI oder Produktimplementierung.

## Statische Konsistenzprüfung

* Alle zwölf Domains besitzen genau einen Layer und vollständige Allowed/Forbidden-Regeln.
* Die Matrix enthält zwölf Source-Zeilen und zwölf Target-Spalten.
* Die Diagonale enthält ausschließlich `SELF`; alle übrigen 132 Zellen sind `ALLOWED` oder `FORBIDDEN`.
* 25 `ALLOWED`-Zellen entsprechen exakt den 25 eindeutigen Domain-Richtungen aus allen 39 Aggregate-Beziehungen.
* Keine erlaubte Abhängigkeit verletzt eine Aggregate- oder Domain Boundary.
* Für jede erlaubte Kante liegt das Target in einem niedrigeren Layer als die Source.
* Der gerichtete Domain-Graph ist azyklisch.
* Technische Kommunikation und Implementierung bleiben unmodelliert.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-OWNERSHIP-AND-RESPONSIBILITIES.md`
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `ARCHITECTURE.md`
* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0003-explainability-projection.md`
* `.ai/decisions/ADR-0004-explainability-completeness.md`
* `.ai/decisions/ADR-0005-mission-console-workspace-architecture.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/tasks/done/TASK-0033.md`

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
