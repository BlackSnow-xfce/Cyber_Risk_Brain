# ADR-0013 – Trusted Retrieval Boundary and Bound Context Construction

## Status

ACCEPTED

## Datum

2026-08-19

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

ADR-0010 definiert LLMs und LLM-Ausgaben als untrusted. ADR-0011 verlangt
Authorization vor geschütztem Retrieval und unabhängige Context Admission.
ADR-0012 verlangt eine deterministische Bindung von Retrieved Content an seine
typed Resource Identity. TASK-0081 bis TASK-0084 liefern die dafür notwendigen
Contracts und die isolierte Admission-Policy.

Für einen späteren Live-AI-Pfad muss nun festgelegt werden, welche Boundary
Resource Identity bestätigt und `BoundAIContext 1.0` konstruiert.

## Entscheidung

PredatorAI verwendet für geschütztes AI-Retrieval eine kontrollierte Trusted
Retrieval Boundary. Ausschließlich diese serverseitige Application-Boundary
etabliert oder bestätigt die autoritative `AIResourceReference` des tatsächlich
abgerufenen Inhalts und konstruiert beziehungsweise kontrolliert die
Konstruktion von `BoundAIContext 1.0`.

Caller, Prompts, Retrieved Content und LLMs dürfen nach Retrieval keine andere
Resource Identity ersetzen, überschreiben oder unabhängig behaupten.

### Trust-Abgrenzung

Trusted bezeichnet ausschließlich die Durchsetzung der Boundary für
Authorization Scope, Resource Selection, Resource Identity und Binding
Integrity. Retrieved Content bleibt entsprechend seinem `AIContextItem 1.0`
Trust-Level untrusted, auch wenn die Boundary trusted ist.

```text
Trusted Retrieval Boundary
        ↓
SECURITY_FINDING / Retrieved Content
        ↓
BoundAIContext
        ↓
SECURITY_FINDING remains UNTRUSTED
```

### Sicherheitsinvarianten

* **SI-01:** Geschütztes AI-Retrieval benötigt vorab einen gültigen
  deterministischen Authorization Context.
* **SI-02:** Die angefragte Resource liegt vor Retrieval im autorisierten Scope.
* **SI-03:** Die Trusted Retrieval Boundary etabliert oder bestätigt die
  autoritative typed Resource Identity.
* **SI-04:** Die Identity entspricht der tatsächlich abgerufenen Resource.
* **SI-05:** Caller können Retrieved Content und alternative Identity nicht
  unabhängig zu einer autoritativen Bindung kombinieren.
* **SI-06:** Resource Identity wird nicht aus Content, Prompt oder LLM-Output
  abgeleitet.
* **SI-07:** Fehlende, ungültige oder nicht auflösbare Identity führt
  fail-closed zum Abbruch.
* **SI-08:** Authorization-Fehler oder Scope-Mismatch stoppen Retrieval, bevor
  geschützter Content für AI-Verarbeitung zurückgegeben wird.
* **SI-09:** Die Boundary konstruiert oder kontrolliert `BoundAIContext` für
  die nachgelagerte Admission.
* **SI-10:** Trust, Provenance und Classification des Contents bleiben
  unverändert.
* **SI-11:** Binding oder Retrieval verleiht keine Instruction Authority.
* **SI-12:** Erfolgreiches Retrieval bedeutet nicht automatisch Admission.
* **SI-13:** Context Admission bleibt eine unabhängige Entscheidung.
* **SI-14:** Keine Wildcards oder implizite Scope-Erweiterung.
* **SI-15:** Prompt Injection kann Identity oder autorisierten Scope nicht
  verändern.

### Verbindliche Reihenfolge und Ownership

```text
Authenticated Identity
        ↓
AIAuthorizationScope
        ↓
Authorized Resource Request
        ↓
Trusted Retrieval Boundary
        │
        ├── authorization and scope validation
        ├── exact resource retrieval
        ├── authoritative identity confirmation
        ├── AIContextItem construction
        └── BoundAIContext construction/control
        ↓
BoundAIContext
        ↓
AIContextAdmissionPolicy
        ↓
ADMIT / REJECT
        ↓
future LLM boundary
```

Authorization Scope entsteht vor Retrieval. Ein Caller darf eine typed
Resource anfragen, begründet damit aber noch nicht die autoritative Identity.
Die Retrieval Boundary bestätigt, dass die zurückgegebene Resource der
angefragten und autorisierten Resource entspricht. Erst danach entsteht die
immutable Binding. Das LLM hat in keinem dieser Schritte Autorität.

## Fail-Closed-Anforderungen

Für geschützte Daten gilt:

```text
Kein gültiges ALLOW       → kein Retrieval
Resource außerhalb Scope  → kein Retrieval
Resource nicht auflösbar  → kein geschützter AI-Kontext
Identity nicht bestätigbar → keine Binding
Binding nicht herstellbar  → kein Admission-Pfad
```

Es gibt keinen Fallback auf breitere Resources oder alternative Identities.

## Source Adapters und Integritätsgrenzen

Künftige Adapter können Incident-, Finding-, Threat-Intelligence-, Knowledge-
Store-, Runbook-, Vector- oder approved external Sources umfassen. Diese ADR
schreibt keine Storage- oder Retrieval-Technologie vor; jeder Adapter muss die
Trusted Retrieval Boundary-Invarianten erhalten.

Für trusted in-process Repositories können typed Identity-Bestätigung und
immutable Binding ausreichen. Remote-, asynchrone, verteilte oder andere
Cross-Trust-Boundaries können später stärkere Integritätsmechanismen erfordern.
Das bleibt einer zukünftigen ADR vorbehalten; kryptografische Signaturen
werden hier nicht eingeführt.

## Begründung

Die Boundary verhindert Resource Substitution und Confused-Deputy-Fehler,
ohne Content als trusted zu behandeln oder die unabhängige Admission-Policy zu
ersetzen. Sie hält Resource Selection und Binding Integrity serverseitig und
deterministisch.

## Konsequenzen

### Positiv

* Authoritative Resource Identity hat eine eindeutige Owner-Boundary.
* Retrieved Content bleibt semantisch und vertrauensseitig unverändert.
* Admission bleibt unabhängig und fail-closed.
* Bestehende AI-Security-Contracts werden wiederverwendet.

### Negativ

* Jeder spätere geschützte Retrieval-Pfad benötigt diese Boundary.
* Remote- oder asynchrone Integrität kann zusätzliche Architektur erfordern.
* Eine konkrete Retrieval-Infrastruktur ist weiterhin offen.

## Relation zu bestehenden Contracts

Wiederzuverwenden sind:

* `AIContextItem 1.0` aus TASK-0081;
* `AIAuthorizationScope 1.0` und `AIResourceReference` aus TASK-0082;
* `AIContextAdmissionPolicy` aus TASK-0083;
* `BoundAIContext 1.0` aus TASK-0084.

Keine konkurrierenden Trust-, Classification-, Authorization-, Resource- oder
Binding-Modelle werden eingeführt.

## Alternativen

* **Arbitrary Caller konstruiert autoritative Live-Binding:** abgelehnt; dies
  ermöglicht Resource Substitution und Confused Deputy.
* **Angefragte Identity wird ohne Rückgabebestätigung vertraut:** abgelehnt;
  Request Identity und tatsächliche Retrieved Resource sind getrennte Fakten.
* **Identity aus Retrieved Content ableiten:** abgelehnt; Content kann
  attacker-controlled sein.
* **LLM prüft Resource Identity:** abgelehnt; LLM-Output ist untrusted.
* **Erfolgreiches Retrieval ist automatisch Admission:** abgelehnt; Admission
  bleibt unabhängig.
* **Content wird nach erfolgreichem Retrieval trusted markiert:** abgelehnt;
  Boundary-Trust und Content-Trust sind getrennt.

## Abgrenzung

Nicht Bestandteil dieser ADR sind:

* Retrieval-Adapter, RAG, Vector Databases, Embeddings oder Search;
* Context Storage, LLM-Aufrufe oder Prompt Construction;
* API, Frontend, RBAC/ABAC, Identity Provider oder Policy Engine;
* Agents, Tools, DLP/Output Guards oder kryptografische Signaturen.

## Migration

Künftige Live-AI-Retrieval-Pfade müssen Authorization, exakte Resource-Auswahl,
Identity-Bestätigung und `BoundAIContext`-Konstruktion innerhalb einer
trusted serverseitigen Boundary ausführen. Sie dürfen keine parallele Caller-
Identity akzeptieren. Bestehende Contracts und die unabhängige Admission-Policy
bleiben unverändert.

## Qualitäts- und Sicherheitsauswirkungen

Die ADR reduziert Confused-Deputy-, Resource-Substitution- und TOCTOU-Risiken.
Sie führt keine Runtime-Infrastruktur ein und verändert keine bestehende
Produktlogik.

## Referenzen

* `.ai/decisions/ADR-0010-llm-trust-boundary-independent-security-enforcement.md`
* `.ai/decisions/ADR-0011-authorization-before-retrieval-ai-context-admission.md`
* `.ai/decisions/ADR-0012-retrieved-content-resource-binding-admission-integrity.md`
* `core/ai_authorization/scope.py`
* `core/ai_admission/policy.py`
* `core/ai_binding/bound_context.py`
* `.ai/decisions/README.md`

## Architektur-Review

Status: ACCEPTED  
Bemerkungen: Trusted Retrieval Boundary ist Owner der autoritativen Resource
Identity und BoundAIContext-Konstruktion; Retrieved Content bleibt untrusted.  
Freigabe: Architect / Product Owner, 2026-08-19
