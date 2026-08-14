# PredatorAI v3 – Canonical Entities

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument definiert die Ubiquitous Language für die kanonischen fachlichen Entitäten von PredatorAI. Jede aufgeführte Entität besitzt eine eigenständige fachliche Identität, wird genau einer bestehenden kanonischen Domäne zugeordnet und erhält ihre fachliche Ownership ausschließlich über diese Domäne.

Das Dokument beschreibt keine Attribute, Beziehungen, Aggregate, Value Objects, Zustandsautomaten oder technische Realisierung.

## Begriffsregeln

* Ein kanonischer Name bezeichnet plattformweit genau einen fachlichen Begriff.
* Jede Canonical Entity gehört genau einer Owner-Domäne.
* Owner ist die Domäne, nicht eine Person, Rolle, ein Workspace, Team oder technisches Modul.
* Ähnliche Anzeigenamen in Workspaces erzeugen keine zusätzliche Entität.
* Ein fachliches Konzept ohne eigenständige Identität wird durch dieses Dokument nicht als Entität klassifiziert.
* `DecisionResult` bleibt gemäß ADR-0001 das kanonische fachliche Ergebnis einer abgeschlossenen Decision.
* Decision Evidence bleibt gemäß ADR-0006 von ursprünglichen Quellobjekten getrennt.
* Explainability und Execution Trace sind keine Canonical Entities dieses Katalogs.

## Enterprise Context

Fachlicher Owner aller folgenden Entitäten: **Enterprise Context**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Asset | Eindeutig identifizierbarer schutzrelevanter Gegenstand des Unternehmens. | Stellt den autoritativen Bezugspunkt für Schutzwürdigkeit und Unternehmenskontext bereit. | Enterprise Context |
| Business Service | Eindeutig identifizierbare geschäftliche Leistung des Unternehmens. | Beschreibt, welche geschäftliche Leistung geschützt und hinsichtlich ihrer Bedeutung betrachtet wird. | Enterprise Context |
| Organizational Unit | Eindeutig identifizierbarer fachlicher Organisationsbereich. | Stellt den autoritativen organisatorischen Kontext für Unternehmensgegenstände bereit. | Enterprise Context |

`Crown Jewel`, Kritikalität und Business Impact werden in diesem Task nicht als eigenständige Entitäten festgelegt. Ihre spätere Klassifikation würde eine nicht freigegebene Modellentscheidung vorwegnehmen.

## Security Observation

Fachlicher Owner aller folgenden Entitäten: **Security Observation**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Finding | Eindeutig identifizierbare fachliche Feststellung eines sicherheitsrelevanten Sachverhalts. | Hält eine bewertbare Sicherheitsfeststellung als autoritative Beobachtung fest. | Security Observation |
| Alert | Eindeutig identifizierbarer Hinweis auf einen potenziell sicherheitsrelevanten Zustand. | Macht einen prüfungsbedürftigen Sicherheitszustand als eigenständige Beobachtung adressierbar. | Security Observation |
| Exposure | Eindeutig identifizierbarer festgestellter Zustand potenzieller Angreifbarkeit. | Beschreibt einen autoritativen exponierten Sicherheitszustand ohne daraus eine Decision oder ein Enterprise Risk zu machen. | Security Observation |

`Signal`, `Telemetry` und `Detection` sind ohne zusätzliche Architekturentscheidung keine eigenständigen Canonical Entities dieses Katalogs.

## Threat Intelligence

Fachlicher Owner aller folgenden Entitäten: **Threat Intelligence**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Threat Actor | Eindeutig identifizierte oder fachlich abgegrenzte Bedrohungsquelle. | Ermöglicht eine konsistente fachliche Benennung und Bewertung einer Bedrohungsquelle. | Threat Intelligence |
| Threat Technique | Eindeutig identifizierbares Vorgehen, das einer Bedrohung zugeschrieben wird. | Stellt ein kanonisches Vokabular für beobachtete oder bekannte Vorgehensweisen bereit. | Threat Intelligence |
| Threat Indicator | Eindeutig identifizierbarer Bedrohungshinweis aus bewerteter Intelligence. | Macht einen kuratierten Hinweis unabhängig von einer unternehmensinternen Beobachtung fachlich adressierbar. | Threat Intelligence |
| Threat Campaign | Eindeutig identifizierbarer zusammenhängender Bedrohungskontext. | Bündelt die fachliche Betrachtung einer längerfristigen Bedrohungsaktivität, ohne interne Incidents zu besitzen. | Threat Intelligence |

`IOC` ist ein gebräuchlicher Anzeigename für einen Threat Indicator und begründet keine parallele Entität. `MITRE ATT&CK` bezeichnet eine Wissensquelle beziehungsweise Taxonomie, keine PredatorAI-Entität.

## Threat Hunting

Fachlicher Owner aller folgenden Entitäten: **Threat Hunting**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Hunt | Eindeutig identifizierbare proaktive Sicherheitsuntersuchung. | Macht eine geplante und fachlich geführte Hunting-Aktivität über ihren eigenen Lebenslauf adressierbar. | Threat Hunting |
| Hunt Hypothesis | Eindeutig identifizierbare, prüfbare Annahme innerhalb der Hunting-Arbeitswelt. | Formuliert den fachlichen Untersuchungsgegenstand eines proaktiven Hunts. | Threat Hunting |

`Query`, `Saved Hunt` und `Hunt Timeline` sind ohne weitere Modellentscheidung Arbeitsmittel oder Darstellungen und keine zusätzlichen Canonical Entities.

## Incident Response

Fachlicher Owner aller folgenden Entitäten: **Incident Response**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Security Incident | Eindeutig identifizierbarer bestätigter oder vermuteter Sicherheitsvorfall. | Stellt den fachlichen Gegenstand für koordinierte Eindämmung, Beseitigung, Wiederherstellung und Abschluss bereit. | Incident Response |
| Response Action | Eindeutig identifizierbare fachlich koordinierte Reaktionsmaßnahme. | Macht eine beabsichtigte oder durchgeführte Maßnahme im Response-Kontext nachvollziehbar. | Incident Response |
| Incident Communication | Eindeutig identifizierbarer fachlicher Kommunikationsvorgang eines Sicherheitsvorfalls. | Hält die koordinierte Kommunikation während der Vorfallsbearbeitung fachlich adressierbar. | Incident Response |
| Incident Review | Eindeutig identifizierbare fachliche Nachbetrachtung eines Sicherheitsvorfalls. | Trägt die dokumentierte operative Auswertung nach der Response, ohne Governance oder Enterprise Risk zu übernehmen. | Incident Response |

`Containment`, `Eradication`, `Recovery`, `Evidence Collection` und `Timeline` sind in diesem Task keine eigenständigen Entitäten. Insbesondere bleibt Decision Evidence außerhalb der Incident-Response-Ownership.

## Decision Evidence

Fachlicher Owner aller folgenden Entitäten: **Decision Evidence**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Evidence | Eindeutig identifizierbarer, unveränderlicher und provenance-pflichtiger entscheidungsrelevanter Nachweis. | Stellt die überprüfbare Tatsachengrundlage bereit, die einer fachlichen Cyber-Entscheidung zur Verfügung stand. | Decision Evidence |

`Source Evidence` und `Derived Evidence` bleiben die in ADR-0006 definierten fachlichen Arten von Evidence; dieser Task führt daraus keine zusätzlichen Entitäten ein. `Provenance` ist keine eigenständige Canonical Entity dieses Katalogs.

## Cyber Decision

Fachlicher Owner aller folgenden Entitäten: **Cyber Decision**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Decision | Eindeutig identifizierbarer fachlicher Entscheidungsvorgang. | Macht die fachliche Cyber-Entscheidung unabhängig von ihrer Darstellung oder technischen Ausführung adressierbar. | Cyber Decision |
| DecisionResult | Eindeutig identifizierbares kanonisches Ergebnis einer abgeschlossenen Decision gemäß ADR-0001. | Stellt die einzige fachliche Wahrheit über das abgeschlossene Decision-Ergebnis bereit. | Cyber Decision |

`Recommendation`, `Confidence`, `Business Impact` und `Decision Priority` werden durch diesen Task nicht als eigenständige Entitäten klassifiziert. Explainability ist ein read-only Application Read Model und keine Entität der Cyber-Decision-Domäne.

## Enterprise Risk

Fachlicher Owner aller folgenden Entitäten: **Enterprise Risk**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Enterprise Risk | Eindeutig identifizierbares Unternehmensrisiko mit eigenständigem fachlichem Lebenslauf. | Stellt den kanonischen Gegenstand für Bewertung, Ownership, Priorisierung und Steuerung eines Unternehmensrisikos bereit. | Enterprise Risk |
| Risk Treatment | Eindeutig identifizierbares fachliches Vorhaben zur Behandlung eines Unternehmensrisikos. | Macht die geplante und verfolgte Risikobehandlung als eigenen fachlichen Gegenstand adressierbar. | Enterprise Risk |
| Risk Acceptance | Eindeutig identifizierbare fachliche Annahme eines Unternehmensrisikos. | Dokumentiert die bewusste fachliche Übernahme eines Risikos, ohne eine Cyber Decision zu ersetzen. | Enterprise Risk |

`Risk Portfolio`, `Risk Trend`, `Top Business Risk` und `Ownership Summary` sind Darstellungen oder Gruppierungen und keine zusätzlichen Canonical Entities.

## Governance and Compliance

Fachlicher Owner aller folgenden Entitäten: **Governance and Compliance**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Governance Policy | Eindeutig identifizierbare verbindliche Governance-Vorgabe. | Hält eine fachlich geltende organisatorische Vorgabe kanonisch fest. | Governance and Compliance |
| Control | Eindeutig identifizierbare fachliche Kontrollvorgabe. | Beschreibt eine überprüfbare Governance- oder Compliance-Kontrolle als eigenständigen Gegenstand. | Governance and Compliance |
| Compliance Requirement | Eindeutig identifizierbare verbindliche Compliance-Anforderung. | Stellt den kanonischen fachlichen Gegenstand für die Bewertung regulatorischer oder normativer Erfüllung bereit. | Governance and Compliance |
| Governance Exception | Eindeutig identifizierbare genehmigungspflichtige Abweichung von einer Governance-Vorgabe. | Macht eine fachliche Ausnahme über ihren eigenen Lebenslauf adressierbar. | Governance and Compliance |
| Compliance Assessment | Eindeutig identifizierbare fachliche Bewertung der Compliance-Erfüllung. | Hält eine fachliche Prüfung als eigenständigen Bewertungsgegenstand fest. | Governance and Compliance |

`Compliance Status`, `Policy Status` und `Compliance Overview` sind Zustände oder Darstellungen und keine zusätzlichen Canonical Entities.

## Identity and Access

Fachlicher Owner aller folgenden Entitäten: **Identity and Access**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Principal | Eindeutig identifizierbarer Akteur, dessen Plattformzugriff autorisiert werden kann. | Stellt den kanonischen fachlichen Bezugspunkt für Identität und Zugriffsentscheidungen bereit. | Identity and Access |
| Access Role | Eindeutig identifizierbare fachliche Bündelung autorisierter Plattformverantwortung. | Ermöglicht eine konsistente fachliche Benennung wiederkehrender Zugriffsverantwortung. | Identity and Access |
| Permission | Eindeutig identifizierbare fachliche Erlaubnis für eine kontrollierte Plattformhandlung oder Datennutzung. | Stellt die kanonische Bedeutung einer gewährbaren Berechtigung bereit. | Identity and Access |
| Authorization Rule | Eindeutig identifizierbare verbindliche Regel für eine Zugriffsentscheidung. | Definiert den fachlichen Gegenstand, anhand dessen autorisierte Nutzung begrenzt wird. | Identity and Access |

`SOC Analyst`, `Threat Hunter`, `Incident Responder`, `Risk Manager`, `Executive`, `CISO` und `Administrator` sind Rollenbezeichnungen beziehungsweise Arbeitskontexte. Sie sind keine zusätzlichen Canonical Entities und dürfen nicht mit `Access Role` gleichgesetzt werden, solange keine separate Architekturentscheidung dies festlegt.

## Data Integration

Fachlicher Owner aller folgenden Entitäten: **Data Integration**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Integration | Eindeutig identifizierbare kontrollierte Anbindung einer externen Datenumgebung. | Stellt den kanonischen betrieblichen Gegenstand für die Aufnahme externer Daten bereit. | Data Integration |
| Connector | Eindeutig identifizierbarer technischer Zugang zu einer externen Quelle. | Macht den kontrollierten Zugang und dessen technischen Lebenslauf fachlich adressierbar. | Data Integration |
| Data Source | Eindeutig identifizierbare externe Herkunft aufgenommener Daten. | Stellt die kanonische Quellenbezeichnung für technische Lineage bereit. | Data Integration |
| Synchronization Run | Eindeutig identifizierbarer Synchronisierungsvorgang. | Macht die Ausführung einer kontrollierten Datenabstimmung nachvollziehbar. | Data Integration |
| Import Run | Eindeutig identifizierbarer Importvorgang. | Macht eine kontrollierte Datenaufnahme als eigenständigen betrieblichen Vorgang adressierbar. | Data Integration |

`Import Status`, `Synchronization Overview` und `Connector Status` sind Zustände oder Darstellungen und keine zusätzlichen Canonical Entities.

## Platform Operations

Fachlicher Owner aller folgenden Entitäten: **Platform Operations**.

| Canonical Entity | Kurzbeschreibung | Fachlicher Zweck | Zugehörige Domäne |
|---|---|---|---|
| Platform Service | Eindeutig identifizierbare betriebliche Plattformfähigkeit. | Stellt den kanonischen Gegenstand für die betriebliche Überwachung einer Plattformfähigkeit bereit. | Platform Operations |
| Platform Configuration | Eindeutig identifizierbare kontrollierte technische Konfiguration der Plattform. | Macht technische Betriebsfestlegungen als eigenständigen betrieblichen Gegenstand adressierbar. | Platform Operations |
| Background Job | Eindeutig identifizierbarer asynchroner Plattformvorgang. | Ermöglicht die betriebliche Nachverfolgung eines Hintergrundvorgangs. | Platform Operations |
| System Notification | Eindeutig identifizierbare betriebliche Mitteilung der Plattform. | Macht eine technische Betriebsinformation für autorisierte Empfänger adressierbar. | Platform Operations |
| Audit Record | Eindeutig identifizierbarer unveränderlicher Nachweis einer auditrelevanten Plattformaktivität. | Stellt die kanonische betriebliche Auditspur bereit, ohne den Reasoning Execution Trace zu ersetzen. | Platform Operations |
| Feature Flag | Eindeutig identifizierbare kontrollierte technische Funktionsfreigabe. | Macht die betriebliche Aktivierung einer Plattformfähigkeit adressierbar. | Platform Operations |
| License | Eindeutig identifizierbare betriebliche Nutzungsberechtigung der Plattform. | Stellt den kanonischen Gegenstand für den technischen Lizenzstatus bereit. | Platform Operations |

`Platform Health`, `Service Status`, `Audit Activity` und `System Overview` sind Zustände oder Darstellungen und keine zusätzlichen Canonical Entities. Ein `Security Incident` gehört ausschließlich zu Incident Response; eine technische Betriebsstörung wird durch diesen Task nicht als neue Entität eingeführt.

## Kanonisches Glossar und ausgeschlossene Synonyme

| Kanonischer Begriff | Abgrenzung |
|---|---|
| Threat Indicator | `IOC` ist ein möglicher Anzeigename, keine parallele Entität. |
| Security Incident | `Incident` in fachlichen Security-Kontexten bezeichnet diese Entität; technische Betriebsstörungen sind nicht umfasst. |
| Governance Policy | Von `Authorization Rule` und `Platform Configuration` getrennt. |
| Access Role | Nicht automatisch identisch mit einer Workspace- oder Berufsrolle. |
| Evidence | Ausschließlich entscheidungsrelevanter Nachweis gemäß ADR-0006; keine generische Bezeichnung für beliebige Daten. |
| DecisionResult | Kanonisches abgeschlossenes Decision-Ergebnis gemäß ADR-0001; keine UI- oder Transportprojektion. |
| Audit Record | Betrieblicher Auditnachweis; kein Reasoning Execution Trace. |
| Enterprise Risk | Langlebiges Unternehmensrisiko; weder Finding noch DecisionResult. |

## Nicht als Canonical Entities klassifiziert

Workspaces, Mission Consoles, Navigationseinträge, Seiten, Dashboards, Reports, Übersichten, KPIs, Timelines und Rollenansichten sind Presentation- oder Arbeitskonzepte. Explainability ist ein read-only Application Read Model. Der Execution Trace ist ein Application-/Audit-Artefakt einer Reasoning-Ausführung. Attribute, Klassifikationen, Statusangaben und reine Gruppierungen werden durch diesen Task ebenfalls nicht zu Entitäten erklärt.

## Nicht Bestandteil

Dieses Dokument definiert keine Attribute, Felder, Dataclasses, Domain-Klassen, Aggregate, Aggregate Roots, Value Objects, Enums, Beziehungen, Referenzen, Kardinalitäten, Zustandsautomaten, Regeln, APIs, DTOs, Events, Services, Persistenz, Datenbanken, Module, Packages oder Produktimplementierungen. Es entscheidet keine technische Migration bestehender Begriffe.

## Statische Konsistenzprüfung

* Alle zwölf bestehenden kanonischen Domänen sind enthalten.
* Jede aufgeführte Entität besitzt genau einen kanonischen Namen und genau eine Owner-Domäne.
* Kurzbeschreibung und fachlicher Zweck sind für jede Entität dokumentiert.
* Ähnliche Begriffe mit unterschiedlicher fachlicher Bedeutung sind explizit abgegrenzt.
* Rollen-, Workspace-, Read-Model-, Audit- und Presentation-Begriffe begründen keine parallelen Entitäten.
* Attribute, Beziehungen und technische Implementierungsdetails bleiben unmodelliert.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-OWNERSHIP-AND-RESPONSIBILITIES.md`
* `ARCHITECTURE.md`
* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0003-explainability-projection.md`
* `.ai/decisions/ADR-0004-explainability-completeness.md`
* `.ai/decisions/ADR-0005-mission-console-workspace-architecture.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/tasks/done/TASK-0029.md`

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
