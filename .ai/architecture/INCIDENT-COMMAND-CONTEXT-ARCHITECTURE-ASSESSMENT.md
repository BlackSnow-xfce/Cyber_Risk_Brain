# Incident Command Context Architecture Assessment

Status: **ASSESSMENT / REVIEW**  
Task: `TASK-0069`  
Datum: 2026-08-18  
Scope: Incident Command Center – fachliche Context-, Relationship- und Ownership-Grenzen

## 1. Executive Summary

PredatorAI besitzt bereits einen belastbaren, kanonischen **Incident Investigation Context 1.0**. `IncidentObservation`, `IncidentInvestigationContext`, `IncidentInvestigationCandidate` und `IncidentInvestigationService` verbinden eine Observation deterministisch mit einem aufgelösten kanonischen Asset, passenden Findings und vorhandener Correlation Derived Evidence. Candidate bedeutet ausdrücklich nicht Kausalität. Ergänzend kann `IncidentWebEvidenceAssociationService` kanonische Web Source Evidence einem Incident-Identifier zuordnen, ohne Interpretation oder Kausalitätsaussage.

Dieser Bestand ist die geeignete **read-only Investigation-Assembly-Basis**, aber noch kein vollständiger Incident Command Context. Es fehlen eine fachlich autoritative Incident-Response-Verantwortung für Incident-Identität und -Lifecycle, Assignment, Analyst Notes, Incident-eigene Activity sowie versionierte, typisierte Beziehungen zu mehreren Findings, Assets, Evidence- und Decision-Versionen.

Die fachliche Architecture Baseline enthält bereits konzeptionell das **Security Incident Aggregate** in der Domain Incident Response. Es soll erweitert beziehungsweise konkretisiert werden; ein konkurrierendes Aggregate oder ein neuer Finding-, Asset-, TI-, Evidence- oder Decision-Store ist nicht erforderlich.

Vor einer Implementierung ist ein neuer ADR erforderlich. Er muss die dauerhaften Regeln für Incident Lifecycle, Relationship Identity, Activity/Timeline, Human Collaboration, Versionierung und die Referenz auf ADR-0008-Decision-Versionen entscheiden. Erst danach ist ein kleiner kanonischer Contract-Slice zulässig.

## 2. Geprüfter Ist-Zustand

### 2.1 Verbindliche Architekturentscheidungen

* **ADR-0001:** `DecisionResult` ist das einzige kanonische fachliche Decision Outcome.
* **ADR-0002:** Execution Trace ist ein getrenntes Application-/Audit-Artefakt; er besitzt keine fachlichen Lifecycles.
* **ADR-0003:** Explainability ist eine read-only Projektion.
* **ADR-0004:** Completeness ist ein eigener kanonischer Statusraum und darf nicht als Incident- oder Decision-Status verwendet werden.
* **ADR-0005:** Workspaces sind Presentation Boundaries und erzeugen keine fachliche Wahrheit.
* **ADR-0006:** Decision Evidence ist unveränderlich, provenance-pflichtig und von Quellobjekten sowie Decision Outcome getrennt.
* **ADR-0007:** Domain Ownership ist exklusiv; Cross-Domain-Integration erfolgt nur über definierte Verträge und stabile Referenzen.
* **ADR-0008:** Decision Lifecycle, Decision Outcome, Execution Trace und Explainability sind getrennt. Ein Incident Command Center darf Decision-Versionen nur referenzieren und projektieren.

Die Architecture Baseline beschreibt bereits:

* ein **Security Incident Aggregate** in der Owner-Domain Incident Response;
* erlaubte gerichtete Beziehungen von Incident Response zu Security Observation, Enterprise Context, Decision Evidence und Cyber Decision;
* `Security Incident`, `Response Action`, `Incident Communication` und `Incident Review` als konzeptionelle Aggregate-Bestandteile;
* die ausdrückliche Regel, dass Incident Response Findings, Assets, Evidence und Decisions nutzt beziehungsweise referenziert, ohne deren Ownership zu übernehmen.

### 2.2 Produktiv belastbare Backend-Strukturen

| Struktur | Aktuelle Verantwortung | Eignung für Incident Command Context |
|---|---|---|
| `UniversalFinding` | kanonische Security Observation mit Finding-ID, Source, Asset-Identifier und CVE-Referenzen | als Referenz-/Read-Quelle wiederverwendbar; nicht kopieren |
| `ObservedAssetIdentifier`, `AssetContext` | beobachtete Identität, kanonische Asset-ID, Criticality und Source Reference | als Referenz-/Read-Quelle wiederverwendbar; Asset bleibt Enterprise Context |
| Threat Intelligence Contract 1.0 | NVD/CVSS, EPSS, CISA KEV, Availability, Provenance und Timestamps | read-only über kanonische Beziehungen/Evidence; keine Incident-Kopie |
| `Evidence` | kanonische Source-/Derived-Evidence mit Identity, Kind, Provenance und Input References | direkt referenzierbar; Evidence-Inhalt bleibt Evidence-owned |
| `SecurityObservationCorrelationResult` | Correlation Derived Evidence und Completeness | als Investigation Input/Referenz wiederverwendbar |
| `IncidentObservation` | minimale Incident-/Observation-Identität, Source, Timestamp und observed Asset | geeigneter Eingang, aber kein Incident-Lifecycle-Aggregat |
| `IncidentInvestigationContext` 1.0 | zustandslose read-only Assembly von Asset, Candidate Findings und Evidence References | geeignete Grundlage für Investigation-Projection; nicht als persistenter Incident missbrauchen |
| `IncidentWebEvidenceContext` | Zuordnung vorhandener Web Source Evidence anhand des Target Asset | ergänzende read-only Evidence-Association |
| `DecisionResult` | kanonisches fachliches Decision Outcome | nur über stabile Decision-/Versionsreferenz nutzen |
| ADR-0008 Decision Governance Lifecycle | Governance einer konkreten Decision-Version | ausschließlich referenzieren; nicht als Incident-Status übernehmen |
| Explainability / Execution Trace | read-only Erklärung beziehungsweise technischer Ablauf | projektieren/referenzieren; nicht als Incident Activity Store nutzen |

### 2.3 Nicht produktiv belastbare Strukturen

Die SOC-Investigations-UI enthält `Investigation`, `InvestigationRepository` und `MockInvestigationRepository`. Dieses Modell erbt von einem generischen Frontend-`Entity` und bündelt unter anderem Severity, Risk Score, Confidence, Recommendation, Explainability, Decision, Correlations, Evidence, Timeline, Notes und Assignment. Die Daten sind synthetisch und enthalten fachliche Aussagen, die nicht aus einem produktiven Incident-Backend-Vertrag stammen.

Diese UI-Strukturen sind ausschließlich Mock-/Presentation-Bestand. Sie dürfen weder kanonisiert noch rückwärts als Backend-Domainmodell übernommen werden. Insbesondere sind folgende Felder keine belastbare Source of Truth:

* lokaler Risk Score, Severity und Confidence;
* lokale Decision- oder Recommendation-Kopie;
* freie String-Repräsentationen für Timeline und Related Findings;
* synthetische Correlations und Evidence;
* lokaler Entity-/Decision-Status.

Der Incident-Response-Workspace ist strukturell registriert, zeigt aber ausdrücklich, dass keine Incident Data Source oder Execution Capability verbunden ist. Es existiert kein öffentlicher Incident-/Investigation-API-Endpunkt und keine produktive Incident-Persistenz.

## 3. Identifizierte Architektur-Lücke

Es fehlt die konkretisierte kanonische Verantwortung des bereits konzeptionell vorhandenen **Security Incident Aggregate** für einen dauerhaft identifizierbaren Incident Command Context.

Der fehlende Baustein ist nicht ein weiteres Analysemodell, sondern eine Incident-Response-eigene Koordinationsgrenze für:

* stabile Incident-Identität und Version;
* Incident-/Investigation-Lifecycle;
* Incident-Metadaten;
* aktuelle Assignment-/Owner-Verantwortung;
* analyst-authored Notes;
* Incident-eigene Activity-Historie;
* typisierte, versionierte Referenzen auf kanonische Findings, Assets, Evidence und Decisions;
* read-only Projektion des vorhandenen `IncidentInvestigationContext`.

`IncidentInvestigationContext` allein kann diese Verantwortung nicht übernehmen: Er ist bewusst frozen, zustandslos, candidate-orientiert und besitzt weder Lifecycle noch Commands, Assignment, Notes, Activity oder Persistenzsemantik. Er soll deshalb als Investigation-Read-Modell erhalten und später aus dem Incident Command Context plus kanonischen Owner-Reads projiziert werden.

## 4. Empfohlenes Zielmodell

### 4.1 Security Incident als Owner

Die bestehende Domain **Incident Response** und ihr bereits dokumentiertes **Security Incident Aggregate** sollen Owner des Incident Command Context sein. Kein neues paralleles „Investigation Aggregate“ ist erforderlich.

Der minimale zukünftige Context sollte ausschließlich folgende Incident-eigene Informationen besitzen:

1. stabile `incident_id` und Contract-/Aggregate-Version;
2. Incident Source und externe Source Reference;
3. created/observed/updated timestamps mit timezone-aware Semantik;
4. eigener Incident Lifecycle Status;
5. minimale Incident-Metadaten, zum Beispiel kontrollierter Titel und Beschreibung;
6. Assignment-Referenz auf einen Actor/Team und deren Änderungshistorie;
7. immutable beziehungsweise append-only Analyst Notes;
8. Incident Activity Records;
9. typisierte Relationship Records zu fremden kanonischen Objekten;
10. Completeness/Missing Context ausschließlich für die read-only Command-Context-Projektion.

Er besitzt ausdrücklich nicht die fachlichen Inhalte der referenzierten Domänenobjekte.

### 4.2 Read Projection für das Command Center

Das Command Center konsumiert eine serverseitige read-only Projektion:

```text
Security Incident Aggregate
  + Incident-owned Relationships / Activity / Notes / Assignment
  + canonical Finding reads
  + canonical Asset Context reads
  + canonical TI/Evidence reads
  + canonical Decision version/lifecycle reads
  + existing IncidentInvestigationContext assembly
  -> Incident Command Context Projection
  -> API DTO
  -> Incident Command Center UI
```

Die Projection darf denormalisierte Darstellungswerte enthalten, aber nur als zeitlich gekennzeichnete read-only Projektion. Sie ist niemals Owner dieser Werte und darf keine Rückschreiblogik in andere Domains enthalten.

## 5. Relationship-Modell

### 5.1 Erlaubte typisierte Referenzen

Jede Beziehung benötigt mindestens stabile Relationship-ID, Incident-ID, Target Type, kanonische Target Reference, Relationship Role, created-at, created-by/system-source und optionale Evidence References. Die Reihenfolge muss deterministisch sein.

Erlaubte Beziehungen:

| Target | Referenz | Incident-seitige Bedeutung | Verbotene Kopie |
|---|---|---|---|
| Finding | Finding-ID plus Source/Contract-Kontext | `investigation_candidate`, `in_scope` oder später separat definierte Rolle | Finding Severity, CVEs, Description, Disposition als Incident-Wahrheit |
| Canonical Asset | canonical Asset ID; observed Identifier nur als Source Context | `affected_asset_candidate` oder `in_scope` | Criticality, Business Context, Asset Identity |
| Threat Intelligence | kanonische TI-/Fact-/Source-Referenz, vorzugsweise über Evidence | `investigation_context` | CVSS, EPSS, KEV oder Providerdaten |
| Evidence | Evidence-ID und Contract-Version | `supports_investigation`, `contradicts`, `context` nach separater Policy | Evidence Payload oder Provenance |
| Decision | logische Decision-ID, konkrete Version-ID, optional Evidence-Snapshot-ID | `governs_response` beziehungsweise `related_decision` | DecisionResult, Outcome, Lifecycle oder Approval History |
| Execution/Audit Artifact | Trace-/Event-/Action-Referenz | `observed_execution` | technischer Status oder Eventpayload |

Eine Beziehung sagt nur, dass ein kanonisches Objekt im Incident-Kontext referenziert wird. Sie darf keine Kausalität, Exploitation, Priorität oder Risk-Aussage implizieren. Solche Aussagen benötigen eigene, provenance-pflichtige Evidence beziehungsweise eine zuständige Domain-Entscheidung.

### 5.2 Mehrere Findings und Assets

Ein Incident kann null bis viele Finding- und Asset-Beziehungen besitzen. Ein Finding oder Asset kann in mehreren Incidents referenziert werden. Das ist eine many-to-many Referenzbeziehung zwischen Aggregaten, keine gemeinsame Konsistenzgrenze.

Regeln:

* keine willkürliche Primary-Finding- oder Primary-Asset-Auswahl;
* Rollen müssen explizit und fachlich definiert sein;
* Deduplizierung erfolgt über Target Type, stabile Target Identity und Relationship Role;
* Hinzufügen/Entfernen einer Incident-Beziehung verändert das Zielaggregat nicht;
* die bestehende Candidate-Ermittlung über denselben kanonischen Asset-Kontext kann Vorschläge liefern, aber keine In-Scope-Beziehung automatisch als Kausalität bestätigen;
* unbekannte oder nicht auflösbare Referenzen bleiben kontrolliert missing/unavailable und erzeugen keine lokalen Ersatzobjekte.

## 6. Ownership-Grenzen

### 6.1 Incident-/Investigation Status

Incident Response besitzt einen eigenen Lifecycle für Koordination und Untersuchung. Dieser Status beantwortet beispielsweise, ob ein Incident neu, in Untersuchung oder abgeschlossen ist. Die exakte Taxonomie und Transition Matrix sind noch nicht entschieden und dürfen nicht aus dem Frontend-`EntityStatus` übernommen werden.

Ein Investigation Phase/Status darf entweder Teil dieses Incident Lifecycles oder eine klar getrennte Incident-interne Phase sein. Diese Wahl muss ein ADR treffen. Zwei überlappende Lifecycles sind zu vermeiden.

### 6.2 Decision Lifecycle und Outcome

* Decision Lifecycle bleibt ausschließlich bei der ADR-0008 Decision-Owner-Boundary.
* Decision Outcome bleibt ausschließlich in `DecisionResult`.
* Incident Response speichert nur stabile Referenzen auf logische Decision und konkrete Version.
* Approval, Rejection oder Supersede werden nicht aus Incident Status, Assignment, Activity oder UI-Aktion abgeleitet.
* Ein Incident kann einen Decision Transition Command anfordern, aber ausschließlich die Decision Boundary validiert und committed ihn.

### 6.3 Execution-/Audit Status

Execution Trace und spätere Response-Action-Ausführung besitzen eigene technische beziehungsweise operative Zustände. Ein erfolgreich ausgeführter technischer Schritt ist weder Incident Resolution noch Decision Approval. Incident Activity darf auf einen Trace oder Action Record verweisen, aber dessen Status nicht besitzen.

### 6.4 Timeline und Activity

Incident Response besitzt ausschließlich **Incident Activity Records**: beobachtbare, append-only Ereignisse über Änderungen innerhalb des Incident Aggregates, zum Beispiel Erstellung, Statusänderung, Assignment, Note hinzugefügt oder Relationship hinzugefügt/entfernt.

Die sichtbare **Command-Center Timeline** ist eine read-only, deterministisch geordnete Projektion aus:

* Incident Activity Records;
* referenzierten Source-/Derived-Evidence-Timestamps;
* referenzierten Decision-Governance-Transitionen;
* referenzierten Execution-/Response-Action-Events.

Die Projection darf externe Events nicht als Incident Activity kopieren. Jedes Timeline Item bewahrt Owner, Event-/Artifact-ID, Timestamp, Sequence/Ordering Context und Source Reference. Bei identischen Timestamps ist eine stabile, definierte Sekundärordnung erforderlich. Wall-clock timestamp allein ist keine universelle Ereignisreihenfolge.

### 6.5 Analyst Notes

Analyst Notes gehören zu Incident Response, weil sie menschlichen Investigation Context dokumentieren. Sie sind keine Finding-, Evidence-, Decision- oder Explainability-Aussage.

Minimal erforderliche Governance:

* stabile Note-ID;
* Incident-ID;
* Author/Actor Reference und Rollen-Snapshot;
* timezone-aware Timestamp;
* unveränderlicher Inhalt nach Erstellung oder explizit versionierte Korrektur;
* optionale Referenzen auf kanonische Evidence/Findings/Assets/Decisions;
* Datenklassifikation und Zugriffskontrolle.

Eine Note wird nicht automatisch zu kanonischer Evidence. Eine spätere Evidence Qualification muss separat und provenance-pflichtig erfolgen.

### 6.6 Assignment und Owner

Assignment ist Incident-Response-eigene Koordinationsinformation. Sie referenziert eine kanonische Actor-/Team-Identität; sie kopiert keine Identitäts- oder Berechtigungsdaten. Jede Änderung benötigt Actor, Timestamp, vorherige/neue Assignment-Referenz und Audit-Nachweis. Assignment erteilt nicht automatisch Decision-Approval-Rechte.

### 6.7 Incident-Metadaten

Incident-eigene Metadaten dürfen Titel, kontrollierte Beschreibung, externe Case Reference, Source und Timestamps umfassen. Vendor-/Source-Metadaten müssen als solche gekennzeichnet bleiben. Finding-, Asset-, TI-, Evidence- oder Decision-Felder dürfen nicht in generische Incident-Metadaten kopiert werden.

## 7. Verbotene Duplikationen

Der Incident Command Context darf insbesondere nicht besitzen:

* vollständige `UniversalFinding`-Kopien als Incident Records;
* lokale Canonical Asset IDs mit eigener Criticality-/Business-Context-Wahrheit;
* kopierte NVD-, CVSS-, EPSS-, CISA-KEV- oder Providerantworten;
* kopierte Evidence Payloads oder veränderte Evidence Provenance;
* lokale `DecisionResult`-Objekte, Outcomes, Recommendations oder Risk Scores;
* lokalen Decision Approval-/Rejection-/Supersede-Status;
* Execution Trace oder Response-Action-Status als Incident Lifecycle;
* Explainability als mutable Investigation State;
* UI-generierte Correlation, Risk, Priority, Kausalität oder Initial-Access-Aussage;
* synthetische Mockdaten als produktive Incident Source.

## 8. Verhältnis zum vorhandenen Incident Investigation Contract

`IncidentInvestigationContext` 1.0 soll nicht ersetzt werden. Er bleibt eine Application-Read/Assembly-Projektion für:

* observed Incident Asset;
* Asset Resolution;
* Findings desselben kanonischen Assets als Candidates;
* Correlation Derived Evidence;
* TI-/Evidence References;
* Completeness und Missing Context;
* explizit nicht kausale Candidate-Semantik.

Ein zukünftiger Incident Command Application Service kann diesen Service wiederverwenden. Das Security Incident Aggregate bestimmt den koordinierten Scope; der Investigation Service liefert evidenzbasierte Candidate Context. Ob und wie ein Candidate als explizite Incident Relationship bestätigt wird, benötigt einen serverseitigen Incident Command und eine separat entschiedene Policy.

## 9. Verhältnis zu ADR-0008

Ein Incident referenziert eine Decision mindestens durch:

* logische Decision-ID;
* konkrete Decision-Version-ID;
* optional gebundene Evidence-Snapshot-ID;
* optional stabile Lifecycle-Projection-/Transition-Referenz.

Die Incident-Projektion darf aktuellen Lifecycle und Outcome serverseitig lesen und darstellen. Sie darf weder einen lokalen Approval-Status speichern noch eine Decision-Version mutieren. Neue Incident Evidence kann eine Reassessment-Anforderung an die Decision Owner Boundary auslösen; sie verändert keine historische Decision-Version und entscheidet nicht selbst über Materiality oder Supersede.

## 10. Status- und Verantwortungsmatrix

| Status/Aussage | Owner | Incident Command Center |
|---|---|---|
| Incident Lifecycle | Incident Response / Security Incident | anzeigen; Commands an Incident Boundary |
| Investigation Candidate | bestehende Incident Investigation Application Boundary | read-only darstellen |
| Decision Lifecycle | Cyber Decision Governance gemäß ADR-0008 | read-only darstellen; Commands nur an Decision Boundary |
| Decision Outcome | `DecisionResult` | read-only darstellen |
| Evidence Completeness | jeweiliger kanonischer Contract | unverändert projizieren |
| Execution Trace Status | Application/Audit Boundary gemäß ADR-0002 | referenzieren/projizieren |
| Response Action Status | zukünftige Incident Response Action Boundary | referenzieren/projizieren |
| UI Loading/Selection | Frontend Presentation | lokal besitzen; keine fachliche Bedeutung |

## 11. Bewertung möglicher Architekturvarianten

### A. `IncidentInvestigationContext` zum vollständigen Incident Aggregate ausbauen

**Bewertung: nicht empfohlen.** Der Contract ist eine frozen read-only Assembly und bewusst ohne Lifecycle. Ein Ausbau würde Investigation Read Model, Human Collaboration und Aggregate State vermischen.

### B. Frontend-`Investigation` als Contract übernehmen

**Bewertung: abgelehnt.** Das Modell ist synthetisch, presentation-nah und dupliziert Risk, Decision, Evidence und Correlation. Es verletzt Backend Single Source of Truth.

### C. Neues paralleles Incident/Case-Modell neben dem Security Incident Aggregate

**Bewertung: abgelehnt.** Die Architecture Baseline enthält bereits das Security Incident Aggregate. Ein zweiter Owner würde gegen ADR-0007 verstoßen.

### D. Bestehendes Security Incident Aggregate konkretisieren und `IncidentInvestigationContext` als Projection wiederverwenden

**Bewertung: empfohlen.** Die Variante erhält Domain Ownership, vermeidet Duplikate, trennt mutable Coordination State von read-only Evidence Assembly und passt zu den vorhandenen Aggregate Relationships.

## 12. Risiken und offene Entscheidungen

Vor Implementierung müssen mindestens entschieden werden:

1. exakte Incident-Lifecycle-Zustände und Transition Matrix;
2. Abgrenzung eines optionalen Investigation Phase Status vom Incident Lifecycle;
3. Incident-/Relationship-/Activity-/Note-Versionierung und Optimistic Concurrency;
4. Relationship Roles und wer sie serverseitig setzen darf;
5. Policy für Candidate-Vorschlag versus bestätigte In-Scope-Beziehung;
6. Actor-/Team-Identity Contract, Rollen und Assignment Authorization;
7. Analyst-Note-Korrektur, Redaction, Retention und Klassifikation;
8. deterministische Cross-Source-Timeline-Ordnung;
9. externe Incident Source Identity, Deduplizierung und Merge-Semantik;
10. Referenzintegrität bei archivierten, gelöschten oder nicht verfügbaren Zielobjekten;
11. Decision-Reassessment-Command ohne Übernahme der ADR-0008-Materiality-Policy;
12. Persistenz-, Audit-, Zugriffskontroll- und Mandantengrenzen;
13. API-Projektionsumfang und Datenminimierung;
14. Migration beziehungsweise Entfernung der synthetischen SOC Investigation Mockdaten aus einem späteren UI-Scope.

## 13. ADR-Empfehlung

**Ein neuer ADR ist erforderlich.**

Begründung: Die Konkretisierung des Security Incident Aggregate führt einen dauerhaften fachlichen Lifecycle, Human-Collaboration-Ownership, Cross-Domain Relationship Records und eine kombinierte Activity-/Timeline-Grenze ein. Diese Regeln wirken über Domain, Application, Persistenz, API und spätere Workspaces hinweg und können nicht sicher als bloßer Implementierungsdetail-Contract entschieden werden.

Der ADR sollte entscheiden:

* Security Incident als alleiniger Incident-Owner;
* Incident Lifecycle und Guards;
* Relationship Identity und erlaubte Target Types/Roles;
* Assignment, Notes und Incident Activity;
* Timeline als read-only Cross-Owner-Projektion;
* Referenzierung von ADR-0008-Decision-Versionen;
* Versionierung, Immutability, Concurrency und Audit;
* Abgrenzung zu Investigation Context, Evidence, Execution und Response Actions.

Dieses Assessment legt keine ADR-Nummer fest und erstellt keinen Folge-Task.

## 14. Kleinster nächster Implementierungs-/Contract-Schritt

Nach Annahme eines eigenen Incident-Context-ADRs ist der kleinste sinnvolle technische Slice ein **kanonischer Security Incident Context Contract** ohne API, UI, SOAR oder Response-Ausführung.

Der Slice sollte ausschließlich enthalten:

1. Incident Identity und versionierten Lifecycle State;
2. typisierte, referenzielle Finding-/Asset-/Evidence-/Decision-Relationships;
3. minimale append-only Activity Records für Incident-eigene Änderungen;
4. Assignment- und Analyst-Note-Verträge;
5. Guards gegen Cross-Domain-Duplikation;
6. deterministische read-only Assembly mit dem bestehenden `IncidentInvestigationContext`;
7. Contract-Tests für Referenzintegrität, Lifecycle-Trennung, Ordering und fehlende Zielkontexte.

Persistenz, API und Frontend folgen erst in getrennten, freigegebenen Slices. Ein ADR- oder Contract-Slice darf die UI-Mockmodelle nicht als Source verwenden.

## 15. Abschlussbewertung

| Bereich | Status | Bewertung |
|---|---|---|
| Incident Investigation Read Context | COMPLETE | Contract 1.0 und deterministische Candidate-Ermittlung vorhanden |
| Web Source Evidence Association | COMPLETE für aktuellen Slice | read-only und nicht kausal |
| Security Incident Aggregate Konzept | PARTIAL | Architecture Baseline vorhanden, Runtime Contract fehlt |
| Incident Lifecycle | MISSING | keine kanonische Taxonomie/Transition Policy |
| Incident Relationships | MISSING | konzeptionell erlaubt, keine typisierte Runtime-Identity |
| Multiple Findings/Assets | PARTIAL | Investigation Candidates vorhanden; koordinierte Relationships fehlen |
| Assignment/Owner | MISSING | nur synthetisches Frontend-Feld |
| Analyst Notes | MISSING | nur synthetisches Frontend-Feld |
| Incident Activity | MISSING | keine kanonische append-only Boundary |
| Command-Center Timeline | MISSING | nur UI-Placeholder/String; Cross-Owner Projection nicht definiert |
| Decision Reference | PARTIAL | ADR-0008-Regel vorhanden; Incident Reference Contract fehlt |
| API/Persistenz | MISSING / NOT REQUIRED für Assessment | spätere Slices |
| UI Foundation | PARTIAL | Workspace/Layouts vorhanden, produktive Datenquelle fehlt |

Die empfohlene Zielrichtung erzeugt keine parallele Wahrheit: Incident Response besitzt ausschließlich Koordination und Incident-eigene Historie; alle fachlichen Quell- und Ergebnisobjekte bleiben bei ihren bestehenden Ownern.

