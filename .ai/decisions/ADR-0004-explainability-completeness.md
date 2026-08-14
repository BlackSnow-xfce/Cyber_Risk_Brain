# ADR-0004 – Explainability Completeness Contract

## Status

ACCEPTED

## Datum

2026-08-04

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

ADR-0001 legt `DecisionResult` als einziges kanonisches fachliches Ergebnis einer abgeschlossenen Decision fest. ADR-0002 trennt den technischen Ausführungsverlauf ausdrücklich vom fachlichen Ergebnis. ADR-0003 definiert `core.explainability.DecisionTrace` als Grundlage der kanonischen Decision Explainability Projection und verlangt, dass fehlende Informationen weder erzeugt noch plausibilisiert werden.

Die bestehende Projektion bildet vorhandene Decision-Daten deterministisch als `ExplanationItem`-Elemente ab. Nicht vorhandene optionale Felder erzeugen kein Item. Dieses Verhalten verhindert erfundene Aussagen, unterscheidet jedoch nicht, warum eine erwartbare Erklärung fehlt. Insbesondere sind folgende Situationen derzeit strukturell nicht auseinanderzuhalten:

- Daten sind vorhanden und wurden projiziert.
- Die Quelle wurde ausgewertet und enthält keine Daten.
- Die Quelle war nicht verfügbar oder nicht zugreifbar.
- Die Quelle beziehungsweise der Erklärungsschritt war nicht Bestandteil der Ausführung.
- Die vorhandenen kanonischen Quellen reichen nicht aus, um einen dieser Zustände sicher zu bestimmen.

Ein fehlendes `ExplanationItem` allein kann diese Zustände nicht ausdrücken. Eine UI, API oder Reporting-Komponente müsste die Bedeutung erraten und könnte dadurch eine konkurrierende fachliche oder technische Wahrheit erzeugen. Ein pauschales `complete: true|false` würde die fachlich und operativ unterschiedlichen Ursachen ebenfalls zusammenführen.

TASK-0015 hat Projektions- und Quellvertragsversionen sowie einen Erzeugungszeitpunkt ergänzt. TASK-0016 hat strukturierte Provenance aus Quelltyp und stabiler Quellreferenz eingeführt. Diese technischen Metadaten schaffen die Grundlage für einen versionierbaren Completeness Contract, entscheiden dessen Semantik aber nicht.

ADR-0003 verlangt eine separat freigegebene Entscheidung für diese Modellierung. Dieser ADR beschreibt ausschließlich den Vertrag. Er implementiert keine Felder, Enums, Builder-Logik, Serialisierung oder Consumer-Migration.

## Entscheidung

Die kanonische Decision Explainability Projection soll eine additive, projektionsweite Completeness-Beschreibung erhalten. Completeness ist technische Projektionssemantik und weder Bestandteil von `DecisionResult` noch eine fachliche Bewertung.

### Kanonische Zustände

Der Completeness Contract verwendet eine geschlossene, versionierte Zustandsmenge mit mindestens folgenden Zuständen:

| Zustand | Bedeutung | Zulässige Ableitung |
|---|---|---|
| `AVAILABLE` | Die kanonische Quelle enthält verwendbare Daten, die in der Explainability Projection repräsentiert werden. | Ausschließlich aus tatsächlich vorhandenen und projizierten Quelldaten. |
| `NO_DATA` | Die kanonische Quelle beziehungsweise ein vertraglich definierter Quellbereich wurde erfolgreich ausgewertet und enthält explizit keine Daten. | Nur wenn der Quellvertrag Leere eindeutig als geprüftes „keine Daten“ definiert. |
| `SOURCE_UNAVAILABLE` | Der vertraglich definierte Quellbereich konnte nicht gelesen oder ausgewertet werden. | Nur aus einem expliziten, autorisierten technischen Verfügbarkeitszustand; niemals aus `None`, einer leeren Liste oder einem fehlenden Item erraten. |
| `NOT_PART_OF_EXECUTION` | Der Quellbereich war für diese Ausführung vertraglich nicht vorgesehen beziehungsweise nicht Bestandteil des ausgeführten Pfads. | Nur aus einem expliziten kanonischen Ausführungs- oder Quellstatus; niemals aus bloßer Abwesenheit abgeleitet. |
| `UNKNOWN` | Die kanonischen Quellen reichen nicht aus, um einen der anderen Zustände sicher festzustellen. | Verbindlicher sicherer Fallback, wenn keine eindeutige Ableitungsregel greift. |

`UNKNOWN` ist erforderlich, damit die Projektion weder `NO_DATA`, `SOURCE_UNAVAILABLE` noch `NOT_PART_OF_EXECUTION` plausibilisiert. Der Zustand darf nicht durch eine UI in einen vermeintlich konkreteren Zustand umgedeutet werden.

### Ebene der Completeness-Beschreibung

Completeness wird auf Ebene der bestehenden `DecisionTrace`-Projektion als geordnete Sammlung technischer Completeness-Einträge beschrieben. Es entsteht keine zweite Projektion und keine parallele Modellfamilie.

Ein Completeness-Eintrag beschreibt konzeptionell:

- einen stabilen, versionierten Quellbereich beziehungsweise eine Quellreferenz,
- genau einen kanonischen Completeness-Zustand,
- die Provenance des Zustands,
- und optional einen allowlist-basierten technischen Reason Code, sofern die kanonische Quelle diesen explizit bereitstellt.

Ein Completeness-Eintrag enthält keine fachlichen Werte, keine kopierten Source-Payloads, keine generierten Erklärungstexte und keine frei formulierte Begründung.

Die projektionsweite Ebene ist erforderlich, weil `NO_DATA`, `SOURCE_UNAVAILABLE`, `NOT_PART_OF_EXECUTION` und `UNKNOWN` gerade dann relevant sind, wenn kein `ExplanationItem` existiert. Vorhandene Items behalten ihre bestehende Provenance. Ein `AVAILABLE`-Eintrag darf auf die zugehörige stabile Quellreferenz und damit indirekt auf vorhandene Items korrelierbar sein, ohne deren Inhalte zu duplizieren.

### Versionierte Quellbereiche

Die Menge der bewerteten Quellbereiche ist Teil des versionierten Explainability-Projektionsvertrags. Sie wird als geschlossene Allowlist stabiler Referenzen definiert und nicht dynamisch aus UI-Anforderungen, freien Metadata-Keys oder zufällig vorhandenen Feldern erzeugt.

Ein späterer Implementierungstask muss für jeden freigegebenen Quellbereich eine eindeutige Ableitungsregel festlegen. Eine Regel darf ausschließlich:

1. vorhandene kanonische Decision-Daten,
2. explizite technische Zustände einer akzeptierten kanonischen Quelle,
3. bestehende Source-Version und Provenance,

verwenden.

Existiert keine eindeutige Regel, ist `UNKNOWN` auszugeben. Ein leerer Container oder `None` darf nur dann `NO_DATA` bedeuten, wenn der jeweilige Quellvertrag diese Semantik ausdrücklich garantiert.

### Determinismus und Reihenfolge

Für identische kanonische Quellen und identische Vertragsversionen müssen dieselben Completeness-Einträge mit denselben Zuständen, Referenzen und Reason Codes in derselben Reihenfolge entstehen. Der technische Erzeugungszeitpunkt bleibt gemäß ADR-0003 und der bestehenden Versionierungsmetadaten eine explizite Ausnahme vom inhaltlichen Determinismus.

Die Reihenfolge folgt einer versionierten, geschlossenen Quellbereichsreihenfolge. Alphabetische Sortierung, Dictionary-Reihenfolge oder UI-Sortierung dürfen die kanonische Reihenfolge nicht definieren.

### Read-only und Korrekturen

Completeness-Einträge sind read-only. Sie dürfen nach Erzeugung nicht still mutiert werden. Ändert sich eine kanonische Quelle oder wird zuvor fehlende Verfügbarkeit hergestellt, entsteht eine neue Projektion mit neuem Erzeugungszeitpunkt. `DecisionResult` und bestehende Explainability Items werden dadurch nicht verändert.

### Serialisierungsgrenze

Eine spätere strukturierte Serialisierung muss Completeness additiv auf Projection-Ebene ausgeben. Feldnamen, Enum-Repräsentation, Reason-Code-Allowlist und Contract-Version werden in einem separaten Implementierungstask konkretisiert und getestet.

Die Serialisierung darf:

- keine Source-Payloads kopieren,
- keine freien internen Fehlermeldungen oder Stack Traces exponieren,
- keine Autorisierungsdetails offenlegen, die sensible Existenzinformationen verraten,
- und keine fehlenden Zustände durch Default-Texte ersetzen.

### Beziehung zu Decision und Execution Explainability

Dieser Vertrag gilt für die Decision Explainability Projection aus `DecisionResult`. Execution Explainability bleibt gemäß ADR-0002 und ADR-0003 eine getrennte Projektion mit eigener kanonischer Quelle. `NOT_PART_OF_EXECUTION` darf in Decision Explainability nur verwendet werden, wenn ein akzeptierter kanonischer Ausführungs- oder Quellstatus diese Aussage explizit trägt. Die Decision Projection darf keine Execution Events oder Ausführungsschritte erfinden.

Ein späterer gemeinsamer Delivery-Vertrag darf Completeness-Zustände beider Projektionen gemeinsam transportieren, muss ihre Quellen und Bedeutungen jedoch getrennt halten.

## Begründung

Eine geschlossene Zustandsmenge verhindert, dass Backend-, API- und UI-Verbraucher fehlende Informationen unterschiedlich interpretieren. Die projektionsweite Modellierung löst das strukturelle Problem, dass für fehlende Aussagen kein `ExplanationItem` existiert. Stabile Quellreferenzen nutzen die bereits eingeführte Provenance, ohne fachliche Daten zu kopieren.

Der zusätzliche Zustand `UNKNOWN` ist sicherheits- und qualitätsrelevant. Ohne ihn müsste die Projektion bei unzureichender Evidenz einen konkreten Zustand vortäuschen. Das würde dem Verbot aus ADR-0003 widersprechen, fehlende Fakten zu plausibilisieren.

Eine geschlossene, versionierte Allowlist von Quellbereichen stellt Determinismus und Kompatibilität sicher. Sie verhindert zugleich, dass freie Metadata-Keys oder Presentation-Anforderungen den kanonischen Backend-Vertrag unkontrolliert erweitern.

Die Einordnung als technische Projektionssemantik schützt `DecisionResult` als fachliche Single Source of Truth. Completeness beschreibt ausschließlich, ob und warum eine Explainability-Projektion einen definierten Quellbereich repräsentieren kann. Sie bewertet weder Risiko noch Qualität, Confidence oder Richtigkeit der Decision.

## Konsequenzen

### Positiv

- Fehlende Erklärungen werden explizit und maschinenlesbar statt implizit dargestellt.
- `NO_DATA`, `SOURCE_UNAVAILABLE` und `NOT_PART_OF_EXECUTION` bleiben semantisch getrennt.
- `UNKNOWN` verhindert unbelegte oder plausible Default-Zustände.
- Provenance und Source-Version können mit Completeness korreliert werden.
- Backend-, Reporting-, API- und UI-Verbraucher erhalten eine gemeinsame technische Semantik.
- Die bestehende `DecisionTrace`-/`ExplanationItem`-Familie bleibt die einzige Explainability Projection.
- Additive Einführung ermöglicht eine kleinschrittige Migration.
- Deterministische Reihenfolge und geschlossene Zustände verbessern Contract-Tests und Auditierbarkeit.

### Negativ

- Der Projektionsvertrag wird um eine weitere technische Struktur erweitert.
- Die Quellbereichs-Allowlist und ihre Ableitungsregeln müssen versioniert und dauerhaft gepflegt werden.
- Bestehende `DecisionResult`-Felder unterscheiden nicht in jedem Fall explizit zwischen leer, nicht verfügbar und nicht ausgeführt; solche Fälle müssen zunächst `UNKNOWN` bleiben.
- `SOURCE_UNAVAILABLE` und `NOT_PART_OF_EXECUTION` können ohne explizite kanonische Zustände nicht vollständig genutzt werden.
- Consumer müssen additive Completeness-Daten bewusst behandeln und dürfen sie nicht als fachliche Bewertung darstellen.
- Eine fehlerhafte Reason-Code- oder Referenzpflege kann interne technische Informationen offenlegen.

## Alternativen

### Ein einzelnes boolesches `complete`

Abgelehnt.

Ein boolescher Wert kann nicht erklären, ob Daten leer, eine Quelle nicht verfügbar oder ein Schritt nicht ausgeführt war. Er würde operativ unterschiedliche Zustände zusammenführen und zu Consumer-Heuristiken führen.

### Freie Statusstrings

Abgelehnt.

Freie Strings sind nicht vollständig validierbar, erschweren Versionierung und führen zu Schreibvarianten oder semantischer Drift. Eine geschlossene Zustandsmenge ist deterministischer und wartbarer.

### Vollständigkeit ausschließlich aus vorhandenen Items ableiten

Abgelehnt.

Vorhandene Items können `AVAILABLE` anzeigen. Das Fehlen eines Items unterscheidet jedoch nicht zwischen `NO_DATA`, `SOURCE_UNAVAILABLE`, `NOT_PART_OF_EXECUTION` und `UNKNOWN`.

### Fehlende Informationen als künstliche `ExplanationItem`-Texte erzeugen

Abgelehnt.

Generierte Texte würden fehlende fachliche Aussagen mit technischen Zuständen vermischen, Sequenzen verändern und möglicherweise plausible Fakten erzeugen. Completeness bleibt separate technische Projektionsmetadaten.

### Completeness in freie `metadata`-Dictionaries schreiben

Abgelehnt.

Freie Metadata-Keys besitzen keine geschlossene Semantik, keine stabile Reihenfolge und keine verlässliche Validierung. Der Vertrag benötigt eine explizite strukturierte Grenze.

### Completeness im Frontend berechnen

Abgelehnt.

Dies würde technische Vertragssemantik in die Presentation-Schicht verlagern und unterschiedliche Zustände je Client ermöglichen. Das Backend bleibt Single Source of Truth für die Projektion.

### Nur die vier konkreten Zustände ohne `UNKNOWN`

Abgelehnt.

Die heutigen kanonischen Quellen tragen nicht für jeden leeren oder fehlenden Wert ausreichend Information, um einen konkreten Zustand sicher zu bestimmen. Ohne `UNKNOWN` müsste die Projektion einen Zustand raten oder den Vertrag unvollständig lassen.

## Abgrenzung

Dieser ADR:

- implementiert keine Completeness-Felder, Enums oder Value Objects,
- verändert weder `DecisionResult` noch ein anderes Domainmodell,
- verändert keine bestehende Explainability-Struktur oder Builder-Logik,
- verändert keine Versionierungs- oder Provenance-Metadaten,
- definiert keine konkrete Python- oder Transportfeldbenennung,
- definiert keine vollständige Quellbereichs-Allowlist,
- implementiert keine API, UI, Persistenz, Session oder Execution-Trace-Änderung,
- entscheidet keine rollenbezogene Darstellung,
- führt keine zweite Explainability Projection ein,
- und ist keine Freigabe für eine Produktimplementierung.

Die konkrete technische Struktur, Feldnamen, Allowlist, Reason Codes und Tests benötigen nach Annahme einen separat freigegebenen Implementierungstask.

## Migration

Dieser ADR implementiert keine Migration.

Nach einer Annahme soll die Einführung ausschließlich über kleine, separat freigegebene AIDP-Tasks erfolgen:

1. Eine minimale geschlossene Quellbereichs-Allowlist für die bestehende Decision Explainability Projection festlegen.
2. Contract-Tests für die fünf Zustände, deterministische Reihenfolge, Provenance und unveränderte Decision-Daten erstellen.
3. Eine read-only Completeness-Value-Struktur additiv in die bestehende `core.explainability`-Familie einführen.
4. Den vorhandenen `DecisionExplainabilityProjectionBuilder` um eindeutige, allowlist-basierte Ableitungsregeln erweitern.
5. Serialisierung additiv und versioniert ergänzen.
6. Bestehende Backend-Verbraucher einzeln inventarisieren und gegen den erweiterten Vertrag prüfen.
7. API- und UI-Verbraucher ausschließlich über eigene freigegebene Tasks migrieren.

Jeder Schritt muss rückwärtskompatibel bleiben oder eine explizite Vertragsversion und Migration dokumentieren. Eine Big-Bang-Migration und eine parallele Completeness-Projektion sind ausgeschlossen.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität

- Contract-Tests müssen jeden Zustand semantisch prüfen und dürfen nicht nur Snapshots vergleichen.
- Tests müssen nachweisen, dass identische Quellen identische Zustände und Reihenfolgen erzeugen.
- `UNKNOWN` muss verwendet werden, wenn ein konkreter Zustand nicht beweisbar ist.
- `AVAILABLE` muss mit tatsächlich vorhandenen Items beziehungsweise Quellen korrelierbar sein.
- Completeness darf `DecisionResult`, Items oder Provenance nicht verändern.
- Source- und Projection-Versionen müssen mit der verwendeten Allowlist korrelierbar sein.

### Security und Datenschutz

- Reason Codes und Source References benötigen eine Allowlist und Datenminimierung.
- Interne Fehler, Stack Traces, Credentials, Payloads und sensible Evidence-Werte dürfen nicht serialisiert werden.
- Fehlende Berechtigung darf nicht durch detaillierte Completeness-Daten sensible Ressourcen offenlegen.
- Autorisierung erfolgt serverseitig vor einer Delivery-Projektion und wird nicht durch UI-Ausblendung ersetzt.
- `SOURCE_UNAVAILABLE` beschreibt technische Verfügbarkeit, ohne ungeprüfte interne Ursachen offenzulegen.

### Auditierbarkeit

- Jeder Zustand muss auf eine stabile Quellreferenz und Source-Version zurückführbar sein.
- Zustandsänderungen entstehen durch neue Projektionen statt stille Mutation.
- `UNKNOWN` macht unzureichende Quelllage sichtbar und auditierbar.
- Decision Explainability und Execution Explainability bleiben getrennt korrelierbar.

### Performance

- Eine kleine geschlossene Completeness-Sammlung verursacht linearen Aufwand zur Anzahl der freigegebenen Quellbereiche.
- Vollständige Source-Payloads werden nicht dupliziert.
- Die Allowlist muss klein und zweckgebunden bleiben; dynamische Metadateninventare sind ausgeschlossen.
- Caching muss Projection-Version, Source-Version, Erzeugungszeitpunkt und Autorisierung gemeinsam berücksichtigen.

### Kompatibilität und Betrieb

- Die spätere Einführung ist additiv vorgesehen.
- Bestehende Consumer dürfen unbekannte additive Completeness-Daten ignorieren, bis sie separat migriert werden.
- Neue Zustände innerhalb derselben Vertragsversion sind nicht stillschweigend zulässig; die geschlossene Zustandsmenge ist versioniert.
- Monitoring und Logging werden durch diesen ADR nicht eingeführt.
- Runbooks müssen später unterscheiden, ob `SOURCE_UNAVAILABLE` auf erwartete Abhängigkeiten oder Betriebsstörungen hinweist, ohne interne Fehlerdetails offenzulegen.

## Referenzen

- AIDP TASK-0017 – Explainability Completeness Contract
- AIDP TASK-0014 – Decision Explainability Projection Builder
- AIDP TASK-0015 – Version Explainability Projection
- AIDP TASK-0016 – Implement Explainability Provenance Metadata
- ADR-0001 – DecisionResult as Canonical Decision Contract (`ACCEPTED`)
- ADR-0002 – Canonical Execution Trace Contract (`ACCEPTED`)
- ADR-0003 – Canonical Explainability Projection Contract (`ACCEPTED`)
- `AGENTS.md`
- `ARCHITECTURE.md`
- `.ai/decisions/README.md`
- `core/decision/models.py`
- `core/explainability/decision_trace.py`
- `core/explainability/decision_trace_builder.py`
- `core/explainability/explanation_item.py`
- `tests/core/explainability/test_decision_explainability_contract.py`
- `tests/core/explainability/test_decision_explainability_projection_versioning.py`
- `tests/core/explainability/test_decision_explainability_provenance.py`

## Architektur-Review

Status:
APPROVED

Bemerkungen:
ADR-0004 definiert die geforderten Completeness-Zustände eindeutig, ergänzt `UNKNOWN` als sicheren Fallback und ordnet Completeness ohne zweite Projektionsfamilie in die bestehende Decision Explainability Projection ein. Determinismus, Provenance, Versionierung, read-only Verhalten, Serialisierungsgrenzen, Rückwärtskompatibilität, Migration sowie Qualitäts-, Sicherheits- und Betriebsfolgen sind vollständig berücksichtigt. Der Vertrag wahrt ADR-0001 bis ADR-0003 und erzeugt keine fachlichen Fakten. Der dokumentierte Inhalt wurde im Architecture Review von TASK-0017 mit PASS freigegeben.

Freigabe:
Architect
