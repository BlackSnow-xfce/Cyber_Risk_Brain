# ADR-0012 – Retrieved Content Resource Binding and Admission Integrity

## Status

ACCEPTED

## Datum

2026-08-19

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

ADR-0011 verlangt Authorization vor Retrieval und eine unabhängige Context
Admission, bevor geschützte Inhalte die LLM-Trust-Boundary überschreiten.
TASK-0082 definiert deterministische typisierte Authorization Scopes und
TASK-0083 prüft `AIContextItem`, `AIAuthorizationScope` und eine explizite
`AIResourceReference`.

Bei künftiger Retrieval-Integration dürfen Inhalt und Resource Identity nicht
unabhängig an die Admission übergeben werden. Sonst könnte Inhalt von Resource
A mit der autorisierten Identität von Resource B gepaart werden (Resource
Substitution, Confused Deputy oder TOCTOU).

## Entscheidung

Geschützter, abgerufener Inhalt wird durch die vertrauenswürdige Retrieval-
Boundary deterministisch an eine explizite typisierte Resource Identity
gebunden. Die Context Admission bewertet ausschließlich diese gebundene
Identity gegen den `AIAuthorizationScope`.

Ein nachgelagerter Caller darf die Resource Identity nicht ersetzen,
überschreiben oder unabhängig behaupten, um Admission zu erhalten.

### Sicherheitsinvarianten

* **SI-01:** Retrieved protected content trägt eine explizite typisierte
  Resource Identity.
* **SI-02:** Die Identity wird durch die vertrauenswürdige Retrieval-Boundary
  etabliert, nicht durch das LLM.
* **SI-03:** Resource Identity wird nicht aus Inhalt oder natürlicher Sprache
  abgeleitet.
* **SI-04:** Attacker-controlled Content wird nicht zur Identity geparst.
* **SI-05:** Nach Retrieval kann ein Caller keine unabhängige Identity für
  Admission substituieren.
* **SI-06:** Admission vergleicht die gebundene Identity mit dem
  `AIAuthorizationScope`.
* **SI-07:** Ein Identity-/Scope-Mismatch führt fail-closed zur Ablehnung.
* **SI-08:** Fehlende oder nicht auflösbare Identity führt bei geschütztem
  Inhalt fail-closed zur Ablehnung.
* **SI-09:** Prompt Injection und manipulierter Inhalt verändern die gebundene
  Identity nicht.
* **SI-10:** Die `AIContextItem 1.0`-Semantik für Trust, Provenance und
  Classification bleibt erhalten.
* **SI-11:** Binding oder Admission macht Retrieved Content nicht TRUSTED.
* **SI-12:** Es gibt keine Wildcards oder caller-gesteuerte Scope-Erweiterung.

### Ownership und Reihenfolge

```text
Authenticated Identity
        ↓
Authorization Scope
        ↓
Authorized Resource
        ↓
Trusted Retrieval Boundary
        ↓
Bound Retrieved Content
  ├── typed resource identity
  ├── AI context/content
  ├── provenance
  └── classification
        ↓
Context Admission
        ↓
ADMIT / REJECT
        ↓
future LLM boundary
```

Authorization Scope wird vor Retrieval etabliert. Die Retrieval-Boundary ist
Owner der Bindung zwischen Ergebnis und Resource Identity. Context Admission
prüft diese Bindung. Das LLM ist erst nach erfolgreicher Admission beteiligt
und besitzt in keiner dieser drei Entscheidungen Autorität.

Für in-process trusted Retrieval kann eine immutable typed structural binding
ausreichen. Cross-process-, remote- oder asynchrone Pfade können später eine
stärkere Integritätsmaßnahme benötigen; dies bleibt einer späteren ADR
vorbehalten. Kryptografische Signaturen werden hier nicht vorgeschrieben.

## Begründung

Die Bindung verhindert Resource Substitution und Confused-Deputy-Fehler, ohne
die isolierte, reine Policy-Semantik von TASK-0083 nachträglich zu verändern.
Sie stellt sicher, dass Admission genau die Resource prüft, aus der der Inhalt
stammt.

## Konsequenzen

### Positiv

* Resource Identity bleibt explizit, typisiert und deterministisch.
* Content kann keine Berechtigungs- oder Identity-Entscheidung beeinflussen.
* `AIContextItem`, Provenance, Classification und Trust bleiben unverändert.
* Scope-Mismatch und fehlende Bindung fail-closed.

### Negativ

* Künftige Retrieval-Boundaries benötigen eine eigene immutable Binding-
  Repräsentation.
* Remote- oder asynchrone Retrieval-Pfade benötigen möglicherweise zusätzliche
  Integritätsmechanismen.

## Alternativen

* **Caller liefert Content und Resource Identity unabhängig:** abgelehnt;
  ermöglicht Resource Substitution und Confused Deputy.
* **Resource Identity aus Retrieved Content parsen:** abgelehnt; Inhalt ist
  untrusted und attacker-controlled.
* **LLM bestimmt die Resource-Zugehörigkeit:** abgelehnt; LLM-Ausgaben sind
  untrusted und keine Authorization-Identity.
* **Nur `source_reference`-Strings vertrauen:** abgelehnt; Source Metadata und
  Authorization Resource Identity sind getrennte Sicherheitskonzepte.
* **Fallback-Identity bei fehlender Bindung:** abgelehnt; geschützter Inhalt
  muss fail-closed abgewiesen werden.

## Abgrenzung

Nicht Bestandteil dieser ADR sind:

* Retrieval, RAG, Vector Databases, Embeddings oder Context Storage;
* kryptografische Signatur-Infrastruktur;
* API, Frontend oder neue LLM-Aufrufe;
* Policy Engines, Identity Provider, Agents, Tools oder DLP/Output Guards.

## Migration

Künftige Retrieval-Integrationen müssen Content und typed Resource Identity an
der trusted Retrieval-Boundary immutable binden und diese Bindung unverändert
an Admission weitergeben. Caller dürfen keine parallelen Identity-Argumente
für denselben Inhalt liefern. Bestehende AIContext-, Authorization- und
Admission-Contracts bleiben unverändert.

## Qualitäts- und Sicherheitsauswirkungen

Die ADR reduziert Resource-Substitution, TOCTOU- und Confused-Deputy-Risiken.
Sie führt keine Runtime-Infrastruktur ein und verändert keine bestehende
Produktlogik.

## Referenzen

* `.ai/decisions/ADR-0010-llm-trust-boundary-independent-security-enforcement.md`
* `.ai/decisions/ADR-0011-authorization-before-retrieval-ai-context-admission.md`
* `core/ai_authorization/scope.py`
* `core/ai_admission/policy.py`
* `core/ai_context/context.py`
* `.ai/decisions/README.md`

## Architektur-Review

Status: ACCEPTED  
Bemerkungen: Retrieved Content muss vor Admission immutable an eine typed
Resource Identity gebunden werden.  
Freigabe: Architect / Product Owner, 2026-08-19
