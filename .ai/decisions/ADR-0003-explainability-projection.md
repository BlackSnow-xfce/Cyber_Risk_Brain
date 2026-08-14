# ADR-0003 – Canonical Explainability Projection Contract

## Status

ACCEPTED

## Datum

2026-08-04

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI benötigt eine eindeutige, backendseitige Explainability Projection, über die fachliche Entscheidungen nachvollziehbar und konsistent für API-, Reporting- und Presentation-Verbraucher bereitgestellt werden können.

ADR-0001 legt `core.decision.models.DecisionResult` als kanonisches fachliches Decision-Ergebnis fest. ADR-0002 legt einen getrennten kanonischen Execution Trace als Application-/Audit-Artefakt einer Reasoning-Ausführung fest. Explainability muss beide Verantwortlichkeiten respektieren:

- `DecisionResult` beantwortet, welche fachliche Entscheidung entstanden ist und auf welchen fachlichen Bestandteilen sie beruht.
- Execution Trace beantwortet, welche Verarbeitungsschritte während einer konkreten Ausführung tatsächlich stattgefunden haben.
- Explainability beantwortet, wie vorhandene kanonische Informationen nachvollziehbar für Menschen strukturiert werden.

Im bestehenden Backend existiert unter `core/explainability` bereits eine klar gerichtete Projektionsfamilie:

- `core.explainability.decision_trace.DecisionTrace` beschreibt sich als strukturierte Explainability-Repräsentation eines `DecisionResult`.
- Die Klasse ist als frozen Dataclass angelegt, validiert Identität, Entscheidung, Confidence und eindeutige Item-Sequenzen und sortiert Items deterministisch.
- `ExplanationItem` strukturiert Erklärungselemente über Kategorie, Titel, Beschreibung, Sequenz, Quelle, Importance und Metadaten.
- `DecisionTraceBuilder` erhält genau ein `DecisionResult` und transformiert dessen Decision, Attack Reasoning, Business Impact, Confidence, Evidence und Recommendations in geordnete Erklärungselemente.
- Der Builder dokumentiert ausdrücklich, dass er weder Risiko, Priorität, Aktion oder Confidence verändert noch Recommendations erzeugt oder die Decision neu interpretiert.

Diese Struktur bildet bereits die gewünschte Abhängigkeitsrichtung vom kanonischen Domain-Ergebnis zu einer read-only Explainability-Sicht ab.

Daneben existiert unter `core/decision` eine ältere, gleichnamige `DecisionTrace`-Familie:

- `core.decision.decision_trace.DecisionTrace` bündelt Decision, Risk, AI Review, Evidence, Threat Intelligence, Business Impact, Attack Path, Timeline und rollenbezogene Zusammenfassungen.
- `DecisionCard` wird daraus als UI-Repräsentation erzeugt und enthält UI-Felder wie Farbe, Icon und Expanded State.
- `DecisionCardBuilder` leitet sogar rollenbezogene Titel anhand von Prioritätsstrings ab.
- `DecisionExplainer` erzeugt Executive-, SOC- und Technical-Texte direkt aus dieser aggregierten Struktur.

Diese ältere Familie vermischt fachliches Ergebnis, Erklärung, Rollenprojektion und UI-Bereitung. Sie ist daher keine geeignete kanonische Explainability Projection im Sinne der akzeptierten Architekturgrenzen.

Das Frontend visualisiert aktuell eine Explainability Pipeline aus Knowledge, Bindings, Evidence, Correlations, Inference, Reasoning, Decision und Recommendation. Status und Counts werden unmittelbar aus Frontend-Entity-Modellen abgeleitet. Der Explainability Workspace führt außerdem den Frontend-Orchestrator aus und zeigt dessen Execution Trace separat an.

Diese Komponenten erfüllen Presentation-Verantwortung, können aber nicht die Backend-Single-Source-of-Truth für Explainability sein. Ohne expliziten Projektionsvertrag bestehen folgende Risiken:

- Backend und Frontend definieren unterschiedliche Erklärungsreihenfolgen oder Vollständigkeitszustände,
- fehlende Daten werden durch UI-Annahmen oder generierte Texte verdeckt,
- Explainability erzeugt oder verändert unbemerkt fachliche Aussagen,
- Decision-Ergebnis und Ausführungsverlauf werden in einer universellen Trace-Struktur vermischt,
- Rollenprojektionen entwickeln konkurrierende Bedeutungen,
- Provenance und Vertragsversion bleiben unklar,
- und gleichnamige `DecisionTrace`-Klassen werden als austauschbar behandelt.

## Entscheidung

`core.explainability.decision_trace.DecisionTrace` wird als bestehende Grundlage der kanonischen backendseitigen Decision Explainability Projection von PredatorAI v3 vorgeschlagen.

Die Explainability Projection wird als Application Read Model an der Grenze zwischen Domain/Application und Delivery eingeordnet. Sie hängt von kanonischen Backend-Artefakten ab, bleibt selbst jedoch eine abgeleitete, read-only Sicht und kein Domain-Ergebnis. Ihre Builder beziehungsweise Projektoren gehören zur Application-Projektionsgrenze und dürfen ausschließlich strukturelle Transformation ausführen.

Für den Vertrag gelten folgende Architekturregeln:

1. `DecisionResult` ist gemäß ADR-0001 die verpflichtende kanonische Quelle der Decision Explainability Projection.
2. Ein akzeptierter kanonischer Execution Trace gemäß ADR-0002 ist eine getrennte optionale Quelle für Ausführungstransparenz. Er wird nicht in Decision-Erklärungsfelder umgedeutet und nicht als Ersatz für `DecisionResult` verwendet.
3. Decision Explainability und Execution Explainability bleiben getrennte Projektionen beziehungsweise getrennte Abschnitte eines Delivery-Vertrags. Sie dürfen gemeinsam ausgeliefert, aber nicht zu einer mehrdeutigen Universal-Trace-Struktur verschmolzen werden.
4. `core.explainability.decision_trace.DecisionTrace` ist die bestehende kanonische Grundlage für die Decision-Erklärung. Seine spätere Weiterentwicklung muss kompatibel, versioniert und über separate Tasks erfolgen.
5. `core.decision.decision_trace.DecisionTrace` ist weder das kanonische Decision-Ergebnis noch die kanonische Explainability Projection.
6. `DecisionCard`, `DecisionCardBuilder` und `DecisionExplainer` bleiben bestehende rollen- beziehungsweise UI-nahe Projektionen. Sie dürfen eine kanonische Explainability Projection konsumieren, aber keine konkurrierende fachliche Wahrheit definieren.
7. Frontend-Entities, Pipeline-Stages, Counts und Statuswerte sind Presentation-Modelle. Das Frontend darf sie darstellen und UI-spezifisch gruppieren, aber keine fehlenden fachlichen Erklärungen erzeugen.
8. Explainability darf keine Decision, Priorität, Aktion, Confidence, Recommendation, Evidence, Reasoning-Aussage oder Execution-Event erzeugen oder verändern.
9. Eine Projektion darf ausschließlich Informationen darstellen, die in ihren kanonischen Quellen vorhanden oder eindeutig als technische Projektionsmetadaten gekennzeichnet sind.
10. Fehlende, nicht verfügbare oder nicht zugreifbare Quelldaten werden explizit als fehlend beziehungsweise nicht verfügbar dargestellt. Sie werden nicht durch plausible Texte, Default-Fakten oder abgeleitete Gewissheit ersetzt.
11. Jedes Erklärungselement muss auf seine Provenance zurückführbar sein. Provenance umfasst mindestens Quelltyp und stabile Quellreferenz; erforderliche Source- und Contract-Versionen müssen in einem späteren versionierten Vertrag korrelierbar sein.
12. Die Reihenfolge von Erklärungselementen wird deterministisch über eine eindeutige Sequenz festgelegt. UI-Sortierung darf die Anzeige verändern, aber nicht die kanonische Reihenfolge oder Bedeutung überschreiben.
13. Die Projektion muss Vollständigkeit explizit beschreibbar machen. „Keine Daten vorhanden“, „Quelle nicht verfügbar“ und „nicht Bestandteil dieser Ausführung“ dürfen nicht denselben Zustand darstellen. Die konkrete Modellierung wird nicht in diesem ADR implementiert.
14. Eine erzeugte Explainability Projection ist read-only. Nachträgliche Korrekturen erfolgen durch eine neue, versionierte Projektion aus den kanonischen Quellen und nicht durch stille Mutation.
15. Projektionsvertrag, Quellvertragsversionen und Erzeugungszeitpunkt müssen später explizit versionierbar sein. Dieser ADR definiert kein konkretes Versionsschema.
16. Metadaten unterliegen einer Allowlist und dürfen weder fachliche Aussagen verstecken noch ungeprüfte sensible Quelldaten transportieren.
17. API-Transportmodelle sind versionierte Delivery-Projektionen der kanonischen Explainability Projection.
18. Rollen- und UI-spezifische Sichten für Executive, SOC, CISO oder andere Workspaces sind nachgelagerte Presentation-Projektionen. Sie dürfen Inhalte auswählen oder gruppieren, aber nicht fachlich umdeuten.

Die Abhängigkeitsrichtung lautet:

```text
Decision Engine
      │
      ▼
DecisionResult (ADR-0001)
      │
      ▼
Decision Explainability Projection

Reasoning Orchestrator
      │
      ▼
Execution Trace (ADR-0002)
      │
      ▼
Execution Explainability Projection

Decision Explainability + Execution Explainability
      │
      ▼
versionierter Delivery-Vertrag
      │
      ▼
rollen- und UI-spezifische Presentation
```

Die beiden Explainability-Sichten teilen eine gemeinsame Governance für Provenance, Versionierung und fehlende Daten, behalten aber getrennte Quellen und Bedeutungen.

## Begründung

Die bestehende `core.explainability`-Familie ist die technisch geeignetste Grundlage:

- Sie hängt gerichtet vom akzeptierten `DecisionResult` ab.
- Sie ist von React, UI, HTTP und Persistenz unabhängig.
- Ihr Builder führt nach eigener und tatsächlicher Struktur nur Transformation aus.
- Kategorien und Sequenzen ermöglichen eine deterministische, strukturierte Erklärung.
- Die Projektion ist als frozen Dataclass angelegt und sortiert Items stabil.
- Sie stellt eine explizite Serialisierung bereit, ohne eine API zu implementieren.

Die Einordnung als Application Read Model verhindert gleichzeitig, dass ein abgeleitetes Erklärungsformat zum Domainmodell wird. Die Domain bleibt Quelle der fachlichen Wahrheit; die Application-Projektion strukturiert diese Wahrheit für nachgelagerte Verbraucher.

Eine getrennte Execution Explainability ist notwendig, weil Ausführung und fachliches Ergebnis unterschiedliche Fragen beantworten. ADR-0002 verbietet bereits die Duplikation vollständiger Domainobjekte im Execution Trace. Umgekehrt darf die Decision Explainability keine nicht vorhandenen Ausführungsereignisse erfinden.

Die aktuelle Frontend-Pipeline zeigt, dass mehrere Rollen und Darstellungsformen dieselben Informationen unterschiedlich gruppieren müssen. Eine kanonische Backend-Projektion liefert dafür überprüfbare Inhalte und Provenance, ohne konkrete UI-Struktur, Farben, Widgets oder Workspace-Status zu bestimmen.

## Konsequenzen

### Positiv

- PredatorAI erhält eine eindeutige Backend-Quelle für strukturierte Decision Explainability.
- Decision-Ergebnis, Ausführungsaudit und Erklärung bleiben klar getrennt.
- Bestehende `core.explainability`-Strukturen werden genutzt statt einer Parallelarchitektur.
- Explainability kann nicht stillschweigend fachliche Entscheidungen verändern.
- Provenance, Sequenz und explizite fehlende Daten verbessern Auditierbarkeit.
- API-, Reporting- und UI-Verbraucher können auf einen versionierten Projektionsvertrag ausgerichtet werden.
- Rollenbezogene Sichten bleiben flexibel, ohne neue fachliche Wahrheiten zu erzeugen.
- Die vorhandene Explainability-Projektion aus `DecisionResult` entspricht bereits weitgehend der Zielrichtung.

### Negativ

- Die bestehende `core.explainability.DecisionTrace` bildet aktuell nur Decision Explainability ab und enthält keinen kanonischen Execution-Trace-Anteil.
- Das bestehende Modell besitzt noch keine explizite Projection-ID, Contract-Version, Source-Version, Erzeugungszeit oder vollständige Provenance-Referenzen.
- Die frozen Dataclass garantiert keine tiefe Unveränderlichkeit, da `metadata` weiterhin ein veränderliches Dictionary ist.
- Der Builder verwendet teilweise menschenlesbare Texte und technische Source-Strings, deren Versionierung noch nicht geregelt ist.
- Vollständigkeits- und Missing-Data-Zustände sind noch nicht explizit modelliert.
- Die ältere `core.decision.DecisionTrace`-/`DecisionCard`-/`DecisionExplainer`-Familie bleibt vorerst Migration Debt.
- Frontend-Pipeline und Backend-Projektion sind aktuell nicht über einen versionierten Transportvertrag verbunden.

## Alternativen

### `core.decision.decision_trace.DecisionTrace` als kanonische Explainability Projection verwenden

Nicht vorgeschlagen.

Die Struktur bündelt Decision, AI Review, Evidence, Threat Intelligence, Business Impact, Timeline, Stories und Remediation. Sie verwendet eine andere Modellfamilie und trennt Domain-Ergebnis, Erklärung und Rollenprojektion nicht ausreichend.

### `DecisionCard` als kanonische Explainability Projection verwenden

Abgelehnt.

`DecisionCard` ist ausdrücklich UI-orientiert und enthält Farbe, Icon und Expanded State. Sein Builder erzeugt außerdem Titel aus Prioritätsstrings. Ein UI-Vertrag darf keine backendweit kanonische Explainability-Wahrheit bilden.

### `DecisionExplainer`-Texte als kanonische Erklärung verwenden

Abgelehnt.

Freitext ist schwer versionierbar, nicht zuverlässig strukturell prüfbar und auf konkrete Rollenformate zugeschnitten. Texte können als nachgelagerte Projektion aus strukturierten Explainability Items erzeugt werden.

### Frontend-`ExplainabilityPipeline` als kanonischen Vertrag übernehmen

Abgelehnt.

Die Komponente berechnet Counts und Status direkt aus Frontend-Entity-Modellen und enthält UI-Titel sowie Darstellungslogik. Ihre Übernahme würde Backend-Single-Source-of-Truth und Dependency Direction verletzen.

### DecisionResult und Execution Trace in ein einziges Explainability-Modell kopieren

Abgelehnt.

Eine vollständige Kopie erzeugt Datenverdopplung, Versionsdrift und unklare Verantwortlichkeiten. Getrennte Projektionen können über stabile Referenzen und einen Delivery-Vertrag gemeinsam ausgeliefert werden.

### Explainability dynamisch nur im Frontend erzeugen

Abgelehnt.

Dies würde fachliche Erklärung, Provenance und Vollständigkeitsbewertung in die Presentation-Schicht verlagern und zu unterschiedlichen Erklärungen je Client führen.

### Ein vollständig neues Explainability-Modell parallel einführen

Nicht vorgeschlagen.

Die bestehende `core.explainability`-Familie erfüllt die Kernrichtung bereits. Notwendige Erweiterungen sollen kontrolliert und kompatibel erfolgen, nicht über eine zweite Modellfamilie.

### Vorläufig keinen kanonischen Explainability-Vertrag festlegen

Nicht vorgeschlagen.

Ohne explizite Grenze könnten ADR-0001 und ADR-0002 in UI- oder API-Schichten unterschiedlich interpretiert werden. Die Projektionsrichtung muss vor weiteren Reasoning-Intelligence-Implementierungen feststehen.

## Abgrenzung

Dieser ADR:

- verändert kein Explainability-Modell,
- verändert keinen Builder,
- verändert keine Decision- oder Execution-Trace-Struktur,
- implementiert keine neue Projektion,
- implementiert keine API oder Serialisierungsversion,
- implementiert keine UI oder Workspace-Änderung,
- implementiert keine Reasoning Session,
- implementiert keine Persistenz,
- konsolidiert oder benennt keine `DecisionTrace`-Klasse um,
- verändert keine Decision-, Risk-, Confidence-, Reasoning- oder Recommendation-Logik,
- definiert keine rollenbezogenen Texte oder Widgets,
- und entscheidet keine konkrete Migration oder Deprecation.

Konkrete Felder für Projection-ID, Provenance, Versionsinformationen, Vollständigkeit und Missing-Data-Zustände benötigen separat freigegebene Contract- und Implementierungs-Tasks.

## Migration

Dieser ADR implementiert keine Migration.

Nach einer Annahme soll die Weiterentwicklung ausschließlich über kleine, separat freigegebene AIDP-Tasks erfolgen:

1. Produzenten und Verbraucher beider Backend-`DecisionTrace`-Familien sowie der Frontend-Explainability-Sichten vollständig inventarisieren.
2. Die bestehende `core.explainability.DecisionTrace`-Struktur gegen die akzeptierten Anforderungen an Provenance, Versionierung, Vollständigkeit und Missing Data prüfen.
3. Einen kompatiblen, versionierten Delivery-Vertrag separat entscheiden.
4. Projektions- und Contract-Tests vor jeder Modelländerung einführen.
5. Bestehende API-, Reporting- und UI-Verbraucher einzeln gegen den Delivery-Vertrag prüfen.
6. Rollenprojektionen als nachgelagerte Views einführen oder anpassen, ohne fachliche Inhalte umzudeuten.
7. Erst nach erfolgreicher Verbraucher-Migration über Umbenennung, Deprecation oder Entfernung älterer Strukturen entscheiden.

Eine Big-Bang-Migration und eine parallele zweite Explainability-Pipeline sind ausgeschlossen.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität

- Contract-Tests müssen später nachweisen, dass Projektionen keine fachlichen Werte verändern oder erfinden.
- Golden- beziehungsweise Snapshot-Tests können stabile Kategorien, Sequenzen und Transportverträge absichern, dürfen aber semantische Assertions nicht ersetzen.
- Tests müssen vollständige, teilweise vorhandene und fehlende Quelldaten unterscheiden.
- Deterministische Projektion aus identischen Quellen muss identische strukturierte Inhalte erzeugen, abgesehen von expliziten Erzeugungsmetadaten.
- Die Python-Testgrundlage muss vor produktiven Vertragsänderungen eingerichtet sein.

### Security

- Explainability darf keine Secrets, Credentials, ungefilterten Stack Traces oder internen Payloads aus Evidence, Metadata oder Execution Events exponieren.
- Projektionsmetadaten und Quellen benötigen Allowlisting und Datenminimierung.
- Rollenbasierte Sichten dürfen Inhalte nur reduzieren, nicht Zugriffskontrolle durch bloßes Ausblenden in der UI ersetzen.
- Sensitive Evidence und Auditdaten benötigen serverseitige Autorisierung vor jeder Delivery-Projektion.
- Fehlende Berechtigung muss von fehlenden Quelldaten unterscheidbar sein, ohne sensible Existenzinformationen unzulässig offenzulegen.

### Auditierbarkeit

- Jedes Erklärungselement muss zu kanonischen Quellen zurückverfolgbar sein.
- Kanonische Source- und Projection-Versionen müssen später korrelierbar sein.
- Reihenfolge und Missing-Data-Zustände dürfen nicht stillschweigend durch Presentation-Komponenten verändert werden.
- Explainability ersetzt weder `DecisionResult` noch den Execution Trace als Auditquelle.

### Performance

- Strukturierte Projektionen können für mehrere Rollen wiederverwendet werden und vermeiden parallele fachliche Berechnungen.
- Große Evidence-, Metadata- oder Eventmengen können Projektions- und Serialisierungskosten erzeugen.
- Pagination, Lazy Loading, Caching und Materialisierung werden nicht in diesem ADR entschieden.
- Caching darf Provenance, Source-Version und Autorisierung nicht entkoppeln.

### Kompatibilität

- Dieser Dokumentationstask verursacht keine Breaking Changes.
- Die bestehende `core.explainability.DecisionTrace` bleibt unverändert verfügbar.
- Ein späterer versionierter Delivery-Vertrag muss additive und breaking Änderungen explizit unterscheiden.
- Frontend-Darstellungen müssen nicht strukturgleich mit dem Backend-Projektionsmodell sein.
- Bestehende ältere `DecisionTrace`, `DecisionCard` und `DecisionExplainer` bleiben bis zu separat freigegebenen Migrationen verfügbar.

## Referenzen

- AIDP TASK-0006 – Architecture Charter
- AIDP TASK-0007 – ADR Convention
- AIDP TASK-0008 – Canonical Decision Contract
- AIDP TASK-0009 – Execution Trace Contract
- AIDP TASK-0010 – Explainability Projection Contract
- ADR-0001 – DecisionResult as Canonical Decision Contract (`ACCEPTED`)
- ADR-0002 – Canonical Execution Trace Contract (`ACCEPTED`)
- `AGENTS.md`
- `ARCHITECTURE.md`
- `.ai/decisions/README.md`
- `core/explainability/__init__.py`
- `core/explainability/explanation_item.py`
- `core/explainability/decision_trace.py`
- `core/explainability/decision_trace_builder.py`
- `core/decision/decision_trace.py`
- `core/decision/decision_card.py`
- `core/decision/decision_card_builder.py`
- `core/decision/decision_explainer.py`
- `frontend/src/components/reasoning/ExplainabilityPipeline.tsx`
- `frontend/src/components/reasoning/ExecutionTrace.tsx`
- `frontend/src/workspaces/soc/explainability/ExplainabilityOverview.tsx`
- `frontend/src/workspaces/soc/explainability/ExplainabilityWorkspace.tsx`

## Architektur-Review

Status:
APPROVED

Bemerkungen:
ADR-0003 definiert Explainability konsistent als abgeleitete read-only Projektion und grenzt sie sauber von `DecisionResult` und Execution Trace ab. `DecisionResult` bleibt die kanonische fachliche Quelle, Execution Trace ein separates Application-/Audit-Artefakt und Explainability ein Application Read Model. API-, Rollen- und UI-Darstellungen bleiben nachgelagerte Projektionen. Die Architektur verhindert bewusst ein Universal-Trace-Modell. Die dokumentierten offenen Risiken betreffen zukünftige Architekturentscheidungen und blockieren die Freigabe nicht.

Freigabe:
Architect
