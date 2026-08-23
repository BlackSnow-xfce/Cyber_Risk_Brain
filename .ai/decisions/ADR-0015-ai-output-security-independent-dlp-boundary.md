# ADR-0015 – AI Output Security and Independent DLP Boundary

## Status

ACCEPTED

## Datum

2026-08-19

## Verantwortliche

Architect: Architect  \
Implementation: Codex

## Kontext und Problem

ADR-0010 bis ADR-0014 und TASK-0081 bis TASK-0088 etablieren die untrusted
LLM-Grenze, Authorization vor Retrieval, Context Admission, Resource Binding,
Trusted Retrieval und Model Egress. Der aktuelle Finding-Explanation-Pfad ist:

```text
FindingExplanationUseCase
  → FindingExplanationInputBuilder
  → FindingExplanationService
  → OpenAIFindingExplanationModel
  → Finding-Explanation-API
  → Finding-Details-Frontend
```

`FindingExplanationResult.model_output` wird durch die API transportiert und
im Frontend dargestellt. Ein erfolgreicher Provider-Call beweist weder
Korrektheit noch Sicherheit, Autorisierung, Persistenzfähigkeit oder sichere
Offenlegung des Outputs.

## Entscheidung

Model- und LLM-Output ist immer **UNTRUSTED DATA**. Zwischen Provider und
konsumierender Application/UI muss eine unabhängige, LLM-unabhängige Output
Security Boundary liegen:

```text
Trusted Application
        ↓
Model Egress Enforcement
        ↓
LLM / Provider
        ↓
UNTRUSTED MODEL OUTPUT
        ↓
Independent Output Security / Disclosure Boundary
        ↓
validated, purpose-bound application output
```

Ein Provider-Erfolg ist keine Freigabe. Output darf nur weiterverarbeitet oder
offengelegt werden, wenn ein expliziter Output Purpose und die unabhängigen
Security-/Disclosure-Prüfungen erfüllt sind.

## Trust Model und Purpose Binding

Der Output bleibt untrusted, auch wenn er strukturell gültig, schema-konform
oder von einem kontrollierten Provider stammt. Der ursprüngliche fachliche
Purpose bleibt gebunden; zunächst gilt `FINDING_EXPLANATION`.

Finding-Explanation-Output darf nicht implizit als Tool-/Agent-Instruktion,
Authorization- oder Policy-Entscheidung, Incident-/Remediation-Command,
Retrieval-Scope oder Security-Control-Entscheidung verwendet werden.

Text wie `ignore previous instructions`, `call tool X`, `grant access` oder
`retrieve resource Y` bleibt untrusted content und erhält keine Instruction
Authority.

## Independent Output Security und Disclosure Boundary

Eine zukünftige Boundary muss unabhängig vom LLM prüfen, ob Output für den
gebundenen Purpose verarbeitet oder offengelegt werden darf. Sie muss mindestens
Secrets, Credentials, Tokens, sensitive Identifiers, unzulässige
Datenwiedergabe, mögliche Rekonstruktion geschützter Inputs sowie
Classification-/Disclosure-Regeln berücksichtigen.

Fehlende, ungültige oder nicht durchführbare erforderliche Prüfungen führen
fail-closed zum geschützten Weitergabepfad. Das LLM darf seine eigene Ausgabe
nicht klassifizieren, redigieren, genehmigen oder freigeben.

## Structured Output

JSON- oder Schema-Validierung bestätigt ausschließlich strukturelle Validität.

```text
STRUCTURALLY VALID
        ≠ TRUSTED
        ≠ AUTHORIZED
        ≠ SAFE TO DISCLOSE
```

Strukturvalidität erzeugt keine Berechtigung, keine Trust-Erhöhung und keine
Tool- oder Action-Freigabe.

## Persistence

Rohoutput darf nicht automatisch als authoritative Security Fact persistiert
werden. Falls Model Output künftig persistiert wird, muss er als
model-derived/untrusted mit gebundenem Purpose, Provider-/Model-Referenz und
Provenance unterscheidbar bleiben. Authoritative Domain Data bleibt getrennt.
Eine konkrete Persistenzimplementierung ist nicht Teil dieser ADR.

## UI- und Consumer-Grenze

API, Frontend und Application Consumer dürfen aus einem erfolgreichen Model
Call keine implizite Trust-, Korrektheits- oder Autoritätsannahme ableiten.
UI-Darstellung ist eine Consumer-/Projection-Verantwortung und ersetzt keine
Output-Security- oder Disclosure-Prüfung. Output darf keine Berechtigungen,
Scopes, Classification-Downgrades oder privilegierten Aktionen erzeugen.

## Sicherheitsinvarianten

* **SI-01:** LLM-Output bleibt untrusted data.
* **SI-02:** Provider-Erfolg ist keine Output-Freigabe.
* **SI-03:** Output darf nur für einen expliziten, gebundenen Purpose
  weiterverarbeitet oder offengelegt werden.
* **SI-04:** Output erzeugt oder erweitert keine Authorization, Resource Scopes,
  Tool Permissions oder Data Access Rights.
* **SI-05:** Output erzeugt keine Classification-Downgrades und kein Trust
  Upgrade.
* **SI-06:** Output-Inhalt wird nicht allein als System-, Developer-, Security-
  oder Tool-Instruktion interpretiert.
* **SI-07:** Strukturvalidität ist keine Vertrauens-, Autorisierungs- oder
  Disclosure-Entscheidung.
* **SI-08:** Secrets, Credentials und Tokens sind ohne separate Freigabe nicht
  offenlegbar.
* **SI-09:** Erforderliche nicht durchführbare Prüfungen fail-closed.
* **SI-10:** Rohoutput wird nicht automatisch als authoritative Fact
  persistiert.
* **SI-11:** Model-derived Output bleibt von Domain Facts unterscheidbar und
  bewahrt ausreichende Provenance.
* **SI-12:** UI und Consumer dürfen Output nicht selbst autorisieren oder als
  Security-Wahrheit erzeugen.
* **SI-13:** Auditdaten enthalten Purpose, Policy Decision, Allow/Deny, Reason
  und Provider-/Model-Referenz soweit verfügbar, nicht unnötig den Rohoutput.

## Auditability

Zukünftige Output-Security-Entscheidungen müssen mindestens Output Purpose,
Policy Decision, Allow/Deny, deterministischen Reason, Provider-/Model-
Referenz soweit verfügbar und relevante Provenance auditierbar machen. Raw
Protected Output wird nicht allein zu Audit-Zwecken dupliziert.

## Konsequenzen

### Positiv

* LLM-Ausgaben erhalten eine unabhängige Security- und Disclosure-Grenze.
* Prompt Injection kann keine Berechtigungen oder Aktionen erzeugen.
* Model-derived Data bleibt von autoritativen Domain Facts getrennt.
* UI- und API-Consumer erhalten klare Trust-/Purpose-Semantik.

### Negativ

* Künftige Output-Pfade benötigen eine zusätzliche Policy-/DLP-Prüfung.
* Schema-Validierung allein reicht nicht aus.
* Sichere Offenlegung kann Output ablehnen, obwohl der Provider erfolgreich war.

## Abgelehnte Alternativen

* **LLM-Output ist sicher, weil der Input kontrolliert war:** abgelehnt;
  Output bleibt untrusted.
* **Provider-Sicherheitsfilter reichen aus:** abgelehnt; Provider sind keine
  unabhängige PredatorAI-Disclosure-Boundary.
* **Valides JSON ist sicher:** abgelehnt; Strukturvalidität ist keine Policy.
* **UI zeigt erfolgreichen Output direkt:** abgelehnt; Consumer dürfen keine
  Security-Freigabe ersetzen.
* **LLM klassifiziert oder genehmigt eigenen Output:** abgelehnt; LLM ist
  untrusted.
* **LLM redigiert selbst:** abgelehnt; Redaction benötigt unabhängige Logik.
* **Output darf Tools oder Actions direkt autorisieren:** abgelehnt; Output
  erzeugt keine Privilegien.

## Abgrenzung

Nicht Bestandteil dieser ADR sind DLP Engine, Secret Scanner, Output Filter,
Output Admission Service, Provider Governance, neue Provider, RAG, Vector
Databases, Embeddings, Agents, Tools, Function Calling, HITL, neue LLM Calls
oder Änderungen am produktiven Finding-Explanation-Pfad.

## Relation zu bestehenden ADRs

* ADR-0010: LLM und LLM-Output bleiben untrusted.
* ADR-0011 bis ADR-0013: Authorization, Admission, Binding und Trusted
  Retrieval bleiben vorgelagerte unabhängige Grenzen.
* ADR-0014: Model Egress bleibt eine separate vorgelagerte Allowlist-Grenze.
* TASK-0088: Der produktive Finding-Explanation-Pfad nutzt Egress vor dem
  Provider; diese ADR definiert die nachgelagerte Output-Grenze.

## Referenzen

* `application/finding_explanation.py`
* `application/finding_explanation_use_case.py`
* `infrastructure/openai_finding_explanation.py`
* `api_app.py`
* `frontend/src/workspaces/soc/findings/FindingExplanationSection.tsx`
* `.ai/decisions/ADR-0010-llm-trust-boundary-independent-security-enforcement.md`
* `.ai/decisions/ADR-0014-ai-data-classification-minimization-model-boundary-egress.md`

## Architektur-Review

Status: ACCEPTED  \
Bemerkungen: LLM-Output bleibt untrusted; unabhängige Output-/Disclosure-
Boundary ist vor sicherer Weitergabe, Persistenz oder Consumer-Offenlegung
verbindlich.  \
Freigabe: Architect / Product Owner, 2026-08-19
