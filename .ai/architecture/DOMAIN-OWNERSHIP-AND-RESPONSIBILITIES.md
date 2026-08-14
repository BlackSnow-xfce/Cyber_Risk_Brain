# PredatorAI v3 – Domain Ownership and Responsibilities

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument konkretisiert die fachliche Verantwortung der zwölf bereits in `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md` definierten kanonischen Domänen. Es ordnet jedem fachlichen Gegenstand genau eine verantwortliche Domäne zu und macht Nicht-Zuständigkeiten explizit.

`Primary Owner` bezeichnet ausschließlich die kanonische fachliche Ownership. Der Begriff benennt weder eine Person noch eine Rolle, ein Team, einen Workspace, ein Modul oder eine technische Komponente.

## Geltende Regeln

* Die Domänenliste und ihre Grenzen bleiben unverändert.
* Jede fachliche Wahrheit besitzt genau einen Primary Owner.
* Andere Domänen dürfen eine autoritative fachliche Verantwortung nutzen, aber nicht als eigene Wahrheit neu definieren.
* Zulässige Abhängigkeiten beschreiben nur die Nutzung vorhandener fachlicher Verantwortung auf hoher Ebene.
* Abhängigkeiten definieren keine Beziehungen, Kardinalitäten, Austauschverträge, Abläufe oder technische Kopplung.
* Backend bleibt fachliche Single Source of Truth.
* Workspaces, Rollen und Darstellungen besitzen keine fachliche Domain Ownership.
* Decision, Decision Evidence, Explainability und Execution Trace bleiben gemäß ADR-0001 bis ADR-0006 getrennt.

## Ownership-Übersicht

| Kanonische Domäne | Primary Owner für |
|---|---|
| Enterprise Context | autoritativen Unternehmens- und Schutzkontext |
| Security Observation | autoritative sicherheitsrelevante Beobachtungen |
| Threat Intelligence | autoritative bewertete Bedrohungsinformationen |
| Threat Hunting | proaktive Hunt-Verantwortung und Hunt-Lifecycle |
| Incident Response | Vorfallskoordination und Response-Lifecycle |
| Decision Evidence | entscheidungsrelevante, unveränderliche Nachweise |
| Cyber Decision | kanonische fachliche Cyber-Entscheidungen |
| Enterprise Risk | langlebige Unternehmensrisiken und deren Behandlung |
| Governance and Compliance | verbindliche Governance- und Compliance-Anforderungen |
| Identity and Access | Identitäten, Berechtigungen und Autorisierungsregeln |
| Data Integration | kontrollierte externe Datenaufnahme und technische Lineage |
| Platform Operations | Betrieb und technische Konfiguration der Plattform |

## Enterprise Context

**Primary Owner:** Enterprise Context ist alleiniger fachlicher Owner des autoritativen Unternehmens- und Schutzkontexts.

**Fachliche Verantwortung:** Die Domäne verantwortet die eindeutige fachliche Einordnung dessen, was für das Unternehmen geschützt wird, einschließlich der dafür geltenden Identität, Kritikalität und organisatorischen Bedeutung.

**Verantwortungsgrenzen:** Sie bestätigt Unternehmenskontext und Schutzrelevanz. Sie bewertet weder einen beobachteten Sicherheitszustand noch trifft sie eine Cyber- oder Risikoentscheidung. Eine Verwendung ihres Kontexts durch andere Domänen ändert ihre Ownership nicht.

**Ausdrücklich nicht zuständig für:** Security Findings, Alerts, Exposures, Threat Intelligence, Hunts, Incidents, Decision Evidence, DecisionResult, Enterprise-Risk-Lifecycle, Compliance-Bewertungen, Berechtigungen oder Plattformbetrieb.

**Zulässige fachliche Abhängigkeiten:** Die Domäne darf kontrolliert auf durch Data Integration bereitgestellte Quellzuordnung zurückgreifen. Weitere fachliche Abhängigkeiten sind für ihre Kernverantwortung nicht erforderlich.

## Security Observation

**Primary Owner:** Security Observation ist alleiniger fachlicher Owner autoritativer sicherheitsrelevanter Beobachtungen.

**Fachliche Verantwortung:** Die Domäne verantwortet die Bedeutung und den fachlichen Zustand normalisierter Findings, Alerts, Exposures und anderer beobachteter Sicherheitszustände einschließlich ihres Quellbezugs.

**Verantwortungsgrenzen:** Sie beschreibt, was beobachtet wurde. Sie bestimmt nicht, ob daraus ein Hunt, Incident, entscheidungsrelevanter Nachweis, eine Decision oder ein Enterprise Risk entsteht.

**Ausdrücklich nicht zuständig für:** Asset- oder Business-Kontext, Threat-Intelligence-Wahrheit, Hunt-Hypothesen, Incident-Koordination, Evidence-Snapshots, Decisions, Risikobehandlung, Autorisierung oder Connector-Betrieb.

**Zulässige fachliche Abhängigkeiten:** Sie darf Enterprise Context zur fachlichen Einordnung, Threat Intelligence zur autorisierten Kontextualisierung und Data Integration zur Herkunft aufgenommener Daten nutzen.

## Threat Intelligence

**Primary Owner:** Threat Intelligence ist alleiniger fachlicher Owner bewerteter Bedrohungsinformationen.

**Fachliche Verantwortung:** Die Domäne verantwortet die fachliche Aussage, Herkunft, Gültigkeit und Einordnung kuratierter Informationen über Bedrohungsakteure, Techniken, Indikatoren und Kampagnen.

**Verantwortungsgrenzen:** Sie beschreibt Bedrohungswissen, nicht dessen Auftreten im Unternehmen. Eine interne Übereinstimmung oder Bewertung wird außerhalb dieser Domäne verantwortet und verändert die Intelligence-Quelle nicht.

**Ausdrücklich nicht zuständig für:** interne Beobachtungen, Enterprise Context, Hunt-Lifecycle, Incident-Lifecycle, Decision Evidence, Decisions, Enterprise Risks oder Plattformintegrationen.

**Zulässige fachliche Abhängigkeiten:** Sie darf Data Integration zur kontrollierten Herkunft externer Informationen nutzen. Weitere Domänen können ihre autoritativen Aussagen verwenden; daraus entsteht keine rückwärtige Ownership.

## Threat Hunting

**Primary Owner:** Threat Hunting ist alleiniger fachlicher Owner proaktiver Hunts und ihres fachlichen Lifecycles.

**Fachliche Verantwortung:** Die Domäne verantwortet Hunt-Zweck, Hypothese, Untersuchungsabsicht, Suchkontext und fachlichen Fortschritt einer proaktiven Untersuchung.

**Verantwortungsgrenzen:** Sie steuert die Untersuchung, besitzt aber weder die untersuchten Quelldaten noch daraus entstehende Findings, Incidents, Evidence oder Decisions. Eine Eskalation begründet außerhalb des Hunts eine neue fachliche Verantwortung.

**Ausdrücklich nicht zuständig für:** Quelltelemetrie, Findings, Threat-Intelligence-Fakten, Incident-Koordination, Evidence-Wahrheit, DecisionResult, Enterprise-Risk-Behandlung oder Plattformjobs.

**Zulässige fachliche Abhängigkeiten:** Sie darf Security Observation, Threat Intelligence und Enterprise Context als autoritative fachliche Eingaben nutzen. Decision Evidence darf nur als bereits verantwortete Nachweisgrundlage genutzt werden, ohne sie umzudeuten.

## Incident Response

**Primary Owner:** Incident Response ist alleiniger fachlicher Owner der Vorfallskoordination und des Response-Lifecycles.

**Fachliche Verantwortung:** Die Domäne verantwortet die fachliche Koordination eines bestätigten oder vermuteten Sicherheitsvorfalls, seine Response-Phase, Maßnahmensteuerung, Kommunikation und den fachlichen Abschluss.

**Verantwortungsgrenzen:** Sie koordiniert die Reaktion, besitzt aber nicht die zugrunde liegenden Beobachtungen, Unternehmenskontexte oder Nachweise. Sie verändert keine autoritativen Quellen, um den Vorfallsstatus zu begründen.

**Ausdrücklich nicht zuständig für:** Findings, Alerts, Asset-Stammdaten, Threat Intelligence, Hunt-Lifecycle, Decision Evidence, DecisionResult, Enterprise-Risk-Portfolio, Plattformjobs oder technische Auditaktivität.

**Zulässige fachliche Abhängigkeiten:** Sie darf Security Observation, Enterprise Context, Decision Evidence und Cyber Decision als autoritative Eingaben für die Koordination nutzen.

## Decision Evidence

**Primary Owner:** Decision Evidence ist alleiniger fachlicher Owner der unveränderlichen, provenance-pflichtigen und entscheidungsrelevanten Nachweisrepräsentation.

**Fachliche Verantwortung:** Die Domäne verantwortet, welche überprüfbare Aussage einer Decision als Source oder Derived Evidence zur Verfügung stand und wie diese auf eine autoritative Quelle zurückgeführt werden kann.

**Verantwortungsgrenzen:** Sie besitzt die entscheidungsrelevante Nachweisrepräsentation, nicht das ursprüngliche Quellobjekt und nicht die daraus getroffene Decision. Sie erzeugt keine unbelegten Tatsachen und erklärt keine Entscheidung.

**Ausdrücklich nicht zuständig für:** ursprüngliche Findings, Assets, Intelligence oder Governance-Anforderungen, Hunt- oder Incident-Lifecycle, DecisionResult, Explainability, Execution Trace oder Enterprise-Risk-Behandlung.

**Zulässige fachliche Abhängigkeiten:** Sie darf autoritative Aussagen aus Enterprise Context, Security Observation, Threat Intelligence, Threat Hunting, Incident Response sowie Governance and Compliance nutzen, sofern deren fachliche Herkunft erhalten bleibt. Die Nutzung bleibt den Regeln aus ADR-0006 unterworfen.

## Cyber Decision

**Primary Owner:** Cyber Decision ist alleiniger fachlicher Owner der kanonischen Cyber-Entscheidung und ihres abgeschlossenen Ergebnisses.

**Fachliche Verantwortung:** Die Domäne verantwortet den fachlichen Decision-Lifecycle und `DecisionResult` als einzige kanonische Wahrheit über das Ergebnis einer abgeschlossenen Decision.

**Verantwortungsgrenzen:** Sie entscheidet auf Basis autorisierter Evidence. Sie besitzt weder die ursprünglichen Quellen noch Explainability, Execution Trace oder den langfristigen Enterprise-Risk-Lifecycle. Verbraucher dürfen das Ergebnis nicht umschreiben.

**Ausdrücklich nicht zuständig für:** Quellsystemdaten, Findings, Threat Intelligence, Hunt- oder Incident-Koordination, ursprüngliche Evidence-Quellen, Explainability-Projektionen, technische Ausführungsspuren, Risikoportfolio oder Plattformbetrieb.

**Zulässige fachliche Abhängigkeiten:** Sie darf ausschließlich Decision Evidence als fachliche Tatsachengrundlage sowie die dafür geltenden Governance-Vorgaben und autorisierten Unternehmenskontexte nutzen. ADR-0001 und ADR-0006 bleiben verbindlich.

## Enterprise Risk

**Primary Owner:** Enterprise Risk ist alleiniger fachlicher Owner langlebiger Unternehmensrisiken und ihrer fachlichen Behandlung.

**Fachliche Verantwortung:** Die Domäne verantwortet Identifikation, Bewertung, fachliche Ownership, Priorisierung, Treatment, Acceptance, Eskalation und Portfolio-Sicht eines Unternehmensrisikos.

**Verantwortungsgrenzen:** Sie steuert das Unternehmensrisiko über seinen Lebenszyklus. Sie besitzt weder technische Beobachtungen noch Einzelentscheidungen, Unternehmensstammdaten oder Governance-Anforderungen. Eingehende Decisions bleiben unveränderte Quellen.

**Ausdrücklich nicht zuständig für:** Findings, Alerts, Hunts, Incidents, Decision Evidence, DecisionResult, Policies, Compliance-Prüfstatus, Berechtigungen oder Executive-Darstellungen.

**Zulässige fachliche Abhängigkeiten:** Sie darf Enterprise Context, Cyber Decision sowie Governance and Compliance als autoritative fachliche Eingaben nutzen.

## Governance and Compliance

**Primary Owner:** Governance and Compliance ist alleiniger fachlicher Owner verbindlicher Governance- und Compliance-Anforderungen und ihres fachlichen Prüfstatus.

**Fachliche Verantwortung:** Die Domäne verantwortet die Geltung und Bewertung von Policies, Controls, Compliance-Anforderungen und Exceptions.

**Verantwortungsgrenzen:** Sie definiert Anforderungen und bewertet deren Erfüllung. Sie besitzt weder die daraus entstehenden Beobachtungen oder Risiken noch fachliche Risikoakzeptanz, Decisions oder Zugriffsrechte.

**Ausdrücklich nicht zuständig für:** Enterprise Context, Security Findings, Threat Intelligence, Incidents, Decision Evidence, DecisionResult, Enterprise-Risk-Ownership, Identitäten, Berechtigungen oder Plattformkonfiguration.

**Zulässige fachliche Abhängigkeiten:** Sie darf Enterprise Context zur Bestimmung des fachlichen Geltungsbereichs und Security Observation als autoritative Feststellung eines beobachteten Zustands nutzen.

## Identity and Access

**Primary Owner:** Identity and Access ist alleiniger fachlicher Owner von Identitäten, Rollen, Berechtigungen, Organisationszuordnung und Autorisierungsregeln innerhalb der Plattform.

**Fachliche Verantwortung:** Die Domäne verantwortet, wer innerhalb welcher autorisierten Grenze welche Plattformhandlung ausführen oder welche Daten nutzen darf.

**Verantwortungsgrenzen:** Sie kontrolliert Zugriff und Handlungsbefugnis, besitzt aber keine durch den Zugriff sichtbaren oder bearbeiteten fachlichen Daten. Eine Workspace-Rolle begründet keine Ownership an Security-, Decision- oder Risk-Daten.

**Ausdrücklich nicht zuständig für:** Workspace-Darstellung, Unternehmensrisiko-Ownership, Security-Beobachtungen, Hunts, Incidents, Evidence, Decisions, Governance-Inhalte oder technische Plattformkonfiguration.

**Zulässige fachliche Abhängigkeiten:** Sie darf Enterprise Context ausschließlich für den autoritativen organisatorischen Geltungsbereich nutzen. Fachliche Entscheidungen anderer Domänen werden nicht zu Autorisierungsregeln umgedeutet.

## Data Integration

**Primary Owner:** Data Integration ist alleiniger fachlicher Owner der kontrollierten externen Datenaufnahme, technischen Quellzuordnung und Übertragungsnachvollziehbarkeit.

**Fachliche Verantwortung:** Die Domäne verantwortet Integrationsdefinition, Connector-Zuordnung, Import- und Synchronisationszustand sowie technische Lineage bis zur kontrollierten Übergabe an eine fachlich verantwortliche Domäne.

**Verantwortungsgrenzen:** Sie transportiert und ordnet Quellen zu, interpretiert deren Inhalt aber nicht als fachliche Wahrheit der Zieldomäne. Nach fachlicher Zuordnung verbleibt Integrations-Lineage hier, während die Zieldomäne ihre eigene fachliche Aussage besitzt.

**Ausdrücklich nicht zuständig für:** Unternehmenskontext, Security Findings, Threat Intelligence, Evidence, Decisions, Enterprise Risks, Identitäten, Autorisierung oder Gesamtzustand der Plattform.

**Zulässige fachliche Abhängigkeiten:** Für ihre Kernverantwortung benötigt sie keine fachliche Abhängigkeit auf eine andere kanonische Domäne. Identity and Access darf ihre Nutzung autorisieren; Platform Operations darf ihren technischen Betrieb überwachen, ohne ihre Ownership zu übernehmen.

## Platform Operations

**Primary Owner:** Platform Operations ist alleiniger fachlicher Owner des sicheren Plattformbetriebs und der kontrollierten technischen Plattformkonfiguration.

**Fachliche Verantwortung:** Die Domäne verantwortet Plattform- und Servicezustand, technische Konfiguration, Hintergrundaufträge, technische Benachrichtigungen, Auditaktivität, Feature-Freigaben und Lizenzstatus.

**Verantwortungsgrenzen:** Sie hält die Plattform betriebsfähig, interpretiert technische Zustände aber nicht als Cyberlage, Incident, Evidence, Decision oder Enterprise Risk. Der Reasoning Execution Trace bleibt das getrennte Application-/Audit-Artefakt gemäß ADR-0002.

**Ausdrücklich nicht zuständig für:** Security Findings, Threat Intelligence, Hunts, Incidents, Decision Evidence, DecisionResult, Enterprise Risks, Compliance-Inhalte, Identitäten oder fachliche Daten externer Quellen.

**Zulässige fachliche Abhängigkeiten:** Sie darf Identity and Access für autorisierte Betriebsaktionen und Data Integration für den technischen Integrationszustand nutzen. Sie benötigt keine fachlichen Inhalte der übrigen Domänen zur Bestimmung ihrer eigenen Verantwortung.

## Überschneidungsfreie Entscheidungskriterien

Zur eindeutigen Zuordnung gilt jeweils genau eine Leitfrage:

| Leitfrage | Verantwortliche Domäne |
|---|---|
| Was wird im Unternehmen geschützt? | Enterprise Context |
| Was wurde sicherheitsrelevant beobachtet? | Security Observation |
| Welches bewertete Bedrohungswissen liegt vor? | Threat Intelligence |
| Welche proaktive Untersuchung wird geführt? | Threat Hunting |
| Wie wird ein Sicherheitsvorfall koordiniert? | Incident Response |
| Welche überprüfbare Aussage stand einer Decision zur Verfügung? | Decision Evidence |
| Welche kanonische Cyber-Entscheidung wurde getroffen? | Cyber Decision |
| Welches Unternehmensrisiko wird wie verantwortet und behandelt? | Enterprise Risk |
| Welche Governance- oder Compliance-Anforderung gilt? | Governance and Compliance |
| Wer darf innerhalb welcher Grenze handeln oder Daten nutzen? | Identity and Access |
| Woher wurden externe Daten technisch aufgenommen? | Data Integration |
| Wie wird die PredatorAI-Plattform betrieben und konfiguriert? | Platform Operations |

Kann ein Gegenstand nicht durch genau eine dieser Leitfragen eingeordnet werden, ist seine Ownership durch dieses Dokument nicht freigegeben. Eine Mehrfachzuordnung ist unzulässig und erfordert vor einer späteren Umsetzung eine separate Architekturklärung.

## Abgeleitete und technische Verantwortungen

Die Decision Explainability Projection besitzt gemäß ADR-0003 und ADR-0004 keine fachliche Wahrheit, sondern projiziert kanonische Decision-Daten read-only. Der Execution Trace dokumentiert gemäß ADR-0002 eine Reasoning-Ausführung und besitzt keine Decision- oder Evidence-Semantik. Workspaces, Reports, Dashboards und Timelines sind Darstellungen oder Arbeitskontexte. APIs, Services, Events, Datenbanken, Module und Packages sind mögliche technische Realisierungen. Keine dieser Strukturen ist durch ihre Existenz Primary Owner eines fachlichen Gegenstands.

## Nicht Bestandteil

Dieses Dokument definiert oder verändert keine Domäne. Es führt keine Entitäten, Aggregate, Value Objects, Beziehungen, Kardinalitäten, APIs, DTOs, Services, Events, Persistenz, Datenbanken, Module, Packages, Workspaces oder Produktimplementierungen ein. Es weist keine Verantwortung an Personen, Rollen, Teams oder technische Komponenten zu.

## Statische Konsistenzprüfung

* Alle zwölf Domänen aus `CANONICAL-DOMAIN-BOUNDARIES.md` sind genau einmal als Primary Owner aufgeführt.
* Jede Domäne besitzt eine eigene Leitfrage und eine explizite Nicht-Zuständigkeit.
* Gemeinsam verwendete Informationen behalten ihre kanonische Owner-Domäne.
* Zulässige Abhängigkeiten beschreiben nur fachliche Nutzung auf hoher Ebene.
* Es werden keine fachlichen oder technischen Beziehungen modelliert.
* Die Trennung von Decision, Evidence, Explainability und Execution Trace bleibt erhalten.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `ARCHITECTURE.md`
* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0003-explainability-projection.md`
* `.ai/decisions/ADR-0004-explainability-completeness.md`
* `.ai/decisions/ADR-0005-mission-console-workspace-architecture.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/tasks/done/TASK-0028.md`

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
