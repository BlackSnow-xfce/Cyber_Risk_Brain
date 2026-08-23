# ADR-0014 – AI Data Classification, Minimization and Model-Boundary Egress

## Status

ACCEPTED

## Datum

2026-08-19

## Verantwortliche

Architect: Architect  \
Implementation: Codex

## Kontext

ADR-0010 bis ADR-0013 etablieren die Untrusted-LLM-Grenze, Authorization vor
Retrieval, unabhängige Context Admission, deterministische Resource-Bindings
und eine serverseitige Trusted Retrieval Boundary. TASK-0081 bis TASK-0085
liefern die zugehörigen Contracts und den ersten Finding-Retrieval-Pfad.

Zugriffsberechtigung auf eine Resource bedeutet jedoch nicht automatisch die
Berechtigung, sämtliche darin enthaltenen Daten an ein Modell oder einen
externen Provider offenzulegen. Dafür ist eine separate, deterministische
Model-Egress-Grenze erforderlich.

## Entscheidung

PredatorAI erzwingt vor jeder Model-/Provider-Grenze explizite Classification,
zweckgebundene Data Minimization und eine deterministische Egress-Entscheidung.
Nur die für den genehmigten AI Purpose ausdrücklich erlaubten Felder dürfen die
Model-Grenze passieren.

Access Authorization und AI-/Model-Egress-Authorization bleiben getrennte
Security-Entscheidungen:

```text
Access Authorization
        ↓
Trusted Retrieval
        ↓
BoundAIContext
        ↓
Context Admission
        ↓
Classification + AI Purpose + Minimization
        ↓
Model-Egress Policy
        ↓
minimal erlaubtes Model Payload
        ↓
LLM / Provider (UNTRUSTED)
```

## Sicherheitsinvarianten

* **SI-01:** Access Authorization autorisiert Model Disclosure nicht
  automatisch.
* **SI-02:** Erfolgreiches Retrieval autorisiert Model Disclosure nicht
  automatisch.
* **SI-03:** Context Admission autorisiert Model Disclosure nicht automatisch.
* **SI-04:** Geschützte Daten benötigen vor Model Egress eine deterministische
  Classification.
* **SI-05:** Fehlende oder nicht auflösbare Classification fail-closed.
* **SI-06:** Fehlende Classification bedeutet niemals automatisch `PUBLIC`.
* **SI-07:** Nur explizit für den genehmigten AI Purpose erlaubte Felder werden
  in das Payload aufgenommen.
* **SI-08:** Minimization erfolgt vor der Model-/Provider-Grenze.
* **SI-09:** Secrets und Credentials sind standardmäßig vom Model Egress
  ausgeschlossen. Eine Freigabe erfordert eine spätere Security-ADR.
* **SI-10:** Egress-Entscheidungen sind deterministisch und unabhängig vom LLM.
* **SI-11:** Das LLM bestimmt nicht, welche geschützten Felder es erhalten darf.
* **SI-12:** Prompt-Text erweitert weder erlaubte Felder noch Classification-
  oder Purpose-Scope.
* **SI-13:** Retrieved Content erteilt sich selbst keine Disclosure-Erlaubnis.
* **SI-14:** Ein weiterer User-Access-Scope erweitert den Model-Egress-Scope
  nicht automatisch.
* **SI-15:** Ausgeschlossene Daten werden nicht wegen vermeintlicher
  Antwortqualität nachträglich gesendet.
* **SI-16:** Model-Payloads werden durch vertrauenswürdige Application-Logik
  konstruiert.
* **SI-17:** Ein Fallback auf die vollständige Resource ist verboten.
* **SI-18:** Egress-Entscheidungen behalten ausreichende Source-/Provenance-
  Referenzen für Auditierbarkeit, ohne unnötige geschützte Metadaten an das
  Modell zu geben.
* **SI-19:** Egress-Freigabe macht den zugrunde liegenden Content nicht trusted.
* **SI-20:** Provider- oder Model-Auswahl darf Egress-Beschränkungen nicht
  stillschweigend überschreiben.

## Classification

Es wird die bestehende `AIContextClassification` aus TASK-0081 verwendet:

* `PUBLIC`
* `INTERNAL`
* `CONFIDENTIAL`
* `RESTRICTED`

Diese ADR führt keine konkurrierende Classification-Hierarchie ein. Wo eine
Domain-Resource keine explizite Classification besitzt, muss die Zuordnung
zentral, deterministisch und konservativ erfolgen. `PUBLIC` darf nicht aus
Abwesenheit einer Classification abgeleitet werden.

## Data Minimization und AI Purpose

Model-Payloads verwenden eine Allowlist explizit erlaubter Felder. Die sichere
Voreinstellung ist:

```text
ausdrücklich erlaubte Felder → einschließen
alles andere                 → ausschließen
```

Ein Egress-Entscheid benötigt einen deterministischen AI-Purpose-Identifier.
Beispiele wie `finding_explanation`, `incident_summary`, `threat_analysis`
oder `remediation_assistance` sind lediglich mögliche spätere Zwecke. Diese
ADR definiert keinen finalen Purpose-Katalog. Freie natürliche Sprache darf
keinen neuen autorisierten Zweck erzeugen.

## Secrets und Compliance-Grenze

API Keys, Access Tokens, Passwörter, private Schlüssel, Session Credentials und
andere Authentication Secrets sind standardmäßig vom Model Egress abgelehnt.
Diese ADR implementiert weder Secret-Redaction noch einen Secrets Manager.

Die ADR schafft Classification, Zweckbindung, Minimization und Auditierbarkeit,
behauptet aber keine GDPR-, EU-AI-Act- oder sonstige Rechtskonformität. Solche
Mappings benötigen separate Governance-Entscheidungen.

## Auditierbarkeit

Spätere Egress-Entscheidungen müssen anhand von AI Purpose,
Source-/Resource-Referenz, Classification, ausgewählten und gegebenenfalls
ausgeschlossenen Feldern, Policy-/Decision-Referenz sowie späterem
Model-/Provider-Ziel erklärbar sein. Vollständige geschützte Payloads werden
nicht als Standard-Audit-Store vorgeschrieben.

## Relation zu bestehenden Entscheidungen

* ADR-0010 – LLM bleibt untrusted; Security hängt nicht vom LLM ab.
* ADR-0011 – Authorization vor Retrieval und unabhängige Context Admission.
* ADR-0012 – deterministische Resource-Bindung des Retrieved Content.
* ADR-0013 – Trusted Retrieval Boundary besitzt Retrieval- und Binding-
  Ownership.
* TASK-0081 – `AIContextClassification` und Provenance.
* TASK-0082 – Access Authorization Scope.
* TASK-0083 – Context Admission.
* TASK-0084 – `BoundAIContext 1.0`.
* TASK-0085 – erster Finding Trusted Retrieval Path.

Model Egress ist eine zusätzliche Security Boundary und ersetzt keine dieser
Entscheidungen.

## Alternativen

* **Vollständige autorisierte Resource senden:** abgelehnt; Access bedeutet
  nicht Model Disclosure und verletzt Minimization.
* **Vollständiges Serialisieren und bekannte Felder redigieren:** als Default
  abgelehnt; neue oder unbekannte sensible Felder könnten durchsickern.
* **LLM wählt benötigte Felder:** abgelehnt; das LLM ist untrusted.
* **`INTERNAL` automatisch extern freigeben:** abgelehnt; Classification,
  Purpose und Destination benötigen eine eigene Policy.
* **Fehlende Classification als `PUBLIC` behandeln:** abgelehnt; verletzt
  Fail-Closed-Semantik.
* **Prompt definiert neue Egress-Zwecke:** abgelehnt; Zwecke müssen
  deterministisch autorisiert sein.
* **Komplette geschützte Payloads für Audit loggen:** als Default abgelehnt;
  Auditierbarkeit darf keinen zweiten Sensitive-Data-Store erzeugen.

## Abgrenzung

Nicht Bestandteil dieser ADR sind Model-Egress-Code, DLP-/Redaction-Engines,
Provider- oder Model-Auswahl, Provider-Allowlisting, Data Residency,
Retention, Rechtszertifizierung, RAG, Vector Databases, Embeddings,
LLM-Aufrufe, Frontend, APIs, Agents, Tools und Secrets Manager.

## Migration

Künftige Model-/Provider-Pfade müssen Egress als eigene serverseitige Boundary
nach Retrieval und Admission einführen. Bestehende AIContext-, Authorization-,
Binding- und Retrieval-Contracts bleiben unverändert und werden wiederverwendet.

## Qualitäts- und Sicherheitsauswirkungen

Die Entscheidung reduziert Over-Disclosure-, unbekannte-Feld- und
Prompt-Injection-Risiken. Sie führt keine Runtime-Infrastruktur ein und
verändert keine bestehende Produktlogik. Künftige Egress-Pfade benötigen
zusätzliche deterministische Policy- und Audit-Tests.

## Referenzen

* `.ai/decisions/ADR-0010-llm-trust-boundary-independent-security-enforcement.md`
* `.ai/decisions/ADR-0011-authorization-before-retrieval-ai-context-admission.md`
* `.ai/decisions/ADR-0012-retrieved-content-resource-binding-admission-integrity.md`
* `.ai/decisions/ADR-0013-trusted-retrieval-boundary-bound-context-construction.md`
* `core/ai_context/context.py`
* `core/ai_authorization/scope.py`
* `.ai/decisions/README.md`

## Architektur-Review

Status: ACCEPTED  
Bemerkungen: Model Egress bleibt eine eigene, deterministische Boundary;
Access, Retrieval und Admission werden nicht als Disclosure-Erlaubnis
interpretiert.  
Freigabe: Architect / Product Owner, 2026-08-19
