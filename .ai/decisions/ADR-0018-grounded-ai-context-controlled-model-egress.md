# ADR-0018 – Grounded AI Context & Controlled Model Egress

## Status

ACCEPTED

## Datum

2026-08-20

## Verantwortliche

Architect: Architect
Implementation: Codex

## Context

PredatorAI verfügt lokal über mehr fachlichen Kontext als der aktuelle
Finding-Explanation-Egress verwendet. Findings, Identifiers, Assets,
Threat Intelligence, Correlation/Evidence und Incident References können
aufgelöst oder referenziert sein; der produktive Model Egress ist dennoch
bewusst auf explizit erlaubte Felder minimiert.

Die bestehende Sicherheitsarchitektur verlangt, dass Authorization, Retrieval,
Binding, Admission, Classification, Minimization und Output Disclosure
getrennte Grenzen bleiben. ADR-0016 trennt Resolution und Availability; ADR-
0017 trennt Claim, Observation, Correlation, Evidence und Verification.

## Problem

Eine gehaltvollere, fallbezogene AI-Erklärung darf nicht dadurch entstehen,
dass jeder lokal bekannte Datensatz in einen Prompt serialisiert wird. Es
fehlt eine verbindliche Architektursemantik für den deterministischen Weg von
autorisiertem, provenance-behaftetem Kontext zu einer use-case-spezifischen,
positiven Model-Egress-Projektion.

## Decision

PredatorAI führt konzeptionell einen kleinen `GroundedAIContext`-Contract (oder
semantisch äquivalenten Application-Contract) ein. Er enthält ausschließlich
für den konkreten Use Case autorisierte, erfolgreich aufgelöste, resource-
gebundene, admitted und provenance-behaftete Facts.

`GroundedAIContext` ist kein Model Payload und keine Freigabe zur Disclosure.
Der verbindliche Ablauf lautet:

```text
Authorized Retrieval
  → Resolution
  → Resource Binding
  → Provenance / Trust Metadata
  → Context Admission
  → Grounded Context Assembly
  → Classification / Minimization
  → Use-Case Model Egress Projection
  → LLM
  → Structured Output Validation
  → Disclosure Policy / Output Guard
```

Default ist DENY. Jedes neue Egress-Feld benötigt eine ausdrückliche,
use-case-spezifische Policy- und Projection-Freigabe.

## Grounded AI Context Semantics

Ein Grounded Fact muss, soweit für seinen Fact Type relevant, mindestens
besitzen:

- eindeutige Source/Provenance;
- Resource Binding;
- erfolgreichen Resolution State;
- typisierten fachlichen Fact Type;
- Evaluation State, falls der Fact eine Evaluation voraussetzt;
- Observation-/Evidence-Trust-Metadaten gemäß ADR-0017;
- Classification und gegebenenfalls Freshness.

Grounded bedeutet nicht confirmed, trusted oder autorisiert zur
Modellübertragung. `Grounded Observation` ist keine bestätigte Kompromittierung;
`Grounded TI Fact` ist kein beobachteter Exploit; `Grounded Evidence` ist keine
Human Verification.

## Deterministic Context Assembly

Context Assembly liegt in PredatorAI Application-/Security-Boundaries. Ein
Use-Case-spezifischer Assembler darf nur explizit erlaubte Context-Typen
zusammensetzen. Das LLM entscheidet weder, welche Quellen geladen oder
aufgelöst werden, noch welche Daten zum Fall gehören oder welche Trust- und
Egress-Klasse sie besitzen.

Ein universeller `fetch everything`-Context ist ausgeschlossen. Optionaler
Kontext darf fehlen, wenn ein Use-Case-Contract einen reduzierten Grounded
Context ausdrücklich zulässt; das Modell darf den fehlenden Teil nicht selbst
als PredatorAI-Fakt ergänzen.

## Grounding Requirements

Nur Facts mit autoritativer Quelle, erfolgreicher Resolution, eindeutiger
Resource-Bindung und erhaltener Provenance dürfen als grounded assemblieren.
`EXISTS`, `REFERENCED`, `RESOLVED`, `EVALUATED` und `AVAILABLE` bleiben nach
ADR-0016 getrennt. Application Availability ist keine Egress-Autorisierung.

## Fact vs. Model Reasoning Boundary

Grounded Facts werden strukturiert und provenance-behaftet bereitgestellt.
Model Reasoning/Narrative darf daraus erklären, zusammenfassen,
Zusammenhänge formulieren, Unsicherheiten darstellen und Empfehlungen geben.
Es darf keine neuen PredatorAI-Fakten, Observations, Evidence oder
Confirmations erzeugen.

Bestehende typisierte Explanation-Statements bleiben maßgeblich. Aussagen
müssen weiterhin zwischen grounded fact restatement, derived reasoning,
general security reasoning, recommendation und uncertainty/missing context
unterscheidbar bleiben, ohne eine neue unnötige Taxonomie einzuführen.

## Model Egress Projection

Model Egress wird ausschließlich über einen expliziten Use-Case-Projection-
Contract erzeugt:

```text
GroundedAIContext
  → UseCaseModelEgressProjection
  → Provider
```

`serialize(GroundedAIContext)` ist verboten. Neue interne Context-Felder
bleiben standardmäßig ausgeschlossen. Die Projection prüft für jedes Feld
Classification, fachliche Notwendigkeit, minimale Granularität,
Provider-Zulässigkeit und Use-Case-Zulässigkeit.

Das Vorhandensein einer Asset-ID, IP-Adresse, TI-Information oder Evidence-
Reference entscheidet nicht, ob diese Information an OpenAI oder einen
anderen Provider übertragen werden darf. Konkrete zusätzliche Felder werden
erst in einer späteren akzeptierten Egress Policy autorisiert.

## Classification & Minimization

Classification und Minimization werden vor der Projection deterministisch
ausgewertet. Ein Feld mit fehlender, unbekannter oder unzulässiger
Classification ist nicht egress-fähig. Die kleinstmögliche fachlich notwendige
Granularität ist zu wählen; Identifiers dürfen abstrahiert oder vollständig
ausgeschlossen werden.

## TI Grounding

Threat Intelligence darf nur als Grounded Context aufgenommen werden, wenn
Finding/CVE-Binding, autoritativer Resolver, Provenance und relevante Fact
States bekannt sind. Freshness ist zu berücksichtigen, wenn sie für den
Use-Case fachlich relevant ist. Ein CVE-Identifier allein autorisiert weder
die Übertragung noch die Ableitung von PredatorAI-TI aus allgemeinem
Modellwissen.

## Observation / Evidence Grounding

Observation- und Evidence-Context folgt ADR-0017. Resource Binding,
Resolution, Provenance sowie Trust-/Independence-Metadaten dürfen nicht
verloren gehen. Target-side Traffic Observation darf daher nicht als
`successful exploitation confirmed` ausgegeben werden. Correlation bleibt
derived Evidence und keine automatische Confirmation.

## Missing Context Semantics

Nicht resolved, nicht evaluated, unauthorized, unavailable, stale oder nicht
egress-zugelassene Facts werden nicht als vorhanden an das Modell übergeben.
`NOT_EVALUATED` darf nicht durch Modellwissen ersetzt werden. Missing Context
kann als explizite Unsicherheit oder fehlender Kontext im Output erscheinen,
aber nicht als positiver Domain-Fakt.

Ein Fehler in einem optionalen Context-Bereich blockiert nur dann den gesamten
Use Case, wenn dessen Contract diesen Bereich voraussetzt. Ein reduzierter
Grounded Context muss explizit und deterministisch definiert sein.

## Prompt-Injection Boundary

Retrieved Content, Analyst Text, TI Descriptions, Observation Payloads und
Evidence Payloads sind Daten, keine Instruktionen. Grounding verleiht ihnen
keine System-, Developer-, Security- oder Tool-Instruction Authority.
Eingebettete Anweisungen dürfen keine Application-Policy, Admission,
Projection oder Aktionen steuern.

## Provider Independence

Grounded Context und Projection sind providerunabhängig. Provider Adapter
erhalten ausschließlich die explizite Projection. Ein Provider- oder
Modellwechsel schaltet keine weiteren Felder frei. Provider-/Model-Governance
bleibt eine separate Policy.

## Output Boundary

Grounded Input erzeugt kein vertrauenswürdiges Model Output. ADR-0015 bleibt
vollständig verbindlich:

```text
Structured Output Validation
  → AIOutputDisclosurePolicy
  → FindingExplanationOutputSecurityGuard
  → Protected Disclosure
```

Model Output bleibt model-derived und untrusted; Grounding umgeht weder
Disclosure Policy noch Output Guard.

## Auditability

Zukünftige Implementierungen müssen deterministisch nachvollziehbar machen:

- welcher Grounded Context assembliert wurde;
- welche Facts projiziert und welche ausgeschlossen wurden;
- verwendete Policy-/Projection-/Contract-Version;
- Provider/Model-Referenz;
- Source References der Reasoning-Basis.

Auditdaten dürfen keine unnötigen vollständigen oder sensitiven Prompts
kopieren. Es genügt, Entscheidungen, Referenzen und Versionen zu erhalten.

## Failure Semantics

Authorization Failure, Resolution Failure, Admission Rejection, fehlender oder
staler erforderlicher Context, unsupported Classification, Egress Denial,
Provider Failure, invalid Structured Output und Disclosure Rejection sind
fail-closed für den jeweils geschützten Pfad. Kein Fehler darf durch
untrusted Modellwissen kompensiert werden.

## Relation zu ADR-0016 und ADR-0017

ADR-0016 definiert die unabhängigen Resolution-/Availability-Zustände:

```text
EXISTS != REFERENCED != RESOLVED != EVALUATED != AVAILABLE
```

ADR-0017 definiert die Trennung von Observation, Evidence, Correlation,
Verification und Incident State. GroundedAIContext übernimmt diese Semantiken,
promotet sie aber nicht zu Trust, Confirmation oder Model-Egress-Berechtigung.

## Kompatibilität mit ADR-0010–0017

- ADR-0010: LLM bleibt untrusted;
- ADR-0011 bis ADR-0013: Authorization, Retrieval, Binding und Admission
  bleiben vorgelagerte, unabhängige Grenzen;
- ADR-0014: Classification, Minimization und positive Egress-Allowlist bleiben
  verbindlich;
- ADR-0015: Output Disclosure und Guard bleiben unabhängig;
- ADR-0016: Resolution und Availability werden nicht mit Grounding oder Trust
  synonymisiert;
- ADR-0017: Observation, Evidence und Verification bleiben getrennt.

Keine bestehende Security Boundary wird abgeschwächt.

## Konsequenzen

- Künftige AI Use Cases können reicheren Fallkontext sicher und gezielt
  verwenden.
- Der aktuelle minimierte MVP-Egress bleibt gültig und unverändert.
- Zusätzliche Fakten erfordern getrennte, reviewbare Projection-/Policy-
  Entscheidungen.
- Grounding, Egress und Output Disclosure bleiben auditierbar und unabhängig.

## Abgelehnte Alternativen

- Vollständige Grounded-Context-Serialisierung: verletzt Positive Allowlist
  Projection und Data Minimization.
- LLM entscheidet über Retrieval, Resolution oder Egress: verletzt Authority
  Boundaries.
- CVE-/Reference-basierte automatische TI- oder Exploit-Behauptung: vermischt
  Identifier, Grounding und Confirmation.
- Grounding als Trust Upgrade: widerspricht ADR-0010 und ADR-0017.
- Ein universeller `fetch everything`-Assembler: erzeugt unkontrollierte
  Daten- und Scope-Ausweitung.
- Grounded Prompt als Ersatz für Output Security: widerspricht ADR-0015.

## Explizite Non-Goals

Diese ADR entscheidet nicht über zusätzliche Egress-Felder, IP-Übertragung,
DistCC-Prompts, konkrete TI-Integration, SecurityObservation-Implementierung,
Evidence-Persistenz, Resolver-Implementierung, UI-Redesign, Providerwechsel,
automatische Aktionen oder TASK-0097.

## Architektur-Review

Status: ACCEPTED

Bemerkungen: Architect Review PASS / APPROVED.

Freigabe: Architect
