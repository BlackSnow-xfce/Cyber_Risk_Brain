# ADR-0002 – Canonical Execution Trace Contract

## Status

ACCEPTED

## Datum

2026-08-04

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI benötigt für den Reasoning Intelligence Layer eine nachvollziehbare Aufzeichnung darüber, welche Verarbeitungsschritte während einer einzelnen Reasoning-Ausführung tatsächlich stattgefunden haben. Diese Aufzeichnung soll künftig Audit, Diagnose, Replay-Vorbereitung und Explainability unterstützen, ohne selbst fachliche Entscheidungen zu treffen.

Der aktuelle Bestand enthält mehrere Strukturen mit dem Begriff „Trace“, aber noch keinen kanonischen Backend-Execution-Trace:

- `core/decision/decision_trace.py` enthält eine veränderliche, aggregierte Decision-Struktur mit Decision-, AI-Review-, Evidence-, Business-, Timeline- und Story-Daten. Sie beschreibt ein umfangreiches Ergebnisbild, nicht die chronologische Ausführung.
- `core/decision/decision_trace_builder.py` baut diese Struktur aus `DecisionContext`, `ReasoningResult` und mehreren Buildern auf und verändert währenddessen den Context. Der Builder zeichnet keine einzelnen Ausführungsschritte mit stabiler Identität und Reihenfolge auf.
- `core/explainability/decision_trace.py` ist eine unveränderliche, strukturierte Explainability-Repräsentation von `DecisionResult`.
- `core/explainability/decision_trace_builder.py` projiziert das akzeptierte kanonische `DecisionResult` strukturell in Explainability Items. Er beobachtet keine Engine-Ausführung.
- `core/predator_engine.py` orchestriert bereits mehrere aufeinanderfolgende Stufen wie Connector Loading, Mapping, Graph Building, Risk Analysis, Decisions, Reasoning, Stories und Reports. Der Ablauf wird jedoch nicht als eigener, korrelierter Auditvertrag erfasst.

Im Frontend existieren bereits präsentationsnahe Execution-Trace-Typen:

- `ExecutionTraceEntry` enthält Ausführungszeit, Reihenfolge, Rule-Namen, Match-Status, optionale Skip-Begründung, Dauer und Referenzen auf generierte Artefakte.
- `ExecutionTraceResult` gruppiert diese Einträge.
- `RuleResult` erweitert einen Trace-Eintrag zusätzlich um IDs und vollständige generierte Inference-, Reasoning-, Decision- und Recommendation-Objekte.

Diese Frontend-Typen zeigen sinnvolle Informationsbedürfnisse der UI, können aber nicht die fachliche Backend-Single-Source-of-Truth bilden. Insbesondere vermischt `RuleResult` das Ergebnis einer Rule-Auswertung mit einer Presentation-Trace-Struktur und hält neben Referenzen auch vollständige Artefaktobjekte.

ADR-0001 legt `core.decision.models.DecisionResult` als kanonisches fachliches Decision-Ergebnis fest. Ein Execution Trace darf diese Entscheidung nicht duplizieren oder ersetzen.

Ohne expliziten Execution-Trace-Vertrag bestehen folgende Risiken:

- bestehende Decision- oder Explainability-Traces werden fälschlich als Ausführungsprotokoll verwendet,
- Backend und Frontend entwickeln konkurrierende Trace-Wahrheiten,
- technische Logs werden mit einem fachlich korrelierten Audit Trail verwechselt,
- vollständige Domainobjekte werden mehrfach in Trace-Einträgen gespeichert,
- Reihenfolge, Zeitangaben und Fehlerpfade bleiben uneindeutig,
- und eine künftige Reasoning Session erhält keine klare Audit-Grenze.

## Entscheidung

PredatorAI erhält einen einzigen kanonischen Backend-Execution-Trace als Application-/Audit-Artefakt einer vollständigen Reasoning-Ausführung.

Der Execution Trace gehört zur Application-Schicht, weil er die koordinierte Ausführung mehrerer Domain- und Infrastrukturkomponenten beschreibt. Er ist kein fachliches Decision-Domainmodell und keine UI-Projektion. Seine Erzeugung wird künftig durch den Reasoning-Orchestrator beziehungsweise die kontrollierte Application-Ausführungsgrenze verantwortet.

Für den Vertrag gelten folgende Architekturregeln:

1. Genau eine Reasoning-Ausführung besitzt genau einen kanonischen Execution Trace.
2. Der Trace wird über eine stabile `trace_id` identifiziert und muss mit der stabilen ID der zugehörigen künftigen Reasoning Session korrelierbar sein.
3. Die Reasoning Session beschreibt Lifecycle und Ausführungskontext; der Execution Trace beschreibt die während dieser Ausführung beobachteten Schritte. Dieser ADR definiert kein Session-Modell.
4. Der Trace besteht aus geordneten, typisierten Execution Events. Jedes Event besitzt eine stabile Identität und eine innerhalb des Trace eindeutige Ausführungsreihenfolge.
5. Die logische Reihenfolge wird durch eine monotone Sequenz festgelegt. Zeitstempel dokumentieren den Zeitpunkt, sind aber wegen möglicher gleicher Werte oder Clock-Abweichungen nicht die alleinige Sortiergrundlage.
6. Zeitangaben werden in UTC mit eindeutigem Offset und maschinenlesbarer Präzision erfasst. Dauern werden getrennt von Wall-Clock-Zeit als nicht negative Messwerte behandelt.
7. Ein Event beschreibt ausschließlich einen beobachteten Ausführungsschritt, dessen Ergebnisstatus und referenzierte erzeugte Artefakte. Es enthält keine neue Decision-, Recommendation- oder Reasoning-Logik.
8. Erzeugte fachliche Artefakte werden durch Typ und stabile ID referenziert. Vollständige `DecisionResult`-, Inference-, Reasoning- oder Recommendation-Objekte werden nicht in Events dupliziert.
9. `DecisionResult` bleibt gemäß ADR-0001 die kanonische fachliche Decision-Single-Source-of-Truth. Der Trace darf lediglich dokumentieren, dass ein entsprechendes Artefakt erzeugt wurde.
10. Events werden während einer laufenden Ausführung ausschließlich angehängt. Bereits erfasste Events werden fachlich nicht überschrieben oder entfernt.
11. Nach einem terminalen Abschluss wird der Trace unveränderlich. Terminale Ergebnisse unterscheiden mindestens erfolgreiche und fehlgeschlagene Ausführungen, ohne den Session-Status in diesem ADR zu modellieren.
12. Fehler werden als kontrollierte Events mit sicherer Fehlerklassifikation und bereinigter Beschreibung erfasst. Stack Traces, Secrets oder unkontrollierte Payloads gehören nicht in den kanonischen Auditvertrag.
13. Metadaten sind versioniert, allowlist-basiert und auf den Ausführungskontext begrenzt. Sie dürfen nicht zur untypisierten Ablage fachlicher Ergebnisse werden.
14. Technisches Logging darf auf `trace_id` und Session-ID korrelieren, bleibt aber eine getrennte operative Datenquelle.
15. Frontend-Trace-Modelle werden aus einem versionierten Transportvertrag projiziert. Sie sind keine Quelle für Backend-Ausführungswahrheit.

Die Abhängigkeitsrichtung lautet:

```text
Reasoning Orchestrator / Application Boundary
                 │
                 ├──→ Reasoning Session Lifecycle (künftig)
                 │
                 ├──→ Canonical Execution Trace
                 │       └──→ Artefakt-Referenzen
                 │
                 └──→ Domain Engines
                         └──→ DecisionResult

Canonical Execution Trace
        ├──→ versionierte API-/Audit-Projektion
        ├──→ Explainability-Eingabe, soweit separat freigegeben
        └──→ Frontend-Execution-Trace-Projektion
```

Die genaue Explainability-Projektion wird nicht in diesem ADR entschieden und bleibt Gegenstand von ADR-0003.

## Begründung

Ein Execution Trace beschreibt einen Anwendungsablauf über mehrere fachliche und technische Schritte hinweg. Damit ist er nicht Teil einer einzelnen Decision-Domainentität, sondern ein Artefakt der Application-Orchestrierung.

Diese Einordnung bietet folgende Vorteile:

- Domain Engines bleiben unabhängig von Audit-, UI- und Persistenzanforderungen.
- Der künftige Orchestrator kann die tatsächliche Reihenfolge und Fehlerpfade an einer kontrollierten Ausführungsgrenze erfassen.
- `DecisionResult` wird nicht zu einem technischen Prozesscontainer erweitert.
- Explainability kann fachliches Ergebnis und Ausführungsnachweis getrennt projizieren.
- Frontend-Modelle können ihren UI-Bedarf erfüllen, ohne die Backend-Verantwortung zu übernehmen.
- Ein append-only Ereignisstrom ermöglicht Auditierbarkeit, ohne alte Events stillschweigend umzudeuten.

Die vorhandenen Backend-`DecisionTrace`-Klassen sind nicht als Execution Trace geeignet:

- Die Decision-Variante bündelt Ergebnis- und Darstellungsdaten, besitzt aber weder Eventidentität noch eine allgemeine Ausführungsreihenfolge.
- Die Explainability-Variante ist eine abgeleitete Sicht auf `DecisionResult` und beschreibt fachliche Erklärungselemente statt ausgeführter Verarbeitungsschritte.

Die vorhandenen Frontend-Typen liefern wertvolle Anforderungen an die spätere Projektion, liegen jedoch in der Presentation-Schicht. Ihre direkte Wiederverwendung im Backend würde die Dependency Direction umkehren und das Backend als Single Source of Truth verletzen.

## Konsequenzen

### Positiv

- PredatorAI erhält eine eindeutige Trennung zwischen fachlichem Ergebnis und Ausführungsnachweis.
- Eine Reasoning-Ausführung kann vollständig über eine stabile Trace- und Session-Korrelation nachvollzogen werden.
- Chronologie und Reihenfolge sind auch bei identischen oder ungenauen Zeitstempeln deterministisch.
- Erfolgs-, Skip- und Fehlerpfade können einheitlich auditiert werden.
- Fachliche Artefakte werden referenziert statt dupliziert.
- Backend und Frontend erhalten eine klare Source-of-Truth- und Projektionsbeziehung.
- Technische Logs können angereichert werden, ohne den Auditvertrag zu ersetzen.
- Replay, Historie und Explainability werden vorbereitet, aber nicht vorzeitig implementiert.

### Negativ

- Ein zusätzlicher Application-Vertrag erhöht Modell- und Testaufwand.
- Append-only Semantik und Unveränderlichkeit erfordern später eine bewusst gestaltete Schreib- und Persistenzstrategie.
- Artefakt-Referenzen benötigen stabile IDs; diese sind im bestehenden Bestand nicht für alle Ergebnisse durchgängig garantiert.
- Die Beziehung zu einer Reasoning Session bleibt bis zu einer separaten Entscheidung teilweise abstrakt.
- Frontend-`RuleResult` und der künftige Backend-Trace werden voraussichtlich nicht strukturgleich sein.
- Aufbewahrung, Löschung und Zugriffskontrolle erhöhen den betrieblichen Governance-Aufwand.
- Hochgranulare Events können Volumen- und Performancekosten verursachen.

## Alternativen

### `core.decision.decision_trace.DecisionTrace` als Execution Trace verwenden

Nicht vorgeschlagen.

Die Klasse beschreibt ein aggregiertes Decision-, Review- und Story-Ergebnis. Sie besitzt keine generische Eventsequenz und kopiert zahlreiche fachliche Inhalte. Ihre Nutzung als Execution Trace würde Decision-Ergebnis und Ausführung weiter vermischen.

### `core.explainability.decision_trace.DecisionTrace` als Execution Trace verwenden

Nicht vorgeschlagen.

Die Klasse ist eine aus `DecisionResult` erzeugte Explainability-Projektion. Ihre geordneten Items beschreiben Erklärungskategorien, nicht den tatsächlichen zeitlichen Ablauf der Engine.

### Frontend-`ExecutionTraceResult` als kanonischen Vertrag übernehmen

Abgelehnt.

Das Frontend ist nicht die fachliche Single Source of Truth. Der Typ ist auf Rule-Darstellung zugeschnitten, besitzt keine eigene Trace- oder Session-Identität und definiert keinen vollständigen Lifecycle. `RuleResult` dupliziert zusätzlich vollständige generierte Domainobjekte.

### Ausschließlich technisches Logging verwenden

Abgelehnt.

Logs sind für Betrieb und Diagnose optimiert, häufig unstrukturiert oder installationsabhängig und unterliegen anderen Retention-, Sampling- und Zugriffskonzepten. Sie garantieren weder einen vollständigen fachlich korrelierten Ablauf noch stabile Artefakt-Referenzen.

### Execution Trace in `DecisionResult` einbetten

Abgelehnt.

Dies würde den kanonischen fachlichen Decision-Vertrag mit Application-Lifecycle und Auditdaten koppeln. Ein Decision-Ergebnis kann konsumiert werden, ohne den gesamten technischen Ausführungsverlauf zu laden.

### Vollständige Domainobjekte in jedem Event speichern

Abgelehnt.

Dies erzeugt Datenverdopplung, Versionsdrift, erhöhte Speicher- und Serialisierungskosten und konkurrierende Wahrheiten. Der Trace referenziert erzeugte Artefakte stattdessen über stabile IDs.

### Vorläufig keinen kanonischen Execution Trace definieren

Nicht vorgeschlagen.

Ohne Vertrag würden Reasoning Session, Audit und Explainability auf uneindeutigen Trace-Begriffen aufbauen. Die Architekturgrenze muss vor einer Implementierung geklärt sein.

## Abgrenzung

Dieser ADR:

- erstellt kein Execution-Trace-Modell,
- erstellt keine Execution Events,
- erstellt keine Reasoning Session,
- implementiert keinen Orchestrator,
- implementiert keine Persistenz oder Aufbewahrungslogik,
- implementiert kein Replay,
- verändert keine Rule Engine,
- verändert keine Decision- oder Explainability-Logik,
- ändert keine API,
- ändert keine Frontend-Typen oder UI,
- benennt keine bestehende `DecisionTrace`-Klasse um,
- konsolidiert keine bestehenden Builder,
- und definiert nicht die konkrete Explainability-Darstellung.

Eventtypen, konkrete Felder, Persistenzschema, API-Version und Session-Modell werden erst in separat freigegebenen Architektur- beziehungsweise Implementierungs-Tasks festgelegt.

## Migration

Dieser ADR implementiert keine Migration.

Nach einer Annahme soll die Einführung ausschließlich über kleine, separat freigegebene AIDP-Tasks erfolgen:

1. Bestehende Backend- und Frontend-Trace-Produzenten und -Verbraucher vollständig inventarisieren.
2. Den Reasoning-Session- und Orchestrator-Vertrag separat entscheiden.
3. Ein minimales, frameworkunabhängiges Execution-Trace- und Event-Contract entwerfen.
4. Lifecycle-, Chronologie- und Unveränderlichkeitsinvarianten mit Unit Tests absichern.
5. Den Trace an genau einem freigegebenen Application-Composition-Root erzeugen.
6. Eine versionierte Transportprojektion definieren.
7. Frontend-Verbraucher erst danach gegen die Projektion prüfen.
8. Persistenz und Retention separat entscheiden, bevor produktive Audit-Versprechen abgegeben werden.

Bestehende `DecisionTrace`-Strukturen bleiben während dieser Schritte unverändert. Eine spätere Umbenennung, Deprecation oder Konsolidierung benötigt einen eigenen Task und eine Kompatibilitätsprüfung.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität

- Contract-Tests müssen später Identität, eindeutige Sequenzen, Reihenfolge, terminalen Lifecycle und unveränderliche abgeschlossene Traces prüfen.
- Fehler- und Skip-Pfade müssen ebenso testbar sein wie erfolgreiche Ausführungen.
- Tests müssen sicherstellen, dass fachliche Artefakte nur referenziert und nicht dupliziert werden.
- Die Python-Testgrundlage muss vor der produktiven Trace-Implementierung eingerichtet sein.

### Security

- Trace-Metadaten verwenden eine explizite Allowlist und dürfen keine Secrets, Tokens, Credentials oder ungefilterten externen Payloads enthalten.
- Fehlerbeschreibungen müssen interne Stack Traces und sensible Systemdetails standardmäßig ausblenden.
- Zugriff auf Audit-Traces muss rollenbasiert und vom Zugriff auf technische Logs getrennt werden können.
- Mandanten- und Entity-Kontext dürfen nicht über unkontrollierte Metadaten vermischt werden.
- Export und API-Projektion benötigen Datenminimierung und explizite Feldfreigaben.

### Auditierbarkeit

- Stabile Trace-, Session-, Event- und Artefakt-IDs ermöglichen Korrelation.
- Append-only Semantik verhindert unbemerkte fachliche Umschreibung bereits erfasster Ereignisse.
- Sequenz und UTC-Zeitstempel ermöglichen chronologische Rekonstruktion.
- Engine-, Rule-Pack-, Knowledge- und Contract-Versionen sollen später auf Session- oder Trace-Ebene korrelierbar sein; ihre konkrete Modellierung ist nicht Teil dieses ADRs.
- Manipulationsschutz und kryptografische Integritätsnachweise werden nicht vorweggenommen und benötigen bei regulatorischem Bedarf eine eigene Entscheidung.

### Performance

- Eventgranularität muss ausreichend für Audit sein, darf aber keine internen Schleifen oder redundanten Payloads ungefiltert protokollieren.
- Artefakt-Referenzen reduzieren Speicher- und Serialisierungskosten gegenüber vollständigen Objektkopien.
- Trace-Erfassung darf die fachliche Ausführung nicht semantisch verändern.
- Batching, asynchrones Schreiben und Sampling sind nicht Bestandteil dieses ADRs; Sampling darf einen als vollständig deklarierten Audit-Trace später nicht unbemerkt unvollständig machen.

### Aufbewahrung und Datenschutz

- Aufbewahrungsdauer, Löschkonzept, Legal Hold und Mandantentrennung benötigen vor einer Persistenzimplementierung eine eigene freigegebene Policy.
- Trace und technische Logs dürfen unterschiedliche Retention besitzen.
- Referenzierte Artefakte können früher oder später gelöscht werden als der Trace; der Umgang mit verwaisten Referenzen muss vor Persistenz geklärt werden.
- Personenbezogene oder sensible Security-Daten sind zu minimieren.

### Kompatibilität

- Dieser Dokumentationstask verursacht keine Breaking Changes.
- Ein späterer Backend-Vertrag benötigt explizite Versionierung.
- Frontend-`ExecutionTraceEntry` kann als Presentation-Projektion weiterbestehen, muss aber nicht strukturgleich mit dem Backend-Vertrag sein.
- Bestehende `DecisionTrace`-Klassen bleiben bis zu separat freigegebenen Änderungen kompatibel verfügbar.

## Referenzen

- AIDP TASK-0006 – Architecture Charter
- AIDP TASK-0007 – ADR Convention
- AIDP TASK-0008 – Canonical Decision Contract
- AIDP TASK-0009 – Execution Trace Contract
- ADR-0001 – DecisionResult as Canonical Decision Contract (`ACCEPTED`)
- `AGENTS.md`
- `ARCHITECTURE.md`
- `.ai/decisions/README.md`
- `core/decision/decision_trace.py`
- `core/decision/decision_trace_builder.py`
- `core/explainability/decision_trace.py`
- `core/explainability/decision_trace_builder.py`
- `core/predator_engine.py`
- `frontend/src/engine/ExecutionTraceEntry.ts`
- `frontend/src/engine/ExecutionTraceResult.ts`
- `frontend/src/engine/RuleResult.ts`
- Geplant: ADR-0003 – Explainability Projection

## Architektur-Review

Status:
APPROVED

Bemerkungen:
Der Execution Trace ist konsistent als Application-/Audit-Artefakt abgegrenzt und respektiert ADR-0001 sowie die Dependency Rules der Architecture Charter. Append-only-Erfassung während der Ausführung, Unveränderlichkeit nach terminalem Abschluss, monotone Sequenzen, UTC-Zeitangaben und reine Artefakt-Referenzen schaffen eine belastbare Audit-Grundlage. Logging, Explainability und Frontend-Projektionen bleiben getrennte Verantwortlichkeiten. Die offenen Fragen zu stabilen IDs, Session-Vertrag, Persistenz, Retention und Eventgranularität sind nicht blockierend und benötigen separate Folgetasks.

Freigabe:
Architect
