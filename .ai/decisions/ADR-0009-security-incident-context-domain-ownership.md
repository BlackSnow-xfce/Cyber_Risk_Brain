# ADR-0009 – Security Incident Context & Domain Ownership

## Status

ACCEPTED

## Datum

2026-08-18

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI besitzt bereits kanonische fachliche Owner für Security Findings, Enterprise Asset Context, Threat Intelligence, Decision Evidence und Cyber Decisions. ADR-0001 bis ADR-0008 schützen diese Wahrheiten, ihre Projektionen und ihre Governance. Insbesondere bleibt `DecisionResult` das kanonische fachliche Decision Outcome, Decision Evidence provenance-pflichtig, Explainability read-only und Decision Lifecycle vollständig unter der serverseitigen Governance aus ADR-0008.

Die Architecture Baseline beschreibt bereits ein **Security Incident Aggregate** in der Domain Incident Response. Die freigegebenen Aggregate Relationships erlauben Incident Response, Findings zu nutzen, Canonical Assets zu referenzieren, Evidence zu nutzen und kanonische Decisions als Handlungsgrundlage zu referenzieren. Diese Beziehungen übertragen keine Ownership.

Der aktuelle Produktcode enthält mit `IncidentObservation`, `IncidentInvestigationContext`, `IncidentInvestigationCandidate` und `IncidentInvestigationService` einen kanonischen read-only Investigation Contract 1.0. Er löst observed Asset Identifier auf, stellt Findings desselben kanonischen Assets als nicht kausale Investigation Candidates dar und erhält Correlation-/TI-/Evidence-Referenzen sowie Completeness. `IncidentWebEvidenceAssociationService` ordnet vorhandene Web Source Evidence ebenfalls ohne Kausalitätsaussage zu.

Diese Application-Boundaries besitzen absichtlich keinen Incident Lifecycle, keine Assignment-, Participants-, Notes- oder Activity-Verantwortung und keine Persistenz. Im Frontend existiert daneben eine synthetische Investigations-Darstellung mit lokalen Risk-, Decision-, Evidence- und Correlation-Daten. Sie ist Mock-/Presentation-Bestand und keine fachliche Source of Truth.

TASK-0069 hat deshalb folgende Lücke bestätigt: Für das zukünftige Incident Command Center muss das bereits konzeptionell vorhandene Security Incident Aggregate als alleinige Incident-Response-Owner-Boundary konkretisiert werden. Ohne verbindliche Entscheidung könnten ein UI-Modell, eine read-only Assembly oder ein neuer Case Store Findings, Assets, TI, Evidence oder Decisions duplizieren und damit parallele fachliche Wahrheiten erzeugen.

## Entscheidung

PredatorAI verwendet das bestehende **Security Incident Aggregate** als einzige fachliche Owner-Boundary für einen Security Incident und dessen Incident-Response-Koordination.

Das Aggregate besitzt ausschließlich Incident-native Identität, Lifecycle, menschliche Koordination und Incident Activity. Es referenziert fachliche Objekte anderer Domains über typisierte stabile Referenzen. Es besitzt oder verändert deren Inhalte und Lifecycles nicht.

### 1. Incident-native Ownership

Das Security Incident Aggregate darf folgende Informationen fachlich besitzen:

* stabile Incident Identity;
* Aggregate-/Contract-Version und serverseitige Concurrency-Version;
* Incident Lifecycle Status;
* Incident Source und externe Source Reference;
* Incident-native Created-, Updated- und relevante Observation-Timestamps;
* minimale Incident-Metadaten wie kontrollierter Titel und Beschreibung;
* aktuelle Assignment-/Owner-Referenz und deren Änderungshistorie;
* Participant-Referenzen mit Incident-spezifischer Rolle;
* Analyst Notes;
* Incident-native Activity Records;
* typisierte Relationship Records auf fremde kanonische Objekte.

Actor-, User- oder Team-Identitäten bleiben Eigentum ihrer jeweiligen Identity-/Access-Boundary. Incident Response besitzt nur stabile Referenzen und den für einen Incident erforderlichen Rollen-/Assignment-Snapshot.

Incident-Metadaten dürfen keine beliebigen Kopien fremder Domainfelder aufnehmen. Erweiterbare Metadata Bags dürfen nicht als Umgehung der Ownership-Grenzen verwendet werden.

### 2. Incident Lifecycle

Der Incident Lifecycle beschreibt ausschließlich den Koordinationszustand des Security Incident. Er ist weder Decision Lifecycle, Response-Action-Ausführungsstatus, Evidence Completeness noch fachliches Incident Outcome.

Der minimale kanonische Lifecycle besitzt folgende Zustände:

* `OPEN`: Der Incident ist serverseitig erfasst und für Triage beziehungsweise Investigation offen.
* `INVESTIGATING`: Der Incident wird aktiv untersucht und koordiniert.
* `RESOLVED`: Die Incident-Response-Owner-Boundary hat eine begründete fachliche Resolution erfasst; Abschlussprüfung oder erneute Untersuchung bleibt möglich.
* `CLOSED`: Der Incident ist administrativ/fachlich abgeschlossen und nur noch historisch beziehungsweise read-only veränderbar, ausgenommen ein auditierter Reopen-Command.

Zulässige reguläre Transitionen:

```text
OPEN → INVESTIGATING
OPEN → CLOSED
INVESTIGATING → RESOLVED
RESOLVED → INVESTIGATING
RESOLVED → CLOSED
CLOSED → INVESTIGATING
```

`OPEN → CLOSED` ist ausschließlich für kontrollierte Duplicate-, Invalid- oder Non-Incident-Closure mit nicht leerer Justification zulässig. `RESOLVED → INVESTIGATING` und `CLOSED → INVESTIGATING` sind auditierte Reopen-Transitionen aufgrund neuer beziehungsweise neu bewerteter Incident Context Information.

Jede Transition wird ausschließlich serverseitig validiert und benötigt mindestens Incident-ID, erwartete Concurrency-Version, Actor Reference, Rollen-Snapshot, timezone-aware Timestamp, Transition Reason/Justification und idempotente Command-Korrelation. Stale oder nicht autorisierte Commands werden fail closed behandelt.

Eine spätere Response Phase, zum Beispiel Containment, Eradication oder Recovery, ist kein Incident Lifecycle Status. Falls sie benötigt wird, ist sie als getrennte Incident-Response- oder Response-Action-Projektion zu modellieren. Ebenso ist ein fachliches Incident Outcome nicht durch den Lifecycle impliziert und benötigt bei Bedarf einen eigenen Contract.

### 3. Assignment, Participants und Analyst Notes

Assignment und Participants sind Incident-native Koordinationsdaten:

* Assignment referenziert einen verantwortlichen Actor oder ein Team und besitzt eine append-only Änderungshistorie.
* Participants referenzieren Actors/Teams zusammen mit einer Incident-spezifischen Beteiligungsrolle.
* Assignment oder Participation erteilt keine Decision-Approval-, SOAR- oder Response-Execution-Berechtigung. Autorisierung wird an der jeweiligen serverseitigen Owner-Boundary geprüft.
* Änderungen benötigen Actor, Timestamp, Reason und erwartete Incident-Version.

Analyst Notes gehören zur Incident-Response-Domain. Jede Note besitzt mindestens stabile Note-ID, Incident-ID, Author Reference, Rollen-Snapshot, timezone-aware Timestamp, Inhalt und optionale Referenzen auf kanonische Objekte.

Notes sind nach Erstellung immutable oder werden ausschließlich durch explizit versionierte, auditierbare Korrekturen beziehungsweise Redactions ergänzt. Eine Analyst Note ist nicht automatisch Decision Evidence, Finding, Correlation oder Decision. Eine spätere Evidence Qualification benötigt eine getrennte, provenance-pflichtige Boundary.

### 4. Typisiertes Referenzmodell

Das Security Incident Aggregate darf ausschließlich stabile, typisierte Referenzen auf fremde fachliche Objekte halten.

Jede Relationship besitzt mindestens:

* stabile Relationship-ID;
* Incident-ID;
* Target Type;
* kanonische Target Identity;
* Relationship Role;
* created-at und created-by/system-source;
* optionale Evidence References, die die Begründung der Beziehung nachvollziehbar machen;
* Incident-/Relationship-Version für Concurrency und Historie.

Zulässige Targets:

#### Finding Reference

Referenziert Finding-ID und Source Namespace beziehungsweise den bestehenden kanonischen Finding Identity Context. Die Relationship enthält keine Kopie von Finding Title, Description, Severity, CVEs, Disposition oder Finding Lifecycle.

#### Canonical Asset Reference

Referenziert ausschließlich die Canonical Asset ID. Ein observed Identifier darf als provenance-pflichtiger Observation Context referenziert werden, ersetzt jedoch keine kanonische Asset Identity. Incident Response kopiert weder Asset Criticality noch Business Context oder Asset Classification.

#### Threat Intelligence Reference

Referenziert einen kanonischen TI-Fact, Intelligence-Record oder eine bestehende TI Source Reference einschließlich erforderlicher Contract-/Source-Version. Bevorzugt erfolgt die fachliche Nutzung über kanonische Evidence References. NVD-, CVSS-, EPSS-, CISA-KEV- oder Providerdaten werden nicht in das Incident Aggregate kopiert.

#### Evidence Reference

Referenziert Evidence-ID und Contract-Version, bei gebundenen Snapshots zusätzlich die Snapshot-Identität. Evidence Payload, Kind, Provenance und Completeness bleiben bei der Evidence-Owner-Boundary.

#### Decision Reference

Referenziert mindestens logische Decision-ID und konkrete Decision-Version-ID. Soweit für Reproduzierbarkeit erforderlich, darf zusätzlich die gebundene Evidence-Snapshot-ID und eine stabile Governance-Transition-Referenz geführt werden. `DecisionResult`, Outcome, Recommendations, Approval Status und Transition History werden nicht im Incident Aggregate kopiert.

#### Execution-/Audit Reference

Referenziert stabile Trace-, Event- oder Action-Identitäten. Technischer Status und Eventpayload bleiben bei der jeweiligen Execution-/Audit-/Response-Action-Boundary.

Referenzen müssen nicht aufgelöste, archivierte oder aktuell nicht verfügbare Targets kontrolliert darstellen können. Ein fehlender Owner-Read erzeugt kein lokales Ersatzobjekt und keine erfundene Aussage.

### 5. Relationship-Semantik

Zwischen Incidents, Findings und Assets besteht eine many-to-many Cross-Aggregate-Beziehung:

* ein Incident kann null bis viele Findings und Assets referenzieren;
* ein Finding oder Asset kann von null bis vielen Incidents referenziert werden;
* jede Relationship besitzt eine explizite Rolle;
* Relationship Identity und Reihenfolge sind deterministisch;
* Deduplizierung erfolgt mindestens über Incident-ID, Target Type, Target Identity und Relationship Role;
* Hinzufügen, Entfernen oder Historisieren einer Relationship verändert das Target Aggregate nicht.

Aus einer Relationship entsteht insbesondere keine automatische:

* Primary-Finding- oder Primary-Asset-Auswahl;
* Kausalitäts- oder Initial-Access-Aussage;
* Exploitation-Bestätigung;
* Priorisierung oder Risk-Klassifikation;
* Asset-Criticality-Ableitung;
* Finding-Severity-Ableitung;
* Decision oder Recommendation.

Eine Relationship-Rolle wie `investigation_candidate` oder `in_scope` beschreibt ausschließlich ihren explizit definierten Incident-Kontext. Candidate ist nicht gleich confirmed cause. Neue Rollen und ihre Transitionen benötigen eine serverseitige Incident-Policy und dürfen nicht ad hoc durch UI oder freie Strings erzeugt werden.

### 6. `IncidentInvestigationContext` bleibt read-only

`IncidentInvestigationContext` 1.0 bleibt die kanonische read-only Application Assembly für:

* observed Incident Asset und Asset Resolution;
* Findings desselben kanonischen Assets als Investigation Candidates;
* vorhandene Correlation Derived Evidence;
* TI-/Evidence References;
* Completeness und Missing Context;
* ausdrücklich nicht kausale Candidate-Semantik.

Er ist:

* kein Aggregate Root;
* kein zweiter Incident Store;
* kein Finding Store;
* kein Asset Store;
* kein Threat-Intelligence- oder Evidence Store;
* kein Decision Store;
* keine Decision-, Risk- oder Correlation Engine;
* keine Lifecycle- oder Command-Boundary.

Eine zukünftige Incident Command Context Projection darf diese Assembly konsumieren und mit serverseitigen Owner-Reads verbinden. Die Assembly darf weder Incident State persistieren noch Relationship Commands committen.

### 7. Incident-native Activity

Incident Response besitzt ausschließlich Activity Records über Änderungen innerhalb des Security Incident Aggregate, beispielsweise:

* Incident erstellt;
* Lifecycle Transition committed;
* Assignment oder Participants geändert;
* Analyst Note hinzugefügt, korrigiert oder redacted;
* Relationship hinzugefügt, geändert oder historisiert;
* Reassessment-/Decision-/Response-Command angefordert oder dessen externe Result Reference aufgenommen.

Incident Activity ist append-only und benötigt stabile Activity-ID, Incident-ID, monotone Incident Sequence, Activity Type, Actor/System Source, timezone-aware Timestamp, Referenzen und minimale auditable Details. Sie darf keine fremden Eventpayloads oder fachlichen Outcomes kopieren.

### 8. Cross-Domain Timeline

Die im Incident Command Center sichtbare Timeline ist eine read-only Projektion über:

* Incident-native Activity Records;
* referenzierte Source-/Derived-Evidence-Timestamps;
* referenzierte Decision-Governance-Transitions;
* referenzierte Execution-/Audit-/Response-Action-Events.

Die Timeline besitzt und mutiert keine dieser Events. Jedes Timeline Item bewahrt Source Owner, stabile Artifact-/Event-ID, Timestamp, Contract-/Version Context und Source Reference. Owner-lokale Sequenzen bleiben erhalten. Für die gemeinsame Darstellung muss eine deterministische Sekundärordnung definiert werden; Wall-clock Timestamp allein begründet keine globale Kausalität oder Reihenfolge.

Timeline-Filter, Gruppierung und Presentation State sind keine fachliche Wahrheit. Eine Timeline darf keine neue Evidence, Correlation, Decision oder Activity erzeugen.

### 9. Verhältnis zu ADR-0008

Incident Lifecycle und Decision Lifecycle sind vollständig getrennte Statusräume.

* Ein Incident kann eine konkrete Decision-Version referenzieren.
* Incident Status verändert weder Decision Outcome noch Decision Lifecycle.
* Decision Approval, Rejection, Withdrawal und Supersede verbleiben vollständig bei ADR-0008 und der zukünftigen serverseitigen Decision-Owner-Boundary.
* Assignment oder Participant-Rolle im Incident erteilt keine Approval-Berechtigung.
* Das Incident Command Center darf einen typisierten Decision Transition Command anfordern, sofern eine separat freigegebene serverseitige Boundary dies erlaubt.
* Nur die Decision Boundary autorisiert, validiert und committed eine Transition.
* Neue Incident Evidence darf eine Reassessment-Anforderung referenzieren, mutiert aber keine historische Decision-Version und bestimmt nicht selbst Evidence Materiality.

`DecisionResult` bleibt das einzige kanonische fachliche Outcome. Incident Response führt keine lokale Decision-Kopie und keinen lokalen Approval-Status.

### 10. Trennung von Execution, Audit und Response Actions

Execution Trace gemäß ADR-0002, Governance Transition Records gemäß ADR-0008 und zukünftige Response Action Records besitzen jeweils ihre eigenen Owner und Statussemantiken.

* ein erfolgreicher technischer Schritt ist keine Incident Resolution;
* ein geschlossener Incident beweist keine erfolgreiche Response Action;
* eine ausgeführte Response Action ist keine Decision Approval;
* ein Decision Approval führt nicht automatisch eine Response Action aus.

Incident Activity und Timeline dürfen diese Artefakte referenzieren, übernehmen aber weder Status noch Payload oder Lifecycle.

### 11. Incident Command Center und UI

Das zukünftige Incident Command Center ist eine Workspace-, Projection- und Interaction-Schicht gemäß ADR-0005.

Es darf:

* serverseitige kanonische Daten und read-only Assemblies darstellen;
* Incident Lifecycle, Relationships, Assignment, Notes und Activity über autorisierte serverseitige Commands anfordern;
* Commands an andere fachliche Owner-Boundaries anfordern, sofern ausdrücklich freigegeben;
* Loading, Selection und andere Presentation States lokal verwalten.

Es darf nicht:

* fachliche Incident- oder Decision-Status lokal setzen;
* Findings oder Assets kopieren beziehungsweise klassifizieren;
* TI normalisieren oder bewerten;
* Evidence erzeugen, verändern oder als vollständig behaupten;
* Decisions freigeben, ablehnen oder supersedieren;
* fremde Domain Lifecycles besitzen;
* Risk, Priority, Kausalität oder Initial Access ableiten;
* synthetische Mockdaten als produktive Wahrheit verwenden.

API-Verträge sind versionierte Transportprojektionen beziehungsweise Command Boundaries. Sie sind keine zweite fachliche Source of Truth.

## Begründung

Das Security Incident Aggregate ist bereits Teil der akzeptierten Architecture Baseline. Seine Konkretisierung bewahrt bestehende Domain Ownership und vermeidet ein zusätzliches Case-, Investigation- oder UI-Aggregate. Incident Response benötigt eigenen koordinativen Zustand, darf aber fachliche Security Observations, Asset Context, Intelligence, Evidence und Decisions nicht übernehmen.

Typisierte Referenzen ermöglichen many-to-many Investigation Context und auditierbare Beziehungen ohne Kopien. Die Trennung von Incident Activity und Cross-Domain Timeline verhindert, dass eine Darstellungsprojektion zur konkurrierenden Event- oder Evidence-Quelle wird.

Die explizite Bindung an ADR-0008 schützt Human Decision Governance: Ein Incident kann eine Decision-Version in den Arbeitskontext aufnehmen, aber weder Approval noch Outcome besitzen. `IncidentInvestigationContext` bleibt als getestete, nicht kausale Assembly wiederverwendbar und wird nicht mit mutablem Aggregate State vermischt.

## Konsequenzen

### Positiv

* Ein eindeutiger Incident-Response-Owner wird verbindlich.
* Bestehende Finding-, Asset-, TI-, Evidence- und Decision-Wahrheiten bleiben unangetastet.
* Incident Lifecycle, Decision Lifecycle, Execution Status und Completeness bleiben getrennt.
* Multiple Findings und Assets sind ohne Primary- oder Kausalitätsannahme darstellbar.
* Assignment, Participants, Notes und Activity erhalten eine auditierbare Owner-Boundary.
* Das Command Center kann künftig eine konsistente serverseitige Projektion konsumieren.
* Der vorhandene Incident Investigation Contract bleibt wiederverwendbar.

### Negativ

* Ein produktiver Incident Command Center Path benötigt mehrere getrennte Folge-Slices für Contract, Persistenz, API und UI.
* Cross-Domain-Reads können Availability-, Versionierungs- und Performance-Komplexität erzeugen.
* Append-only Activity, Notes und Relationship History erhöhen Speicher- und Query-Aufwand.
* Actor-/Team-Identity, Authorization, Retention und Redaction sind noch nicht technisch festgelegt.
* Bestehende synthetische Investigations-UI kann nicht ohne kontrollierte Migration an den späteren Backend-Vertrag angeschlossen werden.

## Alternativen

### `IncidentInvestigationContext` als Aggregate Root verwenden

Abgelehnt. Die Struktur ist eine frozen read-only Assembly ohne Lifecycle, Commands oder Human Collaboration. Eine Erweiterung würde Projection und Aggregate State vermischen.

### Frontend-`Investigation` als gemeinsames Incident-Modell verwenden

Abgelehnt. Das Modell ist synthetisch, presentation-nah und dupliziert Risk, Decision, Evidence, Correlation und Status. Es verletzt Backend Single Source of Truth.

### Neues Case- oder Investigation-Aggregate neben Security Incident einführen

Abgelehnt. Die Architecture Baseline besitzt bereits ein Security Incident Aggregate. Ein zweiter Owner würde ADR-0007 und One Canonical Model per Concept verletzen.

### Vollständige Fremdobjekte im Incident speichern

Abgelehnt. Kopierte Findings, Assets, TI, Evidence oder Decisions würden bei Änderungen driften und parallele Wahrheiten erzeugen.

### Timeline als zentralen Event Store aller Domains verwenden

Abgelehnt. Eine read-only Projection darf fremde Events nicht besitzen. Owner-lokale Event- und Audit-Verträge bleiben maßgeblich.

### Incident Status aus Decision oder Response Action ableiten

Abgelehnt. Die Lifecycles beantworten unterschiedliche fachliche Fragen. Automatische Gleichsetzung würde Governance und Auditierbarkeit verletzen.

## Abgrenzung

Dieser ADR:

* implementiert kein Domainmodell und keinen Contract;
* implementiert keine API, Persistenz oder UI;
* migriert keine Mock-Investigations-UI;
* erzeugt keine Incident-, Finding-, Asset-, TI-, Evidence- oder Decision-Daten;
* definiert keine SOAR-, Containment- oder Response-Automation;
* implementiert keine Risk-, Correlation-, Decision- oder LLM-Logik;
* verändert ADR-0001 bis ADR-0008 nicht;
* entscheidet keine konkrete Datenbank-, Event-Store- oder Messaging-Technologie;
* autorisiert keinen Folge-Task.

## Migration

Dieser ADR implementiert keine Migration.

Nach Annahme soll die Zielrichtung ausschließlich durch kleine, separat freigegebene Slices umgesetzt werden:

1. kanonischen Security Incident Context Contract mit Identity, Lifecycle, Relationships, Activity, Assignment und Notes definieren;
2. Contract-Tests für Ownership, Transitionen, Referenzidentität, Determinismus und fail-safe Missing Targets erstellen;
3. eine serverseitige Application-/Command-/Query-Boundary definieren;
4. Persistenz, Optimistic Concurrency, Append-only History, Retention und Authorization separat entscheiden und implementieren;
5. eine read-only Incident Command Context Projection unter Wiederverwendung von `IncidentInvestigationContext` bereitstellen;
6. API-Transportprojektionen hinzufügen;
7. die synthetische UI kontrolliert auf den produktiven Read Path migrieren, ohne ihre Mock-Fachmodelle zu übernehmen.

Jeder Schritt benötigt einen eigenen AIDP-Scope. Es gibt keine Big-Bang-Migration.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität

Spätere Contract- und Implementierungstests müssen mindestens Lifecycle-Transitionen, Authorization Guards, Idempotenz, Concurrency, Relationship-Deduplizierung, Many-to-many-Semantik, Missing Targets, deterministische Activity-Reihenfolge, Note-Immutability und Cross-Domain-Projektionsgrenzen prüfen.

### Security und Autorisierung

Incident Context kann sensible Security-, Asset-, Actor- und Response-Informationen referenzieren. Server Boundaries müssen Least Privilege, Mandantenisolation, Field-Level-Datenminimierung und rollenbasierte Commands erzwingen. Clientseitige Rollen oder Assignment sind keine Autorisierung.

Analyst Notes benötigen Schutz vor Injection, unkontrollierter Offenlegung und nachträglicher Manipulation. Referenzen und Provenance dürfen keine Secrets enthalten. Das Auflösen einer Referenz ist gesondert zu autorisieren; die Sichtbarkeit des Incident allein gewährt keinen Zugriff auf alle Target-Daten.

### Auditierbarkeit

Lifecycle-, Assignment-, Participant-, Note- und Relationship-Änderungen benötigen append-only Activity Records. Korrekturen dürfen ursprüngliche Aussagen nicht still überschreiben. Cross-Domain Timeline Items bewahren Source Owner und Artifact Identity.

### Datenschutz und Retention

Actor References, Rollen-Snapshots und Analyst Notes können personenbezogene oder vertrauliche Daten enthalten. Retention, Legal Hold, Export, Redaction und Zugriffsaudit müssen vor Persistenz separat entschieden werden.

### Performance

Eine read-only Command Context Projection kann mehrere Owner-Reads benötigen. Caching oder Materialized Views dürfen nur Projektionen optimieren und niemals Owner-Daten oder Lifecycles ersetzen. Stale-/Freshness-Semantik muss explizit sichtbar bleiben.

### Kompatibilität

Der ADR verursacht keine Runtime- oder API-Änderung. Der vorhandene Incident Investigation Contract 1.0 bleibt unverändert. Eine spätere UI-Migration benötigt einen versionierten Backend-Transportvertrag und darf die bestehenden Mocktypen nicht als Kompatibilitätszwang behandeln.

## Offene Architekturfragen

Vor produktiver Persistenz beziehungsweise API bleiben separat zu entscheiden:

* konkrete Actor-/Team-Identity- und Authorization-Boundary;
* genaue Incident-Metadata- und Incident-Outcome-Felder;
* kontrolliertes Vokabular und Transitionen für Relationship Roles;
* Candidate-to-In-Scope-Confirmation-Policy;
* Note-Korrektur, Redaction, Classification und Retention;
* externe Incident Source Deduplizierung und Merge Policy;
* Referenzintegrität bei archivierten oder gelöschten Targets;
* Cross-Domain-Timeline Pagination, Ordering und Freshness;
* Persistenz-, Eventing-, Concurrency- und Audit-Technologie;
* Command/API-Fehler-, Idempotenz- und Authorization-Verträge;
* Response Phase und Incident Outcome als mögliche getrennte Contracts.

Diese Fragen ändern die in diesem ADR festgelegte Ownership- und Referenzrichtung nicht.

## Referenzen

* `AGENTS.md`
* `ARCHITECTURE.md`
* TASK-0069 – Incident Command Context Architecture Assessment
* `.ai/architecture/INCIDENT-COMMAND-CONTEXT-ARCHITECTURE-ASSESSMENT.md`
* ADR-0001 – DecisionResult as Canonical Decision Contract
* ADR-0002 – Canonical Execution Trace Contract
* ADR-0003 – Canonical Explainability Projection Contract
* ADR-0004 – Explainability Completeness Contract
* ADR-0005 – Mission Console Workspace Architecture
* ADR-0006 – Decision Evidence Architecture
* ADR-0007 – Domain Integration Principles
* ADR-0008 – Decision Lifecycle & Human Decision Governance
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `application/incident_investigation.py`
* `application/incident_web_evidence.py`

## Architektur-Review

Status: APPROVED  
Bemerkungen: ADR-0009 definiert das bestehende Security Incident Aggregate konsistent als alleinige Incident-Response-Owner-Boundary. Referenzmodell, Relationship-Semantik, Incident Lifecycle, Activity-/Timeline-Grenze, `IncidentInvestigationContext` und die Trennung zu ADR-0008 sind ohne parallele fachliche Wahrheit festgelegt. Keine Remediation erforderlich.  
Freigabe: Architect, 2026-08-18
