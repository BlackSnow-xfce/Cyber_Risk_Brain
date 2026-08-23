# ADR-0016 – Context Resolution & Availability Semantics

## Status

ACCEPTED

## Datum

2026-08-20

## Verantwortliche

Architect: Architect
Implementation: Codex

## Kontext

PredatorAI verwendet heute mehrere korrekte, aber nicht einheitlich benannte
Zustände für Domainobjekte und Kontext: typisierte References, aufgelöste
Objekte, Completeness-/Risk-Evaluation, Capability-Zustände und UI-Status.

Die bestehende Architektur unterscheidet diese Zustände technisch bereits an
mehreren Stellen:

- eine `IncidentReference` ist ein strukturell gültiger Pointer;
- eine fehlende `IncidentReferenceResolution` ergibt fail-closed `NO_DATA`;
- `NOT_EVALUATED` bedeutet, dass keine fachliche Bewertung ausgeführt wurde;
- Model Egress ist eine separate Authorization-, Classification- und
  Minimization-Grenze;
- `Evidence` ist nicht dasselbe wie `EvidenceReference`;
- `linked`, `Ready` und `Not available` werden im Frontend derzeit teils
  lokal oder statisch verwendet.

Ohne einen verbindlichen Semantikvertrag können `EXISTS`, `REFERENCED`,
`RESOLVED`, `EVALUATED` und `AVAILABLE` fälschlich synonym dargestellt oder
für Autorisierung, AI-Egress oder fachliche Wahrheit gehalten werden.

## Problem

Die Plattform benötigt eine kleine, deterministische Semantik für:

- Referenzexistenz und Resolution;
- fachliche Evaluation und deren Ausbleiben;
- Datenverfügbarkeit für einen konkreten Use Case;
- fehlende, nicht anwendbare, nicht autorisierte, veraltete oder fehlerhafte
  Ergebnisse;
- die Übersetzung dieser Zustände in Application- und Frontend-Anzeigen.

Der Vertrag darf weder ein generisches Context-Framework noch eine neue
Security-, Trust- oder Classification-Hierarchie einführen.

## Entscheidung

PredatorAI SHALL die folgenden Begriffe als getrennte, deterministische
Semantik behandeln:

1. `EXISTS` bezeichnet die Existenz eines Datensatzes oder Domainobjekts in
   seiner autoritativen Quelle.
2. `REFERENCED` bezeichnet eine strukturell gültige typisierte Reference.
3. `RESOLVED` darf ausschließlich von einer autoritativen Application-/Domain-
   Resolution-Boundary gesetzt werden, nachdem die Reference gegen ihre
   autoritative Quelle geprüft wurde.
4. `EVALUATED` bezeichnet ausschließlich eine tatsächlich ausgeführte
   fachliche Evaluation.
5. `AVAILABLE` bedeutet, dass alle für den konkreten Use Case erforderlichen
   und autorisierten Daten erfolgreich vorliegen. `AVAILABLE` folgt niemals
   allein aus `EXISTS`, `REFERENCED` oder `RESOLVED`.

Die bestehende `IncidentReferenceResolution` ist als Read-Model-/Application-
Boundary-Muster weiterzuverwenden. Neue generische Resolver-Infrastruktur
wird durch diesen ADR nicht eingeführt. Resolver sollen möglichst typisiert
und use-case-nah bleiben.

## Canonical Terminology

### Resolution and evaluation milestones

| Begriff | Bedeutung |
|---|---|
| `EXISTS` | Autoritative Quelle enthält das Objekt oder den Datensatz. |
| `REFERENCED` | Eine typisierte Reference ist vorhanden und strukturell gültig. |
| `RESOLVED` | Eine autoritative Resolution-Boundary hat die Reference erfolgreich geprüft. |
| `EVALUATED` | Eine fachliche Bewertung wurde tatsächlich ausgeführt. |
| `AVAILABLE` | Use-Case-spezifische Voraussetzungen und Daten liegen autorisiert vollständig genug vor. |

Insbesondere gilt:

```text
REFERENCED != RESOLVED
REFERENCED != AVAILABLE
RESOLVED != EVALUATED
EVALUATED != AVAILABLE
```

### Availability outcomes

Die kleine verbindliche Menge von Ergebniszuständen lautet:

- `AVAILABLE`: erforderliche Daten liegen erfolgreich und autorisiert vor;
- `NO_DATA`: erwartete Daten oder eine erforderliche Resolution fehlen;
- `NOT_APPLICABLE`: der Use Case ist für diesen Datensatz nicht anwendbar;
- `NOT_EVALUATED`: die fachliche Prüfung wurde nicht ausgeführt;
- `UNAUTHORIZED`: die Quelle oder der Datensatz darf für diesen Use Case nicht
  verwendet werden;
- `STALE`: eine vorhandene Resolution oder Evaluation ist nicht mehr frisch
  genug für den Use Case;
- `ERROR`: die Resolution oder Evaluation konnte wegen eines technischen
  Fehlers nicht zuverlässig abgeschlossen werden;
- `NOT_IMPLEMENTED`: die erforderliche Capability existiert noch nicht.

Diese Zustände dürfen nicht stillschweigend ineinander konvertiert werden.
Insbesondere darf `NO_DATA`, `UNAUTHORIZED`, `ERROR` oder `NOT_IMPLEMENTED`
nicht zu `AVAILABLE` werden.

`Loading` ist ein temporärer Application-/Presentation-Zustand und kein
fachlicher Domainstatus.

## Resolution Semantics

Ein Resolution-Ergebnis muss mindestens eine typisierte Reference, einen
kanonischen Ergebnisstatus und eine nichtleere Source-/Provenance-Reference
tragen. Für `AVAILABLE` beziehungsweise eine erfolgreiche Resolution muss die
Resolution-Boundary die Identität und den passenden Resource-/Domain-Typ
bestätigen.

Resolution ist eine Application-/Read-Model-Verantwortung unter Kontrolle der
autoritativen Domain- oder Repository-Grenze. Frontend-Komponenten dürfen
References nicht selbst auflösen, synthetisieren oder als verfügbar markieren.

Ein fehlendes Resolution-Ergebnis führt für einen vorhandenen Cross-Domain-
Pointer zu `NO_DATA`. Eine Reference darf nicht automatisch als geladenes
Domainobjekt, fachlich geprüftes Ergebnis oder verfügbare Context-Quelle
behandelt werden.

Source Reference und Provenance müssen bis zum konsumierenden Read Model
erhalten bleiben. Dieser ADR definiert jedoch weder ein konkretes Repository
noch ein neues Persistenzformat.

## Availability Semantics

`Ready` darf ausschließlich eine explizite Capability- oder Betriebsbereitschaft
bezeichnen. Es darf nicht als Beweis für geladene Domaindaten verwendet werden.

`Available` darf nur aus einem autoritativen Backend-/Application-Ergebnis für
den konkreten Use Case entstehen.

`No data` bezeichnet fehlende erwartete Daten oder eine fehlende erforderliche
Resolution. Es bedeutet nicht automatisch, dass die Quelle technisch nicht
erreichbar ist.

`Not evaluated` bezeichnet ausschließlich eine nicht ausgeführte fachliche
Bewertung. Es ist weder positiv noch negativ.

`Unavailable` ist nur als technische oder betriebliche Presentation eines
`ERROR`, `STALE`, `UNAUTHORIZED` oder nicht erreichbaren Dienstes zulässig,
wenn die zugrunde liegende Semantik nicht offengelegt werden darf oder noch
nicht differenziert dargestellt wird. Intern muss der präzisere Status
erhalten bleiben.

`linked` bezeichnet ausschließlich eine erfolgreich geladene Relationship-
Reference und nicht die Resolution oder Vollständigkeit des referenzierten
Contexts.

## Authority Boundaries

- Domain-Contracts validieren typisierte References und ihre strukturellen
  Invarianten.
- Autoritative Repository-/Resolver-Grenzen bestätigen `EXISTS` und
  `RESOLVED`.
- Application-Services bestimmen Use-Case-spezifische `AVAILABLE`-,
  `NO_DATA`-, `NOT_APPLICABLE`- und Evaluationsergebnisse.
- Security Boundaries bestimmen weiterhin Authorization und Model-Egress.
- Frontends visualisieren gelieferte Statuswerte und dürfen keine Domain-
  Resolution oder Verfügbarkeit aus lokalen Platzhaltern ableiten.

## Fail-Closed Rules

- Fehlende Resolution → niemals `AVAILABLE`.
- Nicht bestätigte Identität oder Resource-Typ → keine erfolgreiche Resolution.
- Fehlende fachliche Evaluation → `NOT_EVALUATED`, nicht `AVAILABLE`.
- Fehlerhafte oder stale Quellen → `ERROR` beziehungsweise `STALE`, nicht
  `NO_DATA` als interne Semantik.
- `UNAUTHORIZED` bleibt intern von `NO_DATA` und `NOT_FOUND` getrennt.
- Eine externe Anti-Enumeration-HTTP-Antwort darf mehrere interne Zustände
  zusammenfassen; die interne Resolution-/Audit-Semantik bleibt getrennt.
- Application-Availability autorisiert niemals Model Egress, Disclosure,
  Trust, Tool-Aufrufe oder Actions.

## Frontend Presentation Rules

Frontend-Komponenten müssen den vom Backend gelieferten Zustand darstellen.
Statische `Not available`- oder `Ready`-Labels dürfen nicht wie autoritative
Domainfakten wirken.

Presentation darf `Loading`, `Error` und `Unauthorized` für die UX bündeln,
sofern der zugrunde liegende präzise Status im Application-/Audit-Pfad erhalten
bleibt. Ein Relationship-Count wie `1 linked` darf nur die Reference-Existenz
beschreiben.

## AI/Egress Boundary Interaction

`AVAILABLE TO APPLICATION` bedeutet nicht `AUTHORIZED FOR MODEL EGRESS`.

Jede Model-Grenze bleibt den bestehenden Verträgen unterworfen:

- ADR-0011: Authorization vor Retrieval und unabhängige Admission;
- ADR-0013: Trusted Retrieval und authoritative Binding;
- ADR-0014: Classification, Purpose und positive Egress-Allowlist;
- ADR-0015: unabhängige Output-Security und Disclosure.

Resolution oder Availability darf keine zusätzlichen Felder, keine breitere
Classification und keine neue Egress-Berechtigung erzeugen.

## Konsequenzen

### Positiv

- References, Resolution, Evaluation und Availability sind auditierbar
  unterscheidbar.
- Fehlende oder nicht evaluierte Daten bleiben fail-closed.
- Frontend-Status können später auf eine stabile Backend-Semantik abbilden.
- Bestehende AI- und Incident-Security-Grenzen bleiben unverändert.

### Negativ

- Bestehende UI-Labels und Read Models müssen künftig präziser zugeordnet
  werden.
- Eine vollständige Availability-Anzeige benötigt zusätzliche autoritative
  Resolver-Orchestrierung.
- Mehrere Statuswerte erhöhen die fachliche Dokumentations- und Testlast,
  bleiben aber auf eine kleine deterministische Menge begrenzt.

## Alternativen

### Einen einzigen `available`-Boolean verwenden

Abgelehnt: Er vermischt Existenz, Resolution, Evaluation, technische Fehler
und Use-Case-Vollständigkeit.

### References als automatisch geladene Domainobjekte behandeln

Abgelehnt: Dies verletzt `Reference is not Truth` und kann fehlende oder
unautorisierte Resolutionen verschleiern.

### Frontend lokal über Verfügbarkeit entscheiden lassen

Abgelehnt: Das erzeugt voneinander abweichende Source-of-Truth-Definitionen
und kann statische Platzhalter wie Backend-Fakten wirken lassen.

### Einen großen generischen Context-State-Framework einführen

Abgelehnt: Die bestehende Architektur benötigt kleine typisierte Resolver- und
Read-Model-Verträge, kein neues übergreifendes Framework.

### `UNAUTHORIZED`, `ERROR` und `NO_DATA` immer extern unterscheiden

Abgelehnt: Security- und Anti-Enumeration-Anforderungen können eine gemeinsame
externe Antwort erfordern. Intern bleiben die Zustände dennoch getrennt.

## Kompatibilität mit ADR-0010–0015

- ADR-0010: LLM bleibt untrusted; Availability erzeugt keinen Trust.
- ADR-0011: Resolution ersetzt weder Authorization noch Context Admission.
- ADR-0012: Binding bleibt getrennt von Resolution und Availability.
- ADR-0013: Trusted Retrieval behält die authoritative Identity-Bestätigung.
- ADR-0014: Application-Availability erweitert keine Model-Egress-Allowlist.
- ADR-0015: Output-Security und Disclosure bleiben unabhängig.

ADR-0016 ändert oder ersetzt keinen dieser akzeptierten ADRs.

## Abgrenzung / Explicit Non-Goals

Dieser ADR entscheidet ausdrücklich nicht:

- ein `SecurityObservation`-Domainmodell;
- Evidence Trust Strength oder Sensor Trust;
- Truth Promotion;
- grounded AI Context oder zusätzliche Model-Egress-Felder;
- konkrete Resolver-Implementierungen;
- UI-Redesign;
- Persistenzmigration;
- TASK-0097 oder einen Implementierungstask.

## Migration

Bestehende typisierte References, `IncidentReferenceResolution`,
`CompletenessStatus`, Risk-Input-States und AI-Security-Verträge bleiben
erhalten. Eine spätere Umsetzung soll zunächst die bestehenden Read Models und
Resolver-Grenzen präzisieren und keine parallele Context-Architektur erzeugen.

## Qualitäts- und Sicherheitsauswirkungen

Die Entscheidung erhöht die Anforderungen an Contract-Tests und Auditierbarkeit
und verhindert implizite Availability- oder Trust-Promotion. Die zusätzlichen
Statuswerte verursachen keinen eigenen Laufzeitmechanismus; Resolver und
Application-Services bleiben für ihre konkrete Quelle verantwortlich.

## Referenzen

- AIDP-Task TASK-0098
- ADR-0004 – Explainability Completeness Contract
- ADR-0009 – Security Incident Context & Domain Ownership
- ADR-0010 bis ADR-0015
- `core/incident_response/context.py`
- `core/incident_response/read_model.py`
- `application/incident_command_center.py`
- `application/risk_readiness.py`
- `frontend/src/workspaces/soc/pages/DashboardPage.tsx`

## Architektur-Review

Status: ACCEPTED
Bemerkungen: Architect Review PASS / APPROVED.
Freigabe: Architect
