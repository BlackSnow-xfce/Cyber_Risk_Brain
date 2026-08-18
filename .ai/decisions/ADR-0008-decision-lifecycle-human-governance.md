# ADR-0008 – Decision Lifecycle & Human Decision Governance

## Status

ACCEPTED

## Datum

2026-08-18

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

ADR-0001 legt `core.decision.models.DecisionResult` als einziges kanonisches fachliches Ergebnis einer abgeschlossenen Decision fest. ADR-0002 trennt den technischen Ablauf einer Reasoning-Ausführung als Execution Trace davon. ADR-0003 und ADR-0004 definieren Explainability als read-only Projektion mit expliziter Completeness. ADR-0006 schützt Decision Evidence als unveränderlichen, provenance-pflichtigen Nachweis. ADR-0007 verbietet parallele fachliche Wahrheiten und Änderungen außerhalb der jeweiligen Owner-Domain.

Der aktuelle `DecisionResult` beschreibt das fachliche Outcome einer Decision durch unter anderem `priority`, `action`, `decision`, Reasoning, Business Impact, Confidence, Recommendations und Evidence. Er beschreibt jedoch keinen Governance-Lifecycle: Es ist derzeit nicht kanonisch festgelegt, wann ein erzeugtes Ergebnis zur Prüfung vorliegt, wer es freigeben oder ablehnen darf, wie eine Freigabe an Evidence gebunden wird, wie neue Evidence eine Neubewertung auslöst oder wie historische Versionen unverändert erhalten bleiben.

Im Repository existieren mehrere Statusfamilien für andere fachliche Zwecke, beispielsweise Completeness, Finding-Explanation-Generation, Risk Readiness und Incident-Asset-Resolution. Diese Status besitzen andere Owner und Semantiken. Sie dürfen nicht als Decision-Lifecycle-Status umgedeutet werden. Ebenso sind `DecisionPriority` und `DecisionAction` fachliche Outcome-Werte und keine Governance-Zustände.

Das zukünftige Incident Command Center benötigt eine belastbare Sicht auf bestehende Decisions. Ohne getrennte Lifecycle- und Approval-Semantik könnte die UI eine generierte Recommendation fälschlich als freigegebene Entscheidung darstellen, Approval lokal erfinden, Evidence nachträglich austauschen oder Incident-Daten als zweite Decision-Wahrheit führen.

Es muss daher entschieden werden, wie der Lifecycle des bestehenden kanonischen Decision-Konzepts serverseitig, versioniert, evidenzgebunden und human-governed geführt wird, ohne `DecisionResult` zu ersetzen oder ein zweites Decision-Modell einzuführen.

## Entscheidung

PredatorAI führt für das bestehende kanonische Decision-Konzept einen getrennten **Decision Governance Lifecycle** ein. Der Lifecycle beschreibt ausschließlich Governance-Zustand, Version und autorisierte Transitionen eines referenzierten `DecisionResult`. Das fachliche Outcome verbleibt ausschließlich im `DecisionResult`.

Diese Entscheidung definiert den zukünftigen fachlichen Vertrag und erteilt keine Implementierungsfreigabe.

### 1. Trennung von Lifecycle Status und Outcome

Decision Lifecycle Status beantwortet ausschließlich:

> In welchem Governance-Zustand befindet sich eine konkrete Decision-Version?

Das fachliche Decision Outcome beantwortet ausschließlich:

> Welche fachliche Entscheidung, Priorität, Aktion, Begründung und Empfehlung enthält diese Decision-Version?

Insbesondere sind `APPROVED` und `REJECTED` keine Decision Actions oder Prioritäten. Umgekehrt sind `REMEDIATE_NOW`, `INVESTIGATE`, `CRITICAL` oder `LOW` keine Lifecycle-Zustände. Eine Lifecycle-Transition darf das fachliche Outcome einer bestehenden Decision-Version nicht mutieren.

`DecisionResult` bleibt gemäß ADR-0001 die einzige kanonische fachliche Decision-Wahrheit. Zukünftige Lifecycle-Metadaten referenzieren eine konkrete Decision-Version und bilden kein konkurrierendes Decision-Ergebnis.

### 2. Kanonische Lifecycle-Zustände

Der Decision Governance Lifecycle besitzt genau folgende Zustände:

* `DRAFT`: Eine konkrete Decision-Version wurde serverseitig erzeugt, ist aber noch nicht zur menschlichen Freigabe eingereicht.
* `PENDING_APPROVAL`: Die konkrete Version ist vollständig, evidenzgebunden und wartet auf eine autorisierte Human-Entscheidung.
* `APPROVED`: Eine autorisierte Person hat exakt diese Version mit exakt diesem Evidence Snapshot freigegeben.
* `REJECTED`: Eine autorisierte Person hat exakt diese Version abgelehnt.
* `WITHDRAWN`: Eine noch nicht abgeschlossene Version wurde vor Freigabe kontrolliert aus dem Approval-Prozess zurückgezogen.
* `SUPERSEDED`: Eine zuvor freigegebene Version wurde durch eine neuere freigegebene Version derselben logischen Decision abgelöst.

`REJECTED`, `WITHDRAWN` und `SUPERSEDED` sind terminale historische Zustände einer konkreten Version. `APPROVED` ist ein unveränderlicher freigegebener Zustand, aus dem ausschließlich die historische Ablösung nach `SUPERSEDED` zulässig ist. Keine dieser Versionen kehrt in `DRAFT` oder `PENDING_APPROVAL` zurück.

Die Zustände ergänzen bestehende Statusfamilien nicht global und ersetzen weder Completeness-, Risk-, Incident- noch Execution-Status.

### 3. Zulässige Transitionen

Der reguläre Lifecycle lautet:

```text
DRAFT ───────────────► PENDING_APPROVAL
  │                           │
  └────────► WITHDRAWN        ├────────► APPROVED
                              ├────────► REJECTED
                              └────────► WITHDRAWN

APPROVED ─────────────► SUPERSEDED
```

Alle anderen direkten Transitionen sind unzulässig. Insbesondere sind verboten:

* `DRAFT → APPROVED`;
* `DRAFT → REJECTED`;
* `REJECTED → APPROVED`;
* `WITHDRAWN → PENDING_APPROVAL`;
* `SUPERSEDED → APPROVED`;
* jede Rückkehr einer abgeschlossenen Version in einen bearbeitbaren Zustand;
* Mutation des Outcomes als vermeintliche Lifecycle-Transition.

Eine fachlich überarbeitete, erneut einzureichende oder neu evidenzierte Decision wird stets als neue Version erzeugt.

### 4. Serverseitige Ownership und Transition Records

Alle fachlichen Lifecycle-Transitionen werden ausschließlich durch die zukünftige serverseitige Decision-Owner-Boundary validiert und ausgeführt. API und Frontend dürfen Commands anfordern, aber keinen Zustand setzen oder als autoritativ persistieren.

Jede erfolgreiche Transition erzeugt einen append-only Governance-Nachweis mit mindestens:

* stabiler Referenz auf logische Decision und konkrete Decision-Version;
* vorherigem und neuem Lifecycle-Status;
* stabiler Actor Identity;
* zum Transition-Zeitpunkt wirksamer Actor Role;
* timezone-aware UTC Timestamp;
* nicht leerer Justification;
* Command-/Request-Korrelation für Audit und Idempotenz;
* bei Approval und Supersede: Referenz auf den gebundenen Evidence Snapshot beziehungsweise die ablösende Decision-Version.

Ein Actor kann ein menschlicher Principal oder bei rein technischen, ausdrücklich erlaubten Transitionen ein identifizierter System Actor sein. Anonyme Transitionen sind unzulässig. Rolle und Berechtigung werden serverseitig geprüft; ein vom Client behaupteter Rollenstring ist keine Autorisierung.

### 5. Transition Guards

Für jede Transition gelten mindestens folgende Guards:

#### `DRAFT → PENDING_APPROVAL`

* ein vollständiger, validierter `DecisionResult` liegt vor;
* eine stabile logische Decision-ID und konkrete Versions-ID sind zugeordnet;
* der exakt verwendete immutable Evidence Snapshot ist gebunden;
* erforderliche Completeness-/Readiness-Prüfungen sind serverseitig erfüllt;
* kein neuerer konkurrierender Submission-Vorgang derselben Version besteht;
* Actor, Rolle, Timestamp und Justification sind vorhanden.

#### `DRAFT → WITHDRAWN`

* die Version wurde noch nicht eingereicht oder abgeschlossen;
* der Actor ist zur Rücknahme berechtigt;
* eine nachvollziehbare Justification liegt vor.

#### `PENDING_APPROVAL → APPROVED`

* der Actor ist ein authentisierter menschlicher Principal mit der für Scope und Aktion erforderlichen Approval-Rolle;
* Separation-of-Duties-Regeln werden eingehalten;
* Decision-Version und Evidence Snapshot stimmen exakt mit der eingereichten Version überein;
* seit Submission wurde kein Bestandteil des Outcomes oder Snapshots verändert;
* keine serverseitig bekannte, noch nicht berücksichtigte widersprüchliche oder materiell neue Evidence blockiert die Freigabe;
* eine nicht leere Approval-Justification liegt vor.

#### `PENDING_APPROVAL → REJECTED`

* der Actor besitzt die erforderliche Review-Rolle;
* eine nicht leere, fachlich nachvollziehbare Rejection-Justification liegt vor;
* die abgelehnte Version und ihr Evidence Snapshot bleiben unverändert historisch erhalten.

#### `PENDING_APPROVAL → WITHDRAWN`

* Rücknahme erfolgt durch eine autorisierte serverseitige Rolle;
* eine nicht leere Justification liegt vor;
* es wurde noch keine Approval- oder Rejection-Transition committed.

#### `APPROVED → SUPERSEDED`

* eine neuere Version derselben logischen Decision ist bereits `APPROVED`;
* die neuere Version referenziert ihre eigene immutable Evidence-Basis;
* die Supersede-Beziehung ist eindeutig und azyklisch;
* alte und neue Version bleiben unverändert nachvollziehbar;
* Actor, Rolle, Timestamp und Justification der Ablösung sind dokumentiert.

Transitions werden atomar gegen den aktuellen serverseitigen Zustand geprüft. Stale, doppelte oder konkurrierende Commands dürfen keine zweite Transition erzeugen.

### 6. Human-in-the-loop und Approval

Approval und Rejection sind ausschließlich Human-in-the-loop-Transitionen. LLMs, Agents, Risk Engines, Correlation Services, Provider, Frontend-Code oder Explainability-Projektionen dürfen keine Decision-Version freigeben oder ablehnen.

Ein System Actor darf zukünftig ausschließlich technische Transitionen wie die initiale Erzeugung von `DRAFT` oder eine policy-konforme Submission anfordern, sofern ein separat freigegebener serverseitiger Contract dies erlaubt. Dieser ADR autorisiert keine automatische Approval- oder Execution-Policy.

Die konkrete Rollenmatrix bleibt eine nachgelagerte Autorisierungsentscheidung. Verbindlich ist bereits:

* die Approval-Rolle muss serverseitig und scopebezogen geprüft werden;
* der Approver darf nicht allein durch UI-Sichtbarkeit oder Workspace-Zugehörigkeit autorisiert werden;
* für hochwirksame Actions darf eine spätere Policy strengere Separation of Duties oder Mehrfachfreigabe verlangen;
* fehlende Actor-, Rollen-, Timestamp- oder Justification-Daten blockieren die Transition fail closed.

### 7. Evidence-Bindung

Jede eingereichte und freigegebene Decision-Version ist unveränderlich an exakt den Evidence Snapshot gebunden, auf dessen Grundlage ihr `DecisionResult` erzeugt wurde.

Die Bindung muss künftig mindestens stabil nachweisen können:

* Evidence-Snapshot-ID und Version;
* geordnete Evidence-IDs und jeweilige Contract-Versionen;
* Source-/Derived-Kind und Provenance;
* Integritätsreferenz beziehungsweise kanonischen Digest des Snapshots;
* relevante Completeness-Zustände;
* den Bezug zur konkreten Decision-Version.

Approval bestätigt exakt diese Kombination aus Outcome und Evidence-Basis. Evidence darf nach Submission weder ausgetauscht, ergänzt noch entfernt werden. Explainability projiziert die gebundene Basis read-only; sie erzeugt oder korrigiert keine Evidence.

### 8. Versionierung und Supersede

Eine logische Decision besitzt eine stabile Identität. Jede fachlich oder evidenzseitig unterschiedliche Ausprägung besitzt eine neue, monoton geordnete Version mit eigener stabiler Versions-ID.

Neue Version erforderlich ist mindestens bei:

* Änderung eines fachlichen Outcome-Felds;
* Änderung von Priority, Action, Reasoning, Business Impact, Confidence oder Recommendations;
* Hinzufügen, Entfernen, Ersetzen oder Korrigieren gebundener Evidence;
* geänderter Completeness, sofern sie die Decision-Basis beeinflusst;
* Neubewertung aufgrund materiell neuer oder widersprüchlicher Evidence;
* erneuter Einreichung nach `REJECTED` oder `WITHDRAWN`.

Historische Versionen werden niemals überschrieben. Eine neue Version beginnt in `DRAFT`; sie erbt weder Approval noch Rejection einer älteren Version. Erst wenn die neue Version `APPROVED` ist, darf die zuvor freigegebene Version atomar zu `SUPERSEDED` wechseln.

Es darf je logischer Decision höchstens eine nicht supersedete `APPROVED`-Version geben. Die Supersede-Kette muss eindeutig, monoton und azyklisch sein.

### 9. Neue oder widersprüchliche Evidence

Neue Evidence verändert keine bestehende Decision-Version und keine historische Approval-Aussage.

* Für `DRAFT` oder `PENDING_APPROVAL` wird bei materiell neuer oder widersprüchlicher Evidence eine neue Version erzeugt; die alte offene Version wird kontrolliert `WITHDRAWN` und darf nicht weiter freigegeben werden.
* Für `APPROVED` löst neue materielle Evidence eine serverseitige Reassessment-Anforderung aus. Die bestehende Version bleibt als historisch freigegebene Aussage zu ihrer damaligen Evidence-Basis unverändert.
* Das Ergebnis der Neubewertung ist eine neue `DRAFT`-Version.
* Erst eine freigegebene Nachfolgeversion supersediert die bisher freigegebene Version.
* Ist die neue Version nicht freigabefähig oder wird sie abgelehnt, wird die historische Version nicht rückwirkend umgeschrieben. Operative Verwendbarkeit und mögliche Execution-Sperren benötigen eine separate Policy und sind nicht Lifecycle-Outcome dieses ADRs.

Die Feststellung, ob Evidence materiell oder widersprüchlich ist, gehört zu einer zukünftigen serverseitigen Evidence-/Decision-Policy. UI und Incident Command Center dürfen dies nicht selbst ableiten.

### 10. Immutability und Historie

Ab Submission ist die konkrete Decision-Version einschließlich Outcome, Evidence-Bindung und Versionsidentität immutable. Änderungen erfolgen ausschließlich durch neue Versionen und append-only Transition Records.

Mindestens `APPROVED`, `REJECTED`, `WITHDRAWN` und `SUPERSEDED` sind dauerhaft historische Zustände. Korrekturen an Actor, Rolle, Timestamp, Justification oder Evidence erfolgen nicht durch Überschreiben; sie benötigen einen gesonderten, auditierbaren Korrekturmechanismus, der die ursprüngliche Aussage erhält. Dieser ADR definiert dessen technische Form nicht.

### 11. Trennung vom Execution Trace

Der Execution Trace gemäß ADR-0002 dokumentiert den technischen Ablauf einer Reasoning-Ausführung. Er darf referenzieren:

* erzeugte Decision-Version;
* angeforderten oder ausgeführten Transition Command;
* Ergebnisstatus der technischen Verarbeitung;
* stabile Governance-Transition-ID.

Er besitzt und verändert jedoch weder Lifecycle-Status noch Approval. Ein erfolgreicher technischer Schritt ist keine fachlich erfolgreiche Transition, solange die serverseitige Decision-Owner-Boundary sie nicht committed hat.

### 12. Trennung von Explainability

Explainability bleibt gemäß ADR-0003 und ADR-0004 eine read-only Projektion. Sie darf Outcome, Evidence-Basis, Lifecycle-Status und Transition-Historie darstellen, aber:

* keine Transition auslösen;
* keine Approval- oder Rejection-Aussage erzeugen;
* keine Justification ergänzen oder umdeuten;
* keine fehlende Evidence künstlich vervollständigen;
* keine historische Version verändern.

### 13. Frontend- und API-Grenze

Frontend und zukünftiges Incident Command Center sind Consumer serverseitiger Projektionen.

Das Frontend darf:

* Lifecycle, Outcome, Evidence-Bindung und Governance-Historie darstellen;
* einen typisierten Transition Command mit der erwarteten Version anfordern;
* serverseitige Validation-/Conflict-Ergebnisse darstellen.

Das Frontend darf nicht:

* Lifecycle-Zustände lokal als Wahrheit setzen;
* Guards, Rollen oder Separation of Duties selbst entscheiden;
* eine optimistische UI-Aktualisierung als fachlich committed behandeln;
* Approval aus Button-Klick, Workspace oder Rolle ableiten;
* Outcome, Evidence oder Historie duplizieren.

API-Verträge sind versionierte Transportprojektionen und Command-Boundaries. Sie sind keine zweite Decision-Quelle.

### 14. Incident Command Center

Das zukünftige Incident Command Center darf bestehende kanonische Findings, Canonical Assets, Threat Intelligence, Source-/Derived-Evidence, Decision-Versionen und deren Lifecycle referenzieren und projektieren.

Es darf diese Konzepte nicht duplizieren, besitzen oder verändern. Insbesondere darf ein Incident weder eine lokale Decision-Kopie noch einen eigenen Approval-Status als parallele fachliche Wahrheit führen. Incident-bezogene Commands werden an die jeweilige fachliche Owner-Boundary gerichtet.

ADR-0008 definiert kein vollständiges Incident-Domain-Modell, keinen Incident Lifecycle, keine Response Action und keine Containment-Ausführung.

## Begründung

Die Trennung von fachlichem Outcome und Governance-Lifecycle erhält `DecisionResult` als Single Source of Truth und verhindert, dass Approval-Status in Actions, Prioritäten oder UI-State einfließt. Versionierte, evidenzgebundene Decisions sind reproduzierbar und auditierbar. Append-only Transition Records erhalten die historische Aussage und ermöglichen Human Governance ohne nachträgliche Plausibilisierung.

Serverseitige Guards und Human Approval schützen besonders wirkungsvolle Security Decisions vor Client-Manipulation, stale Commands und automatischer Freigabe durch LLMs oder Engines. Die Supersede-Semantik erlaubt Weiterentwicklung bei neuer Evidence, ohne historische Entscheidungen umzuschreiben.

Die Entscheidung ergänzt ADR-0001 bis ADR-0007, ohne deren Inhalte zu verändern:

* ADR-0001 bleibt Owner des kanonischen Outcomes;
* ADR-0002 bleibt Owner des technischen Execution Trace;
* ADR-0003/0004 halten Explainability read-only;
* ADR-0006 liefert die unveränderliche Evidence-Basis;
* ADR-0007 verhindert parallele Wahrheiten im Incident Command Center.

## Konsequenzen

### Positiv

* Outcome und Governance sind eindeutig getrennt.
* Approval ist human, serverseitig autorisiert und auditierbar.
* Jede freigegebene Version ist an ihre tatsächliche Evidence-Basis gebunden.
* Neue oder widersprüchliche Evidence kann kontrolliert zu einer neuen Version führen.
* Historische Entscheidungen bleiben unverändert rekonstruierbar.
* Execution Trace, Explainability, API, Frontend und Incident Command Center bleiben abgeleitete Verbraucher.
* Stale oder konkurrierende Transition Commands können fail closed behandelt werden.

### Negativ

* Das bestehende `DecisionResult` besitzt noch keine stabile Decision-ID, Version oder explizite Snapshot-Referenz; eine spätere kompatible Erweiterung ist erforderlich.
* Rollenmatrix, Separation of Duties und Materiality Policy benötigen weitere Architekturentscheidungen.
* Append-only Historie und Snapshot-Integrität erhöhen Persistenz- und Auditaufwand.
* Die Trennung von historischer Approval und aktueller operativer Verwendbarkeit benötigt künftig eine eigene Execution-/Policy-Grenze.
* Bestehende ältere Decision-/DecisionTrace-Pfade bleiben Migration Debt.

## Alternativen

### Approval als Feld im fachlichen Outcome

Abgelehnt. Approval beschreibt Governance, nicht die fachliche Aktion oder Priorität. Eine Vermischung würde Outcome mutieren und ADR-0001 schwächen.

### Bestehendes `DecisionResult` durch ein neues Decision Aggregate ersetzen

Abgelehnt. Dies würde ein konkurrierendes Decision-Modell und eine parallele Wahrheit erzeugen. Lifecycle-Metadaten müssen die bestehende kanonische Decision-Version referenzieren.

### Freigabestatus ausschließlich im Frontend halten

Abgelehnt. Client-State ist nicht autoritativ, nicht ausreichend auditierbar und kann serverseitige Guards oder Rollen nicht ersetzen.

### Execution Trace als Lifecycle-Historie verwenden

Abgelehnt. Ein technischer Ablauf kann Commands und Ergebnisse beobachten, besitzt aber keine fachliche Transition Ownership.

### Explainability als Approval Workflow verwenden

Abgelehnt. Explainability ist read-only und darf keine fachlichen State Transitions auslösen.

### Neue Evidence in eine freigegebene Decision hineinmutieren

Abgelehnt. Dadurch gingen Evidence-Bindung, Reproduzierbarkeit und historische Approval-Bedeutung verloren.

### Incident als Owner einer lokalen Decision-Kopie

Abgelehnt. Das Incident Command Center darf Decisions referenzieren, aber nicht duplizieren oder als zweite Wahrheit besitzen.

### Vollautomatische Approval durch Risk Engine, Agent oder LLM

Abgelehnt. Diese Komponenten dürfen Outcomes oder Vorschläge erzeugen, aber keine Human-Governance-Transition ersetzen.

## Abgrenzung

Dieser ADR:

* verändert keine Produkt-, API-, Frontend- oder Persistenzdatei;
* implementiert keine Lifecycle-Klasse, Datenbank, Repository, Commands oder Endpoints;
* verändert `DecisionResult` nicht;
* führt kein konkurrierendes Decision-Modell ein;
* definiert kein Incident Aggregate oder vollständiges Incident-Domain-Modell;
* definiert keine konkrete Rollenmatrix oder Autorisierungstechnik;
* definiert keine Mehrfachfreigabe-Policy;
* implementiert keine SOAR-, Response-, Containment- oder Execution-Aktion;
* ändert keine Risk-, Correlation-, Evidence- oder Explainability-Logik;
* erteilt keine Freigabe für automatische Approval;
* verändert ADR-0001 bis ADR-0007 nicht.

## Migration

Dieser ADR implementiert keine Migration. Nach Acceptance darf die Einführung ausschließlich über separat freigegebene, kleine AIDP-Tasks erfolgen:

1. vorhandene Decision-Produzenten und Verbraucher gegen ADR-0001 und ADR-0008 inventarisieren;
2. einen kompatiblen, versionierten Governance-Contract definieren, der eine konkrete `DecisionResult`-Version referenziert;
3. stabile logische Decision-ID, Versions-ID und Evidence-Snapshot-Bindung definieren;
4. serverseitige Transition Policy und Command Boundary definieren;
5. Rollen-/Authorization-Matrix und Separation of Duties separat entscheiden;
6. append-only Persistenz- und Concurrency-Semantik separat entscheiden;
7. read-only API- und Explainability-Projektionen hinzufügen;
8. Frontend-Commands und Incident-Command-Center-Projektionen zuletzt anbinden.

Jeder Schritt benötigt eigene Contract-, Security-, Audit-, Kompatibilitäts- und Rollback-Prüfung. Es darf kein Parallelbetrieb zweier kanonischer Decision-Modelle entstehen.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität und Tests

Spätere Implementierungen benötigen mindestens Transition-Matrix-, Guard-, Idempotenz-, Concurrency-, Versionierungs-, Snapshot-Integritäts-, Authorization- und Projection-Tests. Negative Transitionen müssen fail closed bleiben. Historische Immutability und eindeutige Supersede-Ketten benötigen Contract-Tests.

### Security und Autorisierung

Actor Identity und Rolle müssen aus serverseitig vertrauenswürdiger Authentisierung/Autorisierung stammen. Justifications sind untrusted Input, müssen validiert und sicher projiziert werden. Least Privilege, Separation of Duties und Schutz vor Replay-/Stale-Commands sind verbindlich. UI-Sichtbarkeit ist keine Berechtigung.

### Auditierbarkeit

Append-only Transition Records, UTC-Timestamps, Evidence-Snapshot-Bindung, Actor-/Rollen-Snapshot und Justification ermöglichen die Rekonstruktion jeder Governance-Entscheidung. Korrekturen dürfen Originalrecords nicht vernichten.

### Datenschutz

Actor- und Justification-Daten können personenbezogene oder sensible Informationen enthalten. Datenminimierung, Zugriffskontrolle, Retention und Redaction müssen vor einer Persistenzimplementierung separat entschieden werden. Secrets dürfen weder in Justifications noch Auditdaten gelangen.

### Performance und Betrieb

Versionen, Snapshots und Transition-Historie erzeugen Speicher- und Query-Aufwand. Optimierungen dürfen Immutability, Eindeutigkeit oder Auditierbarkeit nicht umgehen. Caching und Projektionen sind keine Lifecycle-Quelle.

### Kompatibilität

Der ADR selbst erzeugt keinen Runtime- oder Breaking Change. Eine spätere Erweiterung des bestehenden Decision-Vertrags benötigt versionierte Transportprojektionen und eine schrittweise Migration bestehender Verbraucher.

## Offene Architekturfragen

Folgende Punkte sind bewusst nicht abschließend entschieden und benötigen separate Freigaben:

* konkrete Rollen und Approval-Scope-Matrix;
* Vier-Augen-/Mehrfachfreigabe für hochwirksame Actions;
* Definition materieller beziehungsweise widersprüchlicher Evidence;
* operativer Hold/Revocation-Mechanismus bei neuer Evidence ohne historische Approval-Mutation;
* technische Identität, Versionierung und Digest-Kanonisierung;
* append-only Persistenz, Optimistic Concurrency und Retention;
* Command/API-Fehlersemantik und Idempotency-Key-Vertrag;
* Verhältnis zu späterer SOAR-/Execution-Autorisierung.

## Referenzen

* AIDP TASK-0068
* `AGENTS.md`
* `ARCHITECTURE.md`
* `.ai/decisions/README.md`
* ADR-0001 – DecisionResult as Canonical Decision Contract
* ADR-0002 – Canonical Execution Trace Contract
* ADR-0003 – Canonical Explainability Projection Contract
* ADR-0004 – Explainability Completeness Contract
* ADR-0005 – Mission Console Workspace Architecture
* ADR-0006 – Decision Evidence Architecture
* ADR-0007 – Domain Integration Principles
* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-DEPENDENCIES.md`
* `core/decision/models.py`
* `core/explainability/decision_trace.py`
* `core/explainability/decision_trace_builder.py`

## Architektur-Review

Status: APPROVED  
Bemerkungen: ADR-0008 erfüllt den freigegebenen Architecture-Decision-Scope. Decision Lifecycle und fachliches Outcome bleiben getrennt; Human Governance, Evidence-Bindung, Versionierung, Supersede sowie die Grenzen zu Execution Trace, Explainability, Frontend und Incident Command Center sind konsistent zu ADR-0001 bis ADR-0007 definiert. Keine Remediation erforderlich.  
Freigabe: Architect, 2026-08-18
