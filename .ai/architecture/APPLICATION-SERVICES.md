# PredatorAI v3 – Application Service Catalog

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument katalogisiert die fachlich erforderlichen Application Services von PredatorAI. Ein Application Service koordiniert einen konkreten Anwendungsfall oberhalb bestehender Aggregate, Domain Services und Domain Policies. Er trifft keine fachliche Entscheidung, besitzt keinen fachlichen Zustand und ist kein Daten-Owner.

Referenzen auf Domain Events beschreiben ausschließlich fachlich relevante, bereits eingetretene Tatsachen aus `DOMAIN-EVENTS.md`. Sie legen keine technische Verarbeitung oder Integration fest.

## Verbindliche Abgrenzung

* Application Services koordinieren den Ablauf eines Use Cases.
* Domain Services treffen aggregateübergreifende fachliche Entscheidungen innerhalb ihrer Owner Domain.
* Aggregates bleiben alleinige Zustands-, Invarianten- und Konsistenzgrenzen.
* Domain Policies begrenzen die zulässigen fachlichen Ergebnisse.
* Domain Events werden nur als bestehende fachliche Tatsachen referenziert.
* Application Services enthalten keine Geschäftslogik und besitzen keine Persistenz-, Infrastruktur- oder Integrationsverantwortung.
* Die Owner Domain bezeichnet den fachlichen Ausgangspunkt des Use Cases; sie überträgt keine Domain-Ownership an den Application Layer.

## Katalogübersicht

| Owner Domain | Application Service | Koordinierter Use Case |
|---|---|---|
| Data Integration | Data Intake Application Service | kontrollierte Zuordnung eines Aufnahmevorgangs |
| Enterprise Context | Enterprise Context Classification Application Service | autoritative Einordnung von Unternehmenskontext |
| Threat Intelligence | Threat Intelligence Assessment Application Service | domänenweite Bewertung vorhandener Intelligence |
| Security Observation | Security Observation Correlation Application Service | Korrelation bestehender Observations |
| Governance and Compliance | Governance Compliance Assessment Application Service | Geltungs- und Compliance-Bewertung |
| Identity and Access | Authorization Evaluation Application Service | fachliche Autorisierungsbewertung |
| Decision Evidence | Decision Evidence Qualification Application Service | Qualifikation vorhandener Aussagen als Evidence |
| Cyber Decision | Cyber Decision Evaluation Application Service | kanonische Decision-Bewertung und Abschluss |
| Enterprise Risk | Enterprise Risk Assessment Application Service | Bewertung und Priorisierung bestehender Risiken |

## Data Intake Application Service

**Owner Domain:** Data Integration

**Fachlicher Zweck:** Koordiniert die fachliche Zuordnung eines Import- oder Synchronisierungsvorgangs zu einer vorhandenen Integration.

**Koordinierte Use Cases und Abläufe:** Vorhandenen Integrationskontext und vorhandenen Run zusammenführen; Zuordnungsentscheidung beim Domain Service anfordern; die getrennten Aggregate-Grenzen bei der weiteren fachlichen Behandlung respektieren.

**Verwendete Domain Services:** Data Intake Coordination Service.

**Verwendete Aggregate:** Integration Aggregate; Synchronization Run Aggregate; Import Run Aggregate.

**Berücksichtigte Domain Policies:** Intake Lineage Integrity Policy.

**Relevante Domain Events:** Integration Context Established.

**Zulässige fachliche Abhängigkeiten:** Ausschließlich innerhalb von Data Integration; keine Cross-Domain-Abhängigkeit.

**Nicht zulässige fachliche Abhängigkeiten:** Alle anderen Domains sowie jede fachliche Interpretation aufgenommener Inhalte.

**Vorbehaltene Entscheidungen:** Nur der Data Intake Coordination Service entscheidet über die widerspruchsfreie Zuordnung. Integration Aggregate und Run Aggregates verantworten ihre jeweiligen Zustände und Invarianten.

**Fachliche Begründung:** Der Use Case betrifft unabhängige Integrations- und Run-Grenzen, ohne sie zu einer gemeinsamen Konsistenzgrenze zu verbinden.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine; insbesondere keine Datenübertragung, Connector-Ausführung oder Speicherung.

## Enterprise Context Classification Application Service

**Owner Domain:** Enterprise Context

**Fachlicher Zweck:** Koordiniert die autoritative fachliche Einordnung vorhandener Asset-, Business-Service- und Organisationskontexte.

**Koordinierte Use Cases und Abläufe:** Vorhandene Context-Aussagen und zulässige Herkunft bereitstellen; Klassifikationsentscheidung anfordern; das Ergebnis ausschließlich in den jeweils verantwortenden Aggregate-Grenzen berücksichtigen.

**Verwendete Domain Services:** Enterprise Context Classification Service.

**Verwendete Aggregate:** Asset Context Aggregate; Business Service Context Aggregate; Organizational Unit Context Aggregate; Integration Aggregate ausschließlich als Herkunftsreferenz.

**Berücksichtigte Domain Policies:** Authoritative Context Classification Policy.

**Relevante Domain Events:** Integration Context Established; Asset Context Classified; Business Service Context Classified; Organizational Context Established.

**Zulässige fachliche Abhängigkeiten:** Data Integration gemäß `Enterprise Context → Data Integration`.

**Nicht zulässige fachliche Abhängigkeiten:** Alle übrigen Domains; insbesondere Security Observation, Cyber Decision und Enterprise Risk als Rückreferenz.

**Vorbehaltene Entscheidungen:** Nur der Enterprise Context Classification Service entscheidet über die aggregateübergreifende Einordnung. Jedes Context Aggregate besitzt seine eigene Identität, Kritikalität und Konsistenz.

**Fachliche Begründung:** Der Use Case koordiniert mehrere unabhängige Context-Aussagen und eine autoritative Herkunft, ohne Context-Ownership zu vermischen.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine.

## Threat Intelligence Assessment Application Service

**Owner Domain:** Threat Intelligence

**Fachlicher Zweck:** Koordiniert die konsistente Bewertung vorhandener Threat-Intelligence-Aussagen.

**Koordinierte Use Cases und Abläufe:** Vorhandene Actor-, Technique-, Indicator- und Campaign-Aussagen sowie zulässige Herkunft bereitstellen; domänenweite Bewertung anfordern; Aggregate-Eigenständigkeit bewahren.

**Verwendete Domain Services:** Threat Intelligence Assessment Service.

**Verwendete Aggregate:** Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate; Integration Aggregate ausschließlich als Herkunftsreferenz.

**Berücksichtigte Domain Policies:** Intelligence Provenance and Assessment Integrity Policy.

**Relevante Domain Events:** Integration Context Established; Threat Indicator Assessed; Threat Technique Assessed.

**Zulässige fachliche Abhängigkeiten:** Data Integration gemäß `Threat Intelligence → Data Integration`.

**Nicht zulässige fachliche Abhängigkeiten:** Alle übrigen Domains, insbesondere Security Observation und Decision Evidence als Rückreferenz.

**Vorbehaltene Entscheidungen:** Nur der Threat Intelligence Assessment Service entscheidet über die domänenweite Bewertung. Die vier Intelligence Aggregates verantworten ihre eigenen Aussagen.

**Fachliche Begründung:** Der Use Case verbindet eine bewertende Koordination mehrerer eigenständiger Intelligence-Aggregates mit vorhandener Herkunft.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine.

## Security Observation Correlation Application Service

**Owner Domain:** Security Observation

**Fachlicher Zweck:** Koordiniert die fachliche Korrelation bereits autoritativ festgestellter Security Observations.

**Koordinierte Use Cases und Abläufe:** Vorhandene Findings, Alerts und Exposures mit zulässigem Asset- und Indicator-Kontext bereitstellen; Korrelationsentscheidung anfordern; jede Observation als eigenständige Aussage erhalten.

**Verwendete Domain Services:** Security Observation Correlation Service.

**Verwendete Aggregate:** Finding Aggregate; Alert Aggregate; Exposure Aggregate; Asset Context Aggregate; Threat Indicator Aggregate.

**Berücksichtigte Domain Policies:** Observation Correlation Integrity Policy.

**Relevante Domain Events:** Asset Context Classified; Threat Indicator Assessed; Finding Established; Alert Established; Exposure Established.

**Zulässige fachliche Abhängigkeiten:** Enterprise Context und Threat Intelligence gemäß den erlaubten Richtungen von Security Observation.

**Nicht zulässige fachliche Abhängigkeiten:** Threat Hunting, Decision Evidence, Cyber Decision, Incident Response, Enterprise Risk und alle weiteren verbotenen Richtungen.

**Vorbehaltene Entscheidungen:** Nur der Security Observation Correlation Service entscheidet über gemeinsame Betrachtung. Finding, Alert und Exposure behalten ihre jeweilige Konsistenzgrenze.

**Fachliche Begründung:** Der Use Case koordiniert mehrere unabhängige Observations mit autoritativem Kontext, ohne Evidence, Incident oder Decision zu erzeugen.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine.

## Governance Compliance Assessment Application Service

**Owner Domain:** Governance and Compliance

**Fachlicher Zweck:** Koordiniert die Bewertung von Governance-Geltung und Compliance gegenüber vorhandenen Unternehmenskontexten und Findings.

**Koordinierte Use Cases und Abläufe:** Vorhandene Policy-, Requirement-, Context- und Finding-Aussagen bereitstellen; Geltungs- beziehungsweise Bewertungsentscheidung anfordern; Ergebnisse in ihren jeweiligen Governance-Aggregates belassen.

**Verwendete Domain Services:** Governance Compliance Evaluation Service.

**Verwendete Aggregate:** Governance Policy Aggregate; Compliance Requirement Aggregate; Organizational Unit Context Aggregate; Business Service Context Aggregate; Finding Aggregate.

**Berücksichtigte Domain Policies:** Governance Applicability and Exception Integrity Policy.

**Relevante Domain Events:** Organizational Context Established; Business Service Context Classified; Finding Established; Governance Policy Changed; Compliance Requirement Assessed.

**Zulässige fachliche Abhängigkeiten:** Enterprise Context und Security Observation gemäß den erlaubten Richtungen von Governance and Compliance.

**Nicht zulässige fachliche Abhängigkeiten:** Cyber Decision, Enterprise Risk, Identity and Access und alle weiteren verbotenen Richtungen.

**Vorbehaltene Entscheidungen:** Nur der Governance Compliance Evaluation Service entscheidet über domänenweite Geltung und Bewertung. Governance Policy und Compliance Requirement behalten getrennte Konsistenzgrenzen.

**Fachliche Begründung:** Der Use Case koordiniert zwei Governance-Aggregates mit autoritativen externen Aussagen, ohne Findings, Context oder Risk Acceptance zu besitzen.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine.

## Authorization Evaluation Application Service

**Owner Domain:** Identity and Access

**Fachlicher Zweck:** Koordiniert die fachliche Bewertung, ob ein Principal in einem vorhandenen organisatorischen Kontext handeln oder Daten nutzen darf.

**Koordinierte Use Cases und Abläufe:** Principal, Rolle, Permission, Authorization Rule und Organisationskontext bereitstellen; Autorisierungsentscheidung anfordern; alle beteiligten Aggregate unverändert lassen.

**Verwendete Domain Services:** Authorization Decision Service.

**Verwendete Aggregate:** Principal Aggregate; Access Role Aggregate; Permission Aggregate; Authorization Rule Aggregate; Organizational Unit Context Aggregate.

**Berücksichtigte Domain Policies:** Contextual Authorization Policy.

**Relevante Domain Events:** Organizational Context Established; Authorization Rule Changed.

**Zulässige fachliche Abhängigkeiten:** Enterprise Context gemäß `Identity and Access → Enterprise Context`.

**Nicht zulässige fachliche Abhängigkeiten:** Platform Operations als Rückreferenz sowie alle fachlichen Security-, Decision- und Risk-Domains.

**Vorbehaltene Entscheidungen:** Nur der Authorization Decision Service entscheidet fachlich über die Autorisierung. Principal, Access Role, Permission und Authorization Rule behalten ihre Zustände und Gültigkeit.

**Fachliche Begründung:** Der Use Case benötigt mehrere unabhängige Identity-and-Access-Aussagen und einen autoritativen Organisationskontext.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine; insbesondere keine technische Zugriffsdurchsetzung.

## Decision Evidence Qualification Application Service

**Owner Domain:** Decision Evidence

**Fachlicher Zweck:** Koordiniert die Qualifikation vorhandener autoritativer Aussagen als entscheidungsrelevante Evidence.

**Koordinierte Use Cases und Abläufe:** Zulässige Source-Aussage und vorhandene Herkunft bereitstellen; Evidence-Qualifikation anfordern; die resultierende Aussage ausschließlich im Evidence Aggregate verantworten.

**Verwendete Domain Services:** Decision Evidence Qualification Service.

**Verwendete Aggregate:** Evidence Aggregate; Finding Aggregate; Alert Aggregate; Exposure Aggregate; Threat Indicator Aggregate; Hunt Aggregate; Governance Policy Aggregate.

**Berücksichtigte Domain Policies:** Evidence Admissibility and Provenance Policy.

**Relevante Domain Events:** Finding Established; Alert Established; Exposure Established; Threat Indicator Assessed; Hunt Concluded; Governance Policy Changed; Evidence Qualified.

**Zulässige fachliche Abhängigkeiten:** Security Observation, Threat Intelligence, Threat Hunting und Governance and Compliance gemäß den erlaubten Richtungen von Decision Evidence.

**Nicht zulässige fachliche Abhängigkeiten:** Cyber Decision, Incident Response, Enterprise Risk, Enterprise Context und alle weiteren verbotenen Richtungen.

**Vorbehaltene Entscheidungen:** Nur der Decision Evidence Qualification Service entscheidet über fachliche Eignung, Art, Relevanz und Herkunft. Source Aggregates und Evidence Aggregate behalten ihre getrennte Ownership.

**Fachliche Begründung:** Der Use Case koordiniert mehrere autoritative Source Domains zu einer provenance-pflichtigen Evidence-Aussage, ohne Quellen zu verändern oder Fakten zu erzeugen.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine.

## Cyber Decision Evaluation Application Service

**Owner Domain:** Cyber Decision

**Fachlicher Zweck:** Koordiniert die Bewertung und den Abschluss genau einer kanonischen Cyber Decision aus zulässigen vorhandenen Eingaben.

**Koordinierte Use Cases und Abläufe:** Qualifizierte Evidence, Business-Service-Kontext und Governance Policy bereitstellen; fachliche Decision-Bewertung anfordern; den Abschluss innerhalb des Decision Aggregate koordinieren.

**Verwendete Domain Services:** Cyber Decision Evaluation Service.

**Verwendete Aggregate:** Decision Aggregate; Evidence Aggregate; Business Service Context Aggregate; Governance Policy Aggregate.

**Berücksichtigte Domain Policies:** Canonical Decision Basis Policy.

**Relevante Domain Events:** Evidence Qualified; Business Service Context Classified; Governance Policy Changed; Decision Completed.

**Zulässige fachliche Abhängigkeiten:** Decision Evidence, Enterprise Context und Governance and Compliance gemäß den erlaubten Richtungen von Cyber Decision.

**Nicht zulässige fachliche Abhängigkeiten:** Security Observation und Threat Intelligence als direkte Quellen sowie Incident Response und Enterprise Risk als Rückreferenzen.

**Vorbehaltene Entscheidungen:** Nur der Cyber Decision Evaluation Service trifft die fachliche Decision-Bewertung. Das Decision Aggregate verantwortet Lifecycle und `DecisionResult`; Evidence und Source Context bleiben getrennt.

**Fachliche Begründung:** Der Use Case koordiniert autorisierte Eingaben über mehrere Domain-Grenzen, ohne parallele Decision-Logik oder eine zweite Wahrheit einzuführen.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine; Explainability und Execution Trace werden nicht orchestriert oder erzeugt.

## Enterprise Risk Assessment Application Service

**Owner Domain:** Enterprise Risk

**Fachlicher Zweck:** Koordiniert Bewertung und Priorisierung vorhandener Enterprise Risks anhand autoritativer Decision-, Business- und Governance-Aussagen.

**Koordinierte Use Cases und Abläufe:** Vorhandenes Enterprise Risk und zulässige Eingangsaussagen bereitstellen; vergleichende Bewertung oder Priorisierung anfordern; Risk-Entscheidungen im Enterprise Risk Aggregate belassen.

**Verwendete Domain Services:** Enterprise Risk Assessment Service.

**Verwendete Aggregate:** Enterprise Risk Aggregate; Decision Aggregate; Business Service Context Aggregate; Governance Policy Aggregate.

**Berücksichtigte Domain Policies:** Risk Ownership and Treatment Authority Policy.

**Relevante Domain Events:** Decision Completed; Business Service Context Classified; Governance Policy Changed; Enterprise Risk Treatment Decided.

**Zulässige fachliche Abhängigkeiten:** Cyber Decision, Enterprise Context und Governance and Compliance gemäß den erlaubten Richtungen von Enterprise Risk.

**Nicht zulässige fachliche Abhängigkeiten:** Decision Evidence, Security Observation, Incident Response und alle weiteren verbotenen Richtungen.

**Vorbehaltene Entscheidungen:** Nur der Enterprise Risk Assessment Service entscheidet über vergleichende Bewertung und Priorisierung. Das Enterprise Risk Aggregate verantwortet Rating, Treatment, Acceptance und seinen Lebenslauf.

**Fachliche Begründung:** Der Use Case verbindet langfristige Risikosteuerung mit vorhandenen autoritativen Eingaben, ohne DecisionResult, Business Context oder Governance Policy umzuschreiben.

**Persistenz-, Infrastruktur- und Integrationsverantwortung:** Keine; Reporting und Executive-Darstellung sind nicht Bestandteil.

## Domains ohne eigenen Application Service

### Threat Hunting

Hunt und Hunt Hypothesis liegen gemeinsam im Hunt Aggregate; die freigegebenen Hunting-Abläufe besitzen keinen bestehenden Domain Service und keine zusätzliche aggregateübergreifende Orchestrierungsentscheidung. Ein Application Service würde im aktuellen Architekturstand entweder nur die Aggregate-Verantwortung wiederholen oder nicht freigegebene Ablaufsemantik erfinden.

### Incident Response

Security Incident, Response Action, Incident Communication und Incident Review liegen gemeinsam im Security Incident Aggregate. Die gesamte freigegebene Response-Koordination ist Teil dieser Konsistenzgrenze; ein zusätzlicher Application Service ohne vorhandenen Domain Service hätte keine eigenständige, belegte Orchestrierungsverantwortung.

### Platform Operations

Die Platform-Operations-Aggregates besitzen getrennte technische Lebensläufe. Es existiert weder ein fachlicher Domain Service noch eine freigegebene aggregateübergreifende fachliche Policy für eine gemeinsame Orchestrierung. Technische Betriebskoordination ist ausdrücklich kein Application Service dieses Katalogs.

## Verantwortungsprüfung

| Application Service | Orchestriert | Entscheidet ausdrücklich nicht |
|---|---|---|
| Data Intake Application Service | Intake-Zuordnung | fachliche Zuordnung durch den Data Intake Coordination Service |
| Enterprise Context Classification Application Service | Context-Klassifikationsablauf | Schutzrelevanz durch den Enterprise Context Classification Service |
| Threat Intelligence Assessment Application Service | Intelligence-Bewertungsablauf | domänenweite Bewertung durch den Threat Intelligence Assessment Service |
| Security Observation Correlation Application Service | Korrelationsablauf | Korrelation durch den Security Observation Correlation Service |
| Governance Compliance Assessment Application Service | Geltungs- und Bewertungsablauf | Compliance-Bewertung durch den Governance Compliance Evaluation Service |
| Authorization Evaluation Application Service | Autorisierungsablauf | Autorisierung durch den Authorization Decision Service |
| Decision Evidence Qualification Application Service | Evidence-Qualifikationsablauf | Evidence-Eignung durch den Decision Evidence Qualification Service |
| Cyber Decision Evaluation Application Service | Decision-Bewertungsablauf | Decision-Aussage durch den Cyber Decision Evaluation Service |
| Enterprise Risk Assessment Application Service | Risk-Bewertungsablauf | Priorisierung durch den Enterprise Risk Assessment Service |

Kein Application Service besitzt Aggregate-Zustand, Geschäftsregeln, fachliche Ownership oder eine eigene Konsistenzgrenze.

## Konsistenz mit ADR-0001 bis ADR-0007

* `DecisionResult` bleibt gemäß ADR-0001 ausschließlich beim Decision Aggregate.
* Execution Trace bleibt gemäß ADR-0002 ein getrenntes Application-/Audit-Artefakt und ist kein Application Service.
* Explainability und Completeness bleiben gemäß ADR-0003 und ADR-0004 read-only; kein Service erzeugt fehlende Fakten.
* Workspaces bleiben gemäß ADR-0005 Presentation-Grenzen und begründen keine Application Services.
* Evidence-Qualifikation respektiert gemäß ADR-0006 Unveränderlichkeit, Provenance und getrennte Ownership.
* Alle Abhängigkeiten respektieren gemäß ADR-0007 exklusive Ownership, definierte Verträge und die Domain-Layer-Richtung.

## Nicht Bestandteil

Dieses Dokument definiert keinen Produktcode, keine Implementierung, Klassen, Interfaces, Methoden, REST-Endpunkte, FastAPI, Controller, DTOs, Commands, Queries, Events, Event-Verarbeitung, Repositorys, Persistenz, Datenbanken, Infrastruktur, Integrationsadapter, Messaging, Dependency Injection, Transaktionen, Module, Packages oder Deployments. Es verändert keine bestehende Domain, Entity, Value Object, Aggregate, Relationship, Dependency Rule, Domain Service, Domain Policy, Domain Event oder ADR.

## Statische Konsistenzprüfung

* Neun Application Services besitzen jeweils einen eindeutigen Namen und genau eine Owner Domain.
* Drei Domains sind mit fachlicher Begründung ausdrücklich ohne eigenen Application Service dokumentiert; alle zwölf Domains sind berücksichtigt.
* Alle referenzierten Domain Services stammen aus `DOMAIN-SERVICES.md`.
* Alle referenzierten Aggregate stammen aus `AGGREGATE-BOUNDARIES.md`.
* Alle referenzierten Policies stammen aus `DOMAIN-POLICIES.md`.
* Alle Event-Referenzen stammen unverändert aus `DOMAIN-EVENTS.md`.
* Alle Cross-Domain-Abhängigkeiten entsprechen `AGGREGATE-RELATIONSHIPS.md` und `DOMAIN-DEPENDENCIES.md`.
* Kein Application Service übernimmt Geschäftslogik, Aggregate-Konsistenz, Persistenz, Infrastruktur oder Integration.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `.ai/architecture/DOMAIN-DEPENDENCIES.md`
* `.ai/architecture/DOMAIN-SERVICES.md`
* `.ai/architecture/DOMAIN-POLICIES.md`
* `.ai/architecture/DOMAIN-EVENTS.md`
* ADR-0001 bis ADR-0007
* AIDP TASK-0040

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
