# ADR-0001 – DecisionResult as Canonical Decision Contract

## Status

ACCEPTED

## Datum

2026-08-04

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI besitzt im Python-Backend zwei Strukturen, die derzeit eine kanonische Rolle für abgeschlossene Entscheidungen beanspruchen oder faktisch einnehmen.

`core/decision/models.py` definiert `DecisionResult` zusammen mit den zugehörigen fachlichen Typen `DecisionPriority`, `DecisionAction`, `AttackReasoning`, `BusinessImpact`, `Confidence`, `Recommendation` und `Evidence`. `DecisionResult` bündelt:

- die referenzierte Finding-ID,
- die fachliche Entscheidung,
- Priorität und Aktion,
- Attack Reasoning,
- Business Impact,
- Confidence,
- Recommendations,
- Evidence,
- und erweiterbare Metadaten.

Das Modell validiert zentrale Invarianten, stellt fachlich typisierte Enums bereit und besitzt mit `to_dict()` eine explizite Serialisierungsprojektion.

`core/explainability/decision_trace_builder.py` verwendet `DecisionResult` bereits als alleinige Eingabe und transformiert es strukturell in `core.explainability.decision_trace.DecisionTrace`. Der Builder dokumentiert ausdrücklich, dass er weder Risiko, Priorität, Aktion oder Confidence verändert noch neue Recommendations erzeugt. Damit besteht bereits eine klare Dependency Direction vom fachlichen Ergebnis zur Explainability-Projektion.

Daneben definiert `core/decision/decision_trace.py` eine weitere Klasse `DecisionTrace`. Ihr Docstring bezeichnet sie als „Canonical decision object“. Diese Struktur verwendet jedoch eine andere Modellfamilie und kombiniert mehrere Verantwortlichkeiten:

- fachliches Decision-Ergebnis,
- Confidence und AI Review,
- Reasons und Evidence,
- Threat Intelligence und Correlations,
- Business Impact und Recommendations,
- Attack Path,
- Timeline,
- rollenbezogene Zusammenfassungen,
- und Darstellungsmetadaten.

Der zugehörige `core/decision/decision_trace_builder.py` erzeugt diese Struktur aus einem veränderlichen `DecisionContext`, einem `ReasoningResult` und mehreren Buildern. Während des Builds schreibt er Evidence, Recommendations und Business Impact zurück in den Context. Diese Struktur beschreibt damit nicht ausschließlich den stabilen fachlichen Output einer abgeschlossenen Decision.

Ohne eine explizite Festlegung bestehen folgende Risiken:

- zwei konkurrierende kanonische Decision-Verträge,
- uneindeutige Abhängigkeiten für API, Explainability und Frontend,
- Drift zwischen fachlich gleichnamigen Typen,
- vermischte Verantwortlichkeiten zwischen Ergebnis, Ausführung und Präsentation,
- und eine spätere Parallelarchitektur für Reasoning Sessions und Execution Traces.

## Entscheidung

`core.decision.models.DecisionResult` wird als einziges kanonisches fachliches Ergebnis einer abgeschlossenen Decision in PredatorAI v3 vorgeschlagen.

Für alle künftigen Architektur- und Implementierungsentscheidungen gelten damit folgende Grenzen:

1. `DecisionResult` ist die Backend-Single-Source-of-Truth für das fachliche Decision-Ergebnis.
2. Eine Explainability-Struktur ist eine read-only Projektion aus `DecisionResult` und darf keine fachliche Entscheidung erzeugen oder verändern.
3. Ein API-Vertrag ist eine versionierte Transportprojektion des kanonischen Ergebnisses. Er darf das Domainmodell nicht als zweite fachliche Quelle duplizieren.
4. Frontend-Modelle sind Presentation-Verträge. Sie dürfen Decision-Daten darstellen, aber weder fachliche Invarianten noch Decision-Logik definieren.
5. Ein künftiger Execution Trace beschreibt ausschließlich den zeitlichen beziehungsweise technischen Ablauf einer Reasoning-Ausführung. Er ist weder `DecisionResult` noch Explainability-Projektion.
6. `core/decision/decision_trace.DecisionTrace` wird durch diesen ADR nicht entfernt, umbenannt oder migriert. Sein bestehender „canonical“-Anspruch wird für künftige Architekturentscheidungen nicht als verbindlich betrachtet.
7. `core/explainability/decision_trace.DecisionTrace` bleibt eine aus `DecisionResult` abgeleitete Explainability-Projektion und ist kein kanonisches Decision-Ergebnis.

Die fachliche Abhängigkeitsrichtung lautet:

```text
Decision Engine
      │
      ▼
DecisionResult
      ├──→ versionierte API-Projektion
      ├──→ Explainability-Projektion
      └──→ Frontend-Presentation-Modell

Reasoning-Ausführung ──→ künftiger Execution Trace
```

Ein Execution Trace darf `DecisionResult` oder dessen stabile Referenz als erzeugtes Artefakt referenzieren, aber seine Felder nicht als konkurrierendes Decision-Ergebnis kopieren.

## Begründung

`DecisionResult` ist die technisch geeignetste bestehende kanonische Struktur:

- Es liegt im Backend-Domainbereich `core/decision`.
- Es modelliert ein abgeschlossenes fachliches Ergebnis statt eines Ausführungsablaufs.
- Es verwendet klar typisierte Enums und zusammengesetzte fachliche Modelle.
- Es enthält zentrale Validierungen für Identität, Entscheidung, Confidence und Recommendations.
- Es bietet eine explizite Serialisierung, ohne API- oder UI-Abhängigkeiten zu importieren.
- Der bestehende Explainability-Builder akzeptiert ausschließlich `DecisionResult` und bestätigt damit bereits die gewünschte Abhängigkeitsrichtung.
- Die Explainability-Projektion ist unveränderlich und strukturell aus dem Ergebnis abgeleitet.

Die alternative `core.decision.decision_trace.DecisionTrace` ist als kanonischer Ergebnisvertrag weniger geeignet, weil sie mehrere fachliche und präsentationsnahe Verantwortlichkeiten bündelt, andere Decision-Untertypen verwendet und aus einem veränderlichen Context sowie AI-Reasoning-Daten aufgebaut wird. Ihre Felder reichen über das abgeschlossene Decision-Ergebnis hinaus.

Die Entscheidung folgt den Prinzipien aus `ARCHITECTURE.md`:

- Backend as Single Source of Truth,
- One Canonical Model per Concept,
- Explicit Responsibilities,
- Dependencies Point Inward,
- Explainability by Design,
- und No Parallel Architectures.

## Konsequenzen

### Positiv

- Künftige Backend-Komponenten erhalten einen eindeutigen fachlichen Decision-Vertrag.
- API, Explainability und Frontend können als gerichtete Projektionen entworfen werden.
- Decision-Ergebnis, Execution Trace und Explainability bleiben getrennte Konzepte.
- Neue Reasoning- oder Session-Infrastruktur muss keine Decision-Felder duplizieren.
- Tests können fachliche Invarianten zentral gegen `DecisionResult` absichern.
- Die bereits bestehende Explainability-Transformation entspricht der vorgeschlagenen Zielrichtung.
- Die Gefahr konkurrierender Domainmodelle wird reduziert.

### Negativ

- Bestehende Verbraucher der älteren `core.decision.decision_trace.DecisionTrace`-Struktur bleiben vorerst architektonische Migration Debt.
- Gleichnamige `DecisionTrace`-Klassen bleiben bis zu späteren, separat freigegebenen Entscheidungen missverständlich.
- `DecisionResult` ist aktuell eine veränderliche Dataclass und enthält veränderliche Listen und Dictionaries; Kanonizität bedeutet daher noch keine garantierte Unveränderlichkeit.
- Das Modell ist derzeit explizit auf `finding_id` ausgerichtet. Eine spätere Erweiterung auf andere Entity-Typen benötigt eine eigene kompatible Entscheidung.
- `to_dict()` ist eine direkte Serialisierung, aber noch kein explizit versionierter API-Vertrag.
- Verbraucher müssen langfristig zwischen Domainmodell und Transportprojektion unterscheiden.

## Alternativen

### `core.decision.decision_trace.DecisionTrace` als kanonisches Ergebnis beibehalten

Nicht vorgeschlagen.

Die Klasse enthält neben Decision-Daten auch AI-Review, Threat Intelligence, Correlations, Timeline, Stories und Remediation. Ihr Builder liest aus mehreren Quellen und verändert den übergebenen Context. Dadurch ist sie ein aggregiertes Ausgabe- beziehungsweise Darstellungsmodell und kein klar begrenztes abgeschlossenes Decision-Ergebnis.

### `core.explainability.decision_trace.DecisionTrace` als kanonisches Ergebnis verwenden

Nicht vorgeschlagen.

Die Klasse ist ausdrücklich eine strukturierte Explainability-Repräsentation. Sie enthält eine sortierte Sammlung von `ExplanationItem`-Projektionen und wird aus `DecisionResult` aufgebaut. Eine abgeleitete Sicht darf ihre Quelle nicht ersetzen.

### Ein neues kanonisches Decision-Modell erstellen

Nicht vorgeschlagen.

Ein zusätzliches Modell würde gegen „One Canonical Model per Concept“ und „No Parallel Architectures“ verstoßen. `DecisionResult` erfüllt die Kernverantwortung bereits. Notwendige Weiterentwicklungen sollen später kontrolliert am kanonischen Vertrag oder über versionierte Projektionen erfolgen.

### API- oder Frontend-Modell als gemeinsame Wahrheit verwenden

Abgelehnt.

Transport- und Presentation-Modelle werden von Verbraucheranforderungen bestimmt. Würden sie die fachliche Wahrheit definieren, zeigten Abhängigkeiten nach außen und Businesslogik könnte in Delivery- oder UI-Schichten wandern.

### Vorläufig keine kanonische Struktur festlegen

Nicht vorgeschlagen.

Die bestehende Doppelbezeichnung erzeugt bereits Architekturunsicherheit. Sprint 13 benötigt eine eindeutige Grundlage, bevor Session-, Execution-Trace- oder weitere Explainability-Verträge entworfen werden.

## Abgrenzung

Dieser ADR:

- verändert keine Python-Datei,
- verändert kein Domainmodell,
- entfernt oder benennt keine `DecisionTrace`-Klasse um,
- konsolidiert keine Builder,
- verändert keine Decision-, Risk-, Confidence- oder Recommendation-Logik,
- führt keinen Execution Trace ein,
- führt keine Reasoning Session ein,
- definiert keine Persistenz,
- ändert keine API,
- ändert keine Frontend-Typen oder UI,
- und entscheidet nicht über die konkrete Migration bestehender Verbraucher.

Die Architektur von Execution Trace und Explainability Projection wird in separaten ADRs entschieden.

## Migration

Dieser ADR implementiert keine Migration.

Nach einer Annahme soll eine spätere Migration ausschließlich über kleine, separat freigegebene AIDP-Tasks vorbereitet werden:

1. Bestehende Produzenten und Verbraucher beider `DecisionTrace`-Klassen inventarisieren.
2. API-, Dashboard-, Reporting- und Story-Verträge auf ihre tatsächliche Quelle prüfen.
3. Kompatibilitätsanforderungen und notwendige versionierte Projektionen dokumentieren.
4. Den älteren aggregierten Decision Trace nach Verantwortlichkeiten klassifizieren, ohne sofortige Umbenennung.
5. Verbraucher einzeln auf den kanonischen Ergebnis- oder einen expliziten Projektionsvertrag umstellen.
6. Erst nach erfolgreicher Migration über Deprecation oder Entfernung entscheiden.

Jeder Schritt benötigt einen eigenen Scope, Tests und Rollback-Betrachtung. Eine Big-Bang-Migration ist nicht vorgesehen.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität

- Domain-Tests sollen künftig die Invarianten und Serialisierung von `DecisionResult` abdecken.
- Projektions-Tests sollen nachweisen, dass Explainability keine fachlichen Werte verändert.
- Contract-Tests sollen API-Projektionen gegen den kanonischen Backend-Vertrag absichern.
- Vor einer Implementierung muss zunächst die geplante Python-Testgrundlage freigegeben werden.

### Security

- `metadata` und Evidence-Werte können sensible oder unstrukturierte Inhalte enthalten. Transportprojektionen müssen Felder explizit freigeben und dürfen interne Daten nicht ungeprüft exponieren.
- Das direkte Vorhandensein von `to_dict()` ist keine Autorisierung zur Veröffentlichung sämtlicher Felder.
- Künftige Persistenz- und Audit-Verträge müssen Datenminimierung, Zugriffskontrolle und Aufbewahrung gesondert definieren.

### Auditierbarkeit

- Ein kanonisches Decision-Ergebnis verbessert die fachliche Rückverfolgbarkeit.
- `DecisionResult` ersetzt keinen Execution Trace. Zeitpunkt, Regeln, Versionen und Verarbeitungsschritte benötigen einen getrennten Audit-Vertrag.
- Stabile Ergebnisidentität und Versionierung sind noch nicht vollständig modelliert und bleiben ein Folgethema.

### Performance

- Eine gerichtete Projektion vermeidet unnötige parallele Berechnungen.
- Große Evidence-, Recommendation- oder Metadata-Sammlungen können Serialisierungs- und Kopierkosten verursachen; dieser ADR legt keine Optimierung oder Lazy-Loading-Strategie fest.
- Performance-Änderungen dürfen Domain- und Projektionsgrenzen nicht umgehen.

### Kompatibilität

- Dieser Dokumentationstask verursacht keine Breaking Changes.
- Eine spätere Umstellung bestehender Verbraucher kann Vertragsänderungen auslösen und benötigt eine eigene Kompatibilitäts- und Versionierungsstrategie.
- Bestehende `DecisionTrace`-Strukturen bleiben bis zu einer freigegebenen Migration verfügbar.

## Referenzen

- AIDP TASK-0006 – Architecture Charter
- AIDP TASK-0007 – ADR Convention
- AIDP TASK-0008 – Canonical Decision Contract
- `AGENTS.md`
- `ARCHITECTURE.md`
- `.ai/decisions/README.md`
- `core/decision/models.py`
- `core/decision/decision_trace.py`
- `core/decision/decision_trace_builder.py`
- `core/explainability/decision_trace.py`
- `core/explainability/decision_trace_builder.py`
- Geplant: ADR-0002 – Execution Trace
- Geplant: ADR-0003 – Explainability Projection

## Architektur-Review

Status:
APPROVED

Bemerkungen:
Die Entscheidung ist am vorhandenen Backend-Modellbestand technisch belegt und definiert mit `core.decision.models.DecisionResult` genau eine fachliche Single Source of Truth. Decision Trace, Execution Trace, Explainability, API und Frontend werden klar als getrennte Verantwortlichkeiten abgegrenzt. Die dokumentierten Risiken zu Mutabilität, `finding_id`, Vertragsversionierung und bestehender Migration Debt sind nicht blockierend und benötigen separate Folgetasks.

Freigabe:
Architect
