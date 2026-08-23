# ADR-0011 – Authorization Before Retrieval and AI Context Admission

## Status

ACCEPTED

## Datum

2026-08-19

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

Künftige Retrieval- und RAG-Boundaries können geschützte Informationen für
eine AI-Verarbeitung bereitstellen. ADR-0010 stellt bereits fest, dass LLMs
und ihre Ausgaben untrusted sind und dass Authorization unabhängig vom LLM
durchgesetzt werden muss. TASK-0081 definiert mit `AIContextItem 1.0` die
Trust-, Provenance- und Classification-Semantik für zugelassenen AI-Kontext.

Es ist daher festzulegen, dass die Autorisierung vor Retrieval und zusätzlich
vor der Aufnahme eines Ergebnisses in einen AI-/LLM-Kontext erfolgt.

## Entscheidung

PredatorAI autorisiert den Zugriff auf geschützte Daten vor deren Retrieval
für AI-Verarbeitung oder Aufnahme in einen LLM-Kontext. Ein LLM darf den
autorisierten Ressourcenumfang weder bestimmen, erweitern, überschreiben noch
reparieren. Nicht autorisierte Informationen dürfen keinen LLM-Kontext
erreichen.

Authorization berücksichtigt deterministisch mindestens Subject/Identity,
Operation, Ressource beziehungsweise Ressourcentyp, autorisierten Scope und
gegebenenfalls Data Classification. Diese ADR schreibt weder ein konkretes
RBAC-/ABAC-Produkt noch einen Identity Provider oder eine Policy Engine vor.

### Sicherheitsinvarianten

* **SI-01:** Geschützte Daten unterliegen vor AI-Retrieval einer Authorization.
* **SI-02:** Nicht autorisierte Daten werden nicht in einen LLM-Kontext
  aufgenommen.
* **SI-03:** Ein LLM bestimmt oder erweitert niemals den autorisierten Scope.
* **SI-04:** Authorization basiert auf deterministischem serverseitigem
  Security Context, nicht auf natürlicher Sprachinterpretation.
* **SI-05:** Fehlender, ungültiger oder unbestimmter Authorization Context
  führt fail-closed zum Abbruch.
* **SI-06:** Unbekannter oder nicht auflösbarer geschützter Ressourcenscope
  führt fail-closed zum Abbruch.
* **SI-07:** Output-Filtering ersetzt keine Authorization vor Retrieval.
* **SI-08:** Die Context-Admission prüft unabhängig, dass abgerufener Inhalt
  mit dem autorisierten Scope kompatibel ist.
* **SI-09:** Classification und Provenance bleiben für Admission-Entscheidungen
  verfügbar, sofern erforderlich.
* **SI-10:** Prompt Injection kann weder Retrieval-Scope erweitern noch nicht
  autorisierte Daten in den Modellkontext einschleusen.

### Verbindliche Reihenfolge

```text
Authenticated Identity
        ↓
Authorization Context
        ↓
Policy / Scope Decision
        ↓
Authorized Resource Scope
        ↓
Retrieval
        ↓
AI Context Admission
        ↓
AIContextItem 1.0
        ↓
LLM (untrusted)
```

Authorization ist für geschützte Daten Voraussetzung des Retrievals. Die
spätere Context-Admission ist eine zweite unabhängige Boundary: fehlender
Context, nicht auflösbare Ressource, unzulässige Classification, fehlende oder
ungültige Provenance sowie ungültige `AIContextItem`-Semantik führen zur
Ablehnung. Es gibt keinen stillen Fallback auf breiteren Retrieval-Scope.

Explizit als public/non-protected klassifizierte Quellen dürfen einen
vereinfachten deterministischen Policy-Pfad verwenden. Fehlende Classification
gilt jedoch nicht automatisch als PUBLIC.

## Begründung

Die Reihenfolge verhindert, dass geschützte Daten die Sicherheitsgrenze bereits
vor einer nachgelagerten Ausgabeprüfung überschreiten. Sie hält Authorization
und Context Admission außerhalb des untrusted LLM und bewahrt die Single
Source of Truth der bestehenden Domain-Boundaries.

## Konsequenzen

### Positiv

* Nicht autorisierte Daten werden vor Retrieval und Context Admission blockiert.
* Prompt Injection kann den Ressourcenscope nicht erweitern.
* `AIContextItem 1.0` bleibt die einzige AI-Kontextrepräsentation.
* Classification und Provenance bleiben für Sicherheitsentscheidungen
  nachvollziehbar.

### Negativ

* Künftige Retrieval-Boundaries benötigen einen expliziten Authorization Context.
* Context Admission muss unabhängig vom Retrieval validieren.
* Eine konkrete Authorization-/Identity-/Policy-Infrastruktur ist weiterhin
  offen.

## Alternativen

* **Retrieve first, LLM soll Inhalte verbergen:** abgelehnt; geschützte Daten
  haben die Sicherheitsgrenze bereits überschritten.
* **Breites Retrieval mit reinem Output-/DLP-Filter:** abgelehnt; Filtering ist
  Defense in Depth und keine Zugriffskontrolle.
* **LLM leitet Berechtigungen aus Prompt oder Konversation ab:** abgelehnt;
  LLM-Ausgaben sind untrusted und nicht deterministisch.
* **Unrestricted Retrieval bei fehlendem Authorization Context:** abgelehnt;
  verletzt Fail-Closed-Access-Control.
* **Alle PredatorAI-Quellen sind automatisch autorisiert:** abgelehnt;
  Systemzugriff bedeutet keine Benutzerautorisierung.

## Abgrenzung

Diese ADR definiert ausschließlich die architektonische Reihenfolge und
Sicherheitsanforderungen für Authorization, Retrieval und Context Admission.

Nicht Bestandteil sind:

* RAG, Vektordatenbanken, Embeddings oder Retrieval-Algorithmen;
* konkrete RBAC-/ABAC-Infrastruktur, Identity Provider oder Policy Engine;
* Agenten, Tools, DLP oder Output Guarding;
* neue LLM-Aufrufe, Frontend oder API-Endpunkte;
* eine Implementierung der Context-Admission-Boundary.

## Migration

Künftige AI-Retrieval-Boundaries müssen vor dem Zugriff auf geschützte Daten
einen deterministischen Authorization Context und Scope herstellen. Vor der
LLM-Grenze müssen sie Retrieval-Ergebnis, Resource Identity, Classification,
Provenance und `AIContextItem 1.0` erneut prüfen. Bestehende Finding-, Asset-,
Threat-Intelligence-, Evidence- und Decision-Contracts bleiben unverändert.

## Qualitäts- und Sicherheitsauswirkungen

Die ADR stärkt Least Privilege, Prompt-Injection-Resilienz und Fail-Closed-
Verhalten. Sie führt keine Runtime-Infrastruktur ein und erzeugt keine neuen
Produkt- oder Provider-Abhängigkeiten.

## Referenzen

* `.ai/decisions/ADR-0010-llm-trust-boundary-independent-security-enforcement.md`
* `core/ai_context/context.py`
* `.ai/decisions/README.md`
* `AGENTS.md`

## Architektur-Review

Status: ACCEPTED  
Bemerkungen: Authorization vor Retrieval und unabhängige Context Admission;
LLM bleibt untrusted.  
Freigabe: Architect / Product Owner, 2026-08-19
