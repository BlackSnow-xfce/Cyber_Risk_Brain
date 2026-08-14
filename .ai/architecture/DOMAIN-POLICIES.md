# PredatorAI v3 – Domain Policies Catalog

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument katalogisiert die fachlich erforderlichen Domain Policies von PredatorAI. Eine Domain Policy ist eine technologieunabhängige Regel oder Entscheidungsrichtlinie, die innerhalb genau einer Owner Domain gilt, aber nicht sinnvoll als Invariante genau eines einzelnen Aggregates beschrieben werden kann.

Policies begrenzen fachliche Entscheidungen bestehender Aggregates und Domain Services. Sie besitzen keinen Zustand, übernehmen keine Aggregate-Ownership und ersetzen keinen Domain Service. Der Katalog führt weder technische Policies noch neue fachliche Verantwortlichkeiten ein.

## Verbindliche Abgrenzung

* Jede Policy besitzt genau eine Owner Domain.
* Eine domänenübergreifend geltende Policy bleibt Eigentum ihrer Owner Domain; andere Domains liefern ausschließlich autoritative Aussagen über erlaubte Abhängigkeiten.
* Aggregate behalten ihre Zustände, Lebensläufe, Invarianten und Konsistenzgrenzen.
* Domain Services koordinieren die bereits katalogisierten fachlichen Entscheidungen; Policies beschränken deren zulässiges Ergebnis.
* Eine Policy verändert keine Aussage einer anderen Domain und begründet keine gemeinsame Ownership.
* Persistenz, Infrastruktur und technische Durchsetzung liegen außerhalb jeder Policy dieses Katalogs.
* Unveränderlich bedeutet, dass die fachliche Regel selbst nicht situationsabhängig aufgehoben oder plausibilisiert werden darf. Änderungen an einer solchen Regel erfordern eine neue freigegebene Architekturgrundlage.

## Katalogübersicht

| Owner Domain | Domain Policy | Geltung | Unveränderliche Geschäftsregel |
|---|---|---|---|
| Enterprise Context | Authoritative Context Classification Policy | domänenübergreifend | Ja |
| Security Observation | Observation Correlation Integrity Policy | domänenübergreifend | Ja |
| Threat Intelligence | Intelligence Provenance and Assessment Integrity Policy | domänenübergreifend | Ja |
| Decision Evidence | Evidence Admissibility and Provenance Policy | domänenübergreifend | Ja |
| Cyber Decision | Canonical Decision Basis Policy | domänenübergreifend | Ja |
| Enterprise Risk | Risk Ownership and Treatment Authority Policy | domänenübergreifend | Ja |
| Governance and Compliance | Governance Applicability and Exception Integrity Policy | domänenübergreifend | Ja |
| Identity and Access | Contextual Authorization Policy | domänenübergreifend | Ja |
| Data Integration | Intake Lineage Integrity Policy | domänenintern | Ja |

## Authoritative Context Classification Policy

**Owner Domain:** Enterprise Context

**Fachlicher Zweck:** Sicherstellen, dass die Schutzrelevanz eines Unternehmensgegenstands ausschließlich aus autoritativen Context-Aussagen und einer nachvollziehbaren Herkunft eingeordnet wird.

**Betroffene Aggregate:** Asset Context Aggregate; Business Service Context Aggregate; Organizational Unit Context Aggregate; Integration Aggregate ausschließlich als autoritative Herkunftsaussage.

**Betroffene Domain Services:** Enterprise Context Classification Service.

**Auslösende fachliche Bedingungen:** Eine fachliche Einordnung der Schutzrelevanz betrifft Aussagen aus mehr als einem Context Aggregate oder berücksichtigt die Herkunft eines aufgenommenen Asset-Kontexts.

**Erwartetes fachliches Ergebnis:** Eine widerspruchsfreie Einordnung, die jede Context-Aussage bei ihrer Aggregate Root belässt und ausschließlich die vorhandene Integration-Lineage nutzt. Fehlende Context- oder Herkunftsaussagen werden nicht ergänzt oder plausibilisiert.

**Geltung:** Domänenübergreifend zwischen Enterprise Context und Data Integration in der erlaubten Richtung `Enterprise Context → Data Integration`.

**Unveränderliche Geschäftsregel:** Ja. Fachliche Identität, Kritikalität und Herkunft dürfen weder zusammengeführt noch durch eine konsumierende Domain umgedeutet werden.

**Fachliche Begründung:** Die Klassifikation betrifft mehrere unabhängige Context Aggregates. Eine gemeinsame Regel verhindert widersprüchliche Schutzrelevanz, ohne deren Konsistenzgrenzen zu verschmelzen.

**Verantwortungsgrenze:** Die Aggregate verantworten ihre eigenen Context-Aussagen. Der Enterprise Context Classification Service koordiniert die Einordnung. Die Policy besitzt oder verändert weder Context- noch Integration-Zustand.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Observation Correlation Integrity Policy

**Owner Domain:** Security Observation

**Fachlicher Zweck:** Sicherstellen, dass eine Korrelation vorhandene Security Observations ausschließlich gemeinsam einordnet, ohne ihre autoritativen Aussagen zu verändern oder eine neue gemeinsame Wahrheit zu erzeugen.

**Betroffene Aggregate:** Finding Aggregate; Alert Aggregate; Exposure Aggregate; Asset Context Aggregate; Threat Indicator Aggregate ausschließlich als autoritative Kontextquellen.

**Betroffene Domain Services:** Security Observation Correlation Service.

**Auslösende fachliche Bedingungen:** Mindestens zwei vorhandene Observation-Aussagen sollen gemeinsam betrachtet oder durch autoritativen Asset- beziehungsweise Threat-Indicator-Kontext eingeordnet werden.

**Erwartetes fachliches Ergebnis:** Eine fachliche Korrelationsaussage, bei der Finding, Alert und Exposure eigenständig gültig bleiben und Kontextaussagen unverändert referenziert werden. Eine Korrelation erzeugt weder Evidence noch Incident, Hunt oder Decision.

**Geltung:** Domänenübergreifend entlang `Security Observation → Enterprise Context` und `Security Observation → Threat Intelligence`.

**Unveränderliche Geschäftsregel:** Ja. Korrelation darf Observation- und Kontext-Ownership weder vermischen noch übertragen.

**Fachliche Begründung:** Die beteiligten Observations besitzen getrennte Aggregate-Grenzen. Ihre gemeinsame Bewertung benötigt eine einheitliche Integritätsregel oberhalb eines einzelnen Aggregates.

**Verantwortungsgrenze:** Die Observation Aggregates verantworten ihre eigenen Aussagen. Der Security Observation Correlation Service koordiniert die Korrelation. Die Policy klassifiziert keine Quelle als Evidence und besitzt keinen Beobachtungszustand.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Intelligence Provenance and Assessment Integrity Policy

**Owner Domain:** Threat Intelligence

**Fachlicher Zweck:** Sicherstellen, dass domänenweite Intelligence-Bewertungen die eigenständige Bedeutung ihrer Intelligence-Aussagen und deren autoritative Herkunft bewahren.

**Betroffene Aggregate:** Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate; Integration Aggregate ausschließlich als autoritative Herkunftsaussage.

**Betroffene Domain Services:** Threat Intelligence Assessment Service.

**Auslösende fachliche Bedingungen:** Aussagen mehrerer Intelligence Aggregates werden gemeinsam bewertet oder ihre Herkunft wird für die Bewertung herangezogen.

**Erwartetes fachliches Ergebnis:** Eine widerspruchsfreie Bewertung vorhandener Intelligence-Aussagen mit erhaltener Quellherkunft. Die Bewertung verändert weder die technische Lineage noch interne Security Observations.

**Geltung:** Domänenübergreifend in der erlaubten Richtung `Threat Intelligence → Data Integration`.

**Unveränderliche Geschäftsregel:** Ja. Eine Intelligence-Aussage darf ihre Bedeutung oder Herkunft nicht durch gemeinsame Bewertung verlieren.

**Fachliche Begründung:** Actor, Technique, Indicator und Campaign besitzen unabhängige fachliche Lebensläufe. Eine übergreifende Bewertung benötigt deshalb eine Regel, welche ihre Eigenständigkeit und Nachvollziehbarkeit schützt.

**Verantwortungsgrenze:** Die Intelligence Aggregates verantworten ihre Aussagen. Der Threat Intelligence Assessment Service koordiniert die Bewertung. Die Policy nimmt keine Daten auf, erzeugt keine Observation und qualifiziert keine Evidence.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Evidence Admissibility and Provenance Policy

**Owner Domain:** Decision Evidence

**Fachlicher Zweck:** Sicherstellen, dass ausschließlich vorhandene, autoritative und nachvollziehbare Aussagen als entscheidungsrelevante Evidence qualifiziert werden.

**Betroffene Aggregate:** Evidence Aggregate; Finding Aggregate; Alert Aggregate; Exposure Aggregate; Threat Indicator Aggregate; Hunt Aggregate; Governance Policy Aggregate ausschließlich als autoritative Quellen.

**Betroffene Domain Services:** Decision Evidence Qualification Service.

**Auslösende fachliche Bedingungen:** Eine vorhandene Aussage aus einer erlaubten Source Domain soll als Source Evidence oder Derived Evidence für eine Decision qualifiziert werden.

**Erwartetes fachliches Ergebnis:** Eine unveränderliche, provenance-pflichtige Evidence-Aussage, deren fachliche Relevanz und Herkunft vollständig auf vorhandene Quellen zurückführbar sind. Fehlende Fakten werden weder erzeugt noch plausibilisiert.

**Geltung:** Domänenübergreifend entlang der erlaubten Abhängigkeiten von Decision Evidence zu Security Observation, Threat Intelligence, Threat Hunting und Governance and Compliance.

**Unveränderliche Geschäftsregel:** Ja. Evidence muss immutable, provenance-pflichtig und von Decision, Explainability sowie Execution Trace getrennt bleiben.

**Fachliche Begründung:** ADR-0006 verlangt eine kanonische, überprüfbare Tatsachengrundlage. Die Zulässigkeit einer Quelle betrifft mehrere Domains und kann deshalb nicht als Invariante eines einzelnen Source Aggregates bestehen.

**Verantwortungsgrenze:** Source Aggregates besitzen ihre Originalaussagen; das Evidence Aggregate besitzt ausschließlich die qualifizierte Evidence-Aussage. Der Decision Evidence Qualification Service koordiniert die Qualifikation. Die Policy trifft keine Decision und verändert keine Quelle.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Canonical Decision Basis Policy

**Owner Domain:** Cyber Decision

**Fachlicher Zweck:** Sicherstellen, dass eine kanonische Cyber Decision ausschließlich auf zulässiger Evidence sowie vorhandenen autoritativen Business- und Governance-Aussagen beruht.

**Betroffene Aggregate:** Decision Aggregate; Evidence Aggregate; Business Service Context Aggregate; Governance Policy Aggregate ausschließlich als autoritative Eingaben.

**Betroffene Domain Services:** Cyber Decision Evaluation Service.

**Auslösende fachliche Bedingungen:** Eine Cyber Decision wird aus fachlich autorisierten Eingaben bewertet oder als `DecisionResult` abgeschlossen.

**Erwartetes fachliches Ergebnis:** Genau eine kanonische Decision-Aussage mit dem exakt verwendeten Evidence-Snapshot. Business Context und Governance werden berücksichtigt, aber weder verändert noch als parallele Decision-Quelle fortgeschrieben.

**Geltung:** Domänenübergreifend entlang `Cyber Decision → Decision Evidence`, `Cyber Decision → Enterprise Context` und `Cyber Decision → Governance and Compliance`.

**Unveränderliche Geschäftsregel:** Ja. `DecisionResult` bleibt Single Source of Truth; Evidence, Explainability und Execution Trace bleiben getrennte Verträge.

**Fachliche Begründung:** Die Decision-Bewertung koordiniert Aussagen mehrerer Owner Domains. Eine übergreifende Policy schützt die kanonische Decision-Grenze und verhindert parallele oder unbelegte Decision-Wahrheiten.

**Verantwortungsgrenze:** Das Decision Aggregate besitzt Lifecycle und Ergebnis. Der Cyber Decision Evaluation Service koordiniert die fachliche Bewertung. Die Policy sammelt keine Evidence, erzeugt keine Explainability und steuert weder Incident noch Enterprise Risk.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Risk Ownership and Treatment Authority Policy

**Owner Domain:** Enterprise Risk

**Fachlicher Zweck:** Sicherstellen, dass Bewertung, Priorisierung, Behandlung und Annahme eines Unternehmensrisikos ausschließlich innerhalb der autoritativen Risk-Ownership erfolgen.

**Betroffene Aggregate:** Enterprise Risk Aggregate; Decision Aggregate; Business Service Context Aggregate; Governance Policy Aggregate ausschließlich als autoritative Eingaben.

**Betroffene Domain Services:** Enterprise Risk Assessment Service.

**Auslösende fachliche Bedingungen:** Ein vorhandenes Enterprise Risk wird bewertet oder priorisiert und berücksichtigt dafür eine Cyber Decision, einen Business Service oder eine Governance-Vorgabe.

**Erwartetes fachliches Ergebnis:** Eine fachlich begründete Risk-Bewertung oder Priorisierung, die Risk Treatment und Risk Acceptance bei dem verantwortenden Enterprise Risk belässt und keine Eingangsaussage überschreibt.

**Geltung:** Domänenübergreifend entlang `Enterprise Risk → Cyber Decision`, `Enterprise Risk → Enterprise Context` und `Enterprise Risk → Governance and Compliance`.

**Unveränderliche Geschäftsregel:** Ja. Nur Enterprise Risk besitzt Risiko-Ownership, Treatment und Acceptance; konsumierte Decisions, Contexts und Policies bleiben unverändert.

**Fachliche Begründung:** Vergleichende Risikobewertung kann mehrere Risk-Grenzen und externe autoritative Aussagen betreffen. Die Policy verhindert dabei eine Verlagerung der langfristigen Risikosteuerung in vorgelagerte Domains.

**Verantwortungsgrenze:** Das Enterprise Risk Aggregate verantwortet seinen Lebenslauf. Der Enterprise Risk Assessment Service koordiniert Bewertung und Priorisierung. Die Policy führt kein Treatment aus, genehmigt keine Acceptance und erstellt kein Reporting.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Governance Applicability and Exception Integrity Policy

**Owner Domain:** Governance and Compliance

**Fachlicher Zweck:** Sicherstellen, dass Governance-Vorgaben, Compliance-Anforderungen, Controls und genehmigte Abweichungen nur innerhalb ihres autoritativen Geltungsbereichs bewertet werden.

**Betroffene Aggregate:** Governance Policy Aggregate; Compliance Requirement Aggregate; Organizational Unit Context Aggregate; Business Service Context Aggregate; Finding Aggregate ausschließlich als autoritative Eingaben.

**Betroffene Domain Services:** Governance Compliance Evaluation Service.

**Auslösende fachliche Bedingungen:** Die Geltung einer Governance Policy oder Compliance Requirement wird für einen Unternehmenskontext bestimmt oder ein vorhandenes Finding fließt in eine Compliance-Bewertung ein.

**Erwartetes fachliches Ergebnis:** Eine nachvollziehbare Geltungs- oder Compliance-Aussage, bei der Controls und Governance Exceptions ihrer Policy sowie Compliance Assessments ihrer Requirement zugeordnet bleiben. Eine Governance Exception wird nicht als Risk Acceptance umgedeutet.

**Geltung:** Domänenübergreifend entlang `Governance and Compliance → Enterprise Context` und `Governance and Compliance → Security Observation`.

**Unveränderliche Geschäftsregel:** Ja. Geltungsbereich und genehmigte Ausnahme dürfen die Ownership von Context, Finding oder Enterprise Risk nicht übernehmen.

**Fachliche Begründung:** Governance Policy und Compliance Requirement sind unabhängige Aggregate, deren Bewertung autoritative Aussagen anderer Domains verwenden kann. Eine gemeinsame Policy schützt Geltung, Ausnahmeintegrität und klare Ownership.

**Verantwortungsgrenze:** Die Governance Aggregates besitzen Vorgaben, Controls, Exceptions und Assessments. Der Governance Compliance Evaluation Service koordiniert Geltung und Bewertung. Die Policy trifft keine Cyber Decision und keine Risikoakzeptanz.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Contextual Authorization Policy

**Owner Domain:** Identity and Access

**Fachlicher Zweck:** Sicherstellen, dass eine fachliche Autorisierungsentscheidung ausschließlich aus gültigen Identity-and-Access-Aussagen und einem autoritativen organisatorischen Kontext hervorgeht.

**Betroffene Aggregate:** Principal Aggregate; Access Role Aggregate; Permission Aggregate; Authorization Rule Aggregate; Organizational Unit Context Aggregate ausschließlich als autoritative Kontextquelle.

**Betroffene Domain Services:** Authorization Decision Service.

**Auslösende fachliche Bedingungen:** Für einen Principal soll innerhalb eines organisatorischen Geltungsbereichs entschieden werden, ob eine fachlich kontrollierte Plattformhandlung oder Datennutzung zulässig ist.

**Erwartetes fachliches Ergebnis:** Eine eindeutige Autorisierungsentscheidung, die Principal, Rolle, Berechtigung, Regel und Organisationskontext unverändert berücksichtigt. Workspace-Darstellung und andere Fachdomains begründen keine Berechtigung.

**Geltung:** Domänenübergreifend in der erlaubten Richtung `Identity and Access → Enterprise Context`.

**Unveränderliche Geschäftsregel:** Ja. Autorisierung kontrolliert Zugriff und Handlungen, verändert aber weder organisatorische noch fachliche Ownership.

**Fachliche Begründung:** Eine Autorisierungsentscheidung betrifft vier unabhängige Identity-and-Access-Aggregate und einen autoritativen Kontext. Die Policy verhindert, dass einzelne Aggregates oder konsumierende Workspaces eine Berechtigung eigenständig plausibilisieren.

**Verantwortungsgrenze:** Die Identity-and-Access-Aggregate verantworten ihre Aussagen. Der Authorization Decision Service koordiniert die Entscheidung. Die Policy definiert weder organisatorischen Kontext noch technische Zugriffsdurchsetzung.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Intake Lineage Integrity Policy

**Owner Domain:** Data Integration

**Fachlicher Zweck:** Sicherstellen, dass jeder Import- oder Synchronisierungsvorgang einer vorhandenen Integration zugeordnet bleibt und seine vorhandene Quell-Lineage widerspruchsfrei bewahrt.

**Betroffene Aggregate:** Integration Aggregate; Synchronization Run Aggregate; Import Run Aggregate.

**Betroffene Domain Services:** Data Intake Coordination Service.

**Auslösende fachliche Bedingungen:** Ein Import Run oder Synchronization Run wird fachlich einer bestehenden Integration als Aufnahmekontext zugeordnet.

**Erwartetes fachliches Ergebnis:** Eine eindeutige, domänenintern konsistente Zuordnung mit erhaltener Source Lineage. Aufgenommene Inhalte werden nicht fachlich interpretiert und keine Target-Domain-Aussage wird erzeugt.

**Geltung:** Ausschließlich innerhalb der Owner Domain Data Integration.

**Unveränderliche Geschäftsregel:** Ja. Ein Aufnahmevorgang darf seine autoritative Integrationszuordnung und vorhandene Quellherkunft nicht rückwirkend umdeuten.

**Fachliche Begründung:** Integration, Synchronization Run und Import Run besitzen unabhängige Lebensläufe. Eine domänenweite Regel ist erforderlich, damit ihre Zuordnung nachvollziehbar bleibt, ohne eine gemeinsame Aggregate-Grenze zu erzeugen.

**Verantwortungsgrenze:** Die drei Aggregate verantworten ihre Definition beziehungsweise ihren eigenen Run-Lifecycle. Der Data Intake Coordination Service koordiniert die Zuordnung. Die Policy führt keine Datenübertragung aus und besitzt keine fachliche Interpretation aufgenommener Inhalte.

**Persistenz- und Infrastrukturverantwortung:** Keine.

## Domains ohne eigenständige Domain Policy

### Threat Hunting

**Ergebnis:** Keine eigenständige Domain Policy erforderlich.

**Begründung:** Hunt und Hunt Hypothesis liegen gemeinsam im Hunt Aggregate. Die derzeit freigegebenen Regeln zu Hypothese, Untersuchung und Hunt-Lifecycle können vollständig innerhalb dieser Konsistenzgrenze gelten. Die Nutzung von Security Observation und Threat Intelligence ist bereits durch Aggregate-Beziehungen und Domain Dependencies begrenzt; eine zusätzliche Policy würde keine nachweisbar neue aggregateübergreifende Regel schützen.

### Incident Response

**Ergebnis:** Keine eigenständige Domain Policy erforderlich.

**Begründung:** Security Incident, Response Action, Incident Communication und Incident Review liegen gemeinsam im Security Incident Aggregate. Die freigegebene Response-Verantwortung einschließlich Phasen, Maßnahmen und Abschluss ist damit durch eine Aggregate-Grenze abgedeckt. Eine zusätzliche Policy würde Aggregate-Verantwortung duplizieren.

### Platform Operations

**Ergebnis:** Keine eigenständige Domain Policy erforderlich.

**Begründung:** Die vorhandenen Platform-Operations-Aggregate besitzen getrennte betriebliche Verantwortungen. Der aktuelle Architekturstand belegt keine fachliche Regel, die unabhängig von einem einzelnen Aggregate durch einen bestehenden Domain Service koordiniert werden müsste. Technische Betriebs-, Security- oder Infrastruktur-Policies sind ausdrücklich nicht Bestandteil dieses Katalogs.

## Verantwortungs- und Überschneidungsprüfung

| Domain Policy | Begrenzte fachliche Entscheidung | Verbleibende Verantwortung |
|---|---|---|
| Authoritative Context Classification Policy | zulässige Grundlage domänenweiter Context-Klassifikation | Context-Aussagen bei den drei Context Aggregates; Koordination beim Classification Service |
| Observation Correlation Integrity Policy | Integrität einer aggregateübergreifenden Korrelation | Observation-Aussagen bei Finding, Alert und Exposure; Koordination beim Correlation Service |
| Intelligence Provenance and Assessment Integrity Policy | Eigenständigkeit und Herkunft gemeinsamer Intelligence-Bewertung | Intelligence-Aussagen bei ihren vier Aggregates; Koordination beim Assessment Service |
| Evidence Admissibility and Provenance Policy | Zulässigkeit und Herkunft entscheidungsrelevanter Evidence | Originalaussagen bei Source Aggregates; Evidence beim Evidence Aggregate; Qualifikation beim Qualification Service |
| Canonical Decision Basis Policy | zulässige Grundlage genau einer kanonischen Decision | Decision-Lifecycle beim Decision Aggregate; Bewertung beim Evaluation Service |
| Risk Ownership and Treatment Authority Policy | Autorität über Bewertung, Treatment und Acceptance | Risk-Lifecycle beim Enterprise Risk Aggregate; vergleichende Bewertung beim Assessment Service |
| Governance Applicability and Exception Integrity Policy | Geltung sowie Trennung von Exception und Risk Acceptance | Governance-Aussagen bei ihren Aggregates; Bewertung beim Compliance Evaluation Service |
| Contextual Authorization Policy | zulässige Grundlage einer Autorisierungsentscheidung | Identity-and-Access-Aussagen bei ihren Aggregates; Koordination beim Authorization Decision Service |
| Intake Lineage Integrity Policy | Integrität der Zuordnung und Herkunft eines Aufnahmevorgangs | Definition und Run-Lifecycle bei den Data-Integration-Aggregates; Zuordnung beim Intake Coordination Service |

Keine Policy besitzt Zustand, verändert Aggregate-Grenzen oder übernimmt die koordinierende Verantwortung eines Domain Service.

## Konsistenz mit bestehenden Architekturartefakten

* ADR-0001: `DecisionResult` bleibt ausschließlich das kanonische Ergebnis des Decision Aggregate.
* ADR-0002: Execution Trace bleibt ein getrenntes Application-/Audit-Artefakt und ist keine Domain Policy.
* ADR-0003 und ADR-0004: Explainability und Completeness bleiben read-only Projektionen beziehungsweise Projektionsverträge und erzeugen keine Fakten.
* ADR-0005: Workspaces und Mission Consoles bleiben Presentation-Grenzen ohne fachliche Policy-Ownership.
* ADR-0006: Evidence bleibt immutable, provenance-pflichtig und von Quelle, Decision und Explainability getrennt.
* ADR-0007: Jede Policy respektiert exklusive Domain Ownership, getrennte Aggregate-Grenzen und die erlaubte Dependency-Richtung.
* Alle betroffenen Aggregate stammen unverändert aus `AGGREGATE-BOUNDARIES.md`.
* Alle betroffenen Domain Services stammen unverändert aus `DOMAIN-SERVICES.md`.
* Alle domänenübergreifenden Geltungsbereiche entsprechen `AGGREGATE-RELATIONSHIPS.md` und `DOMAIN-DEPENDENCIES.md`.
* Ein freigegebener Domain-Events-Katalog ist nicht vorhanden; dieses Dokument definiert oder antizipiert daher keine Domain Events.

## Nicht Bestandteil

Dieses Dokument definiert keine Produktimplementierung, Klassen, Interfaces, Methoden, APIs, DTOs, Repositorys, Persistenz, Datenbanken, Infrastruktur, technische Policies, technische Security Policies, Events, Commands, Queries, Messaging, Dependency Injection oder technische Services. Es verändert keine bestehende Domain, Entity, Value Object, Aggregate, Beziehung, Dependency Rule, Domain-Service-Verantwortung oder Architekturentscheidung.

## Statische Konsistenzprüfung

* Neun Domain Policies besitzen jeweils einen eindeutigen Namen und genau eine Owner Domain.
* Drei Domains sind mit fachlicher Begründung ausdrücklich ohne eigenständige Domain Policy dokumentiert; alle zwölf kanonischen Domains sind berücksichtigt.
* Alle genannten Aggregate stammen aus `AGGREGATE-BOUNDARIES.md`.
* Alle genannten Domain Services stammen aus `DOMAIN-SERVICES.md`.
* Jede domänenübergreifende Geltung entspricht einer erlaubten Richtung in `DOMAIN-DEPENDENCIES.md` und einer belegten Beziehung in `AGGREGATE-RELATIONSHIPS.md`.
* Jede Policy ist als unveränderliche Geschäftsregel gekennzeichnet.
* Keine Policy besitzt Aggregate-, Persistenz- oder Infrastrukturverantwortung.
* Keine Policy ersetzt einen Domain Service oder führt technische Details ein.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-OWNERSHIP-AND-RESPONSIBILITIES.md`
* `.ai/architecture/CANONICAL-ENTITIES.md`
* `.ai/architecture/CANONICAL-VALUE-OBJECTS.md`
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `.ai/architecture/DOMAIN-DEPENDENCIES.md`
* `.ai/architecture/DOMAIN-SERVICES.md`
* ADR-0001 bis ADR-0007
* AIDP TASK-0038

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
