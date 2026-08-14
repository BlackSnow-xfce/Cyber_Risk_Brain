# ADR-0006 – Decision Evidence Architecture

## Status

ACCEPTED

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI benötigt eine eindeutige Architektur für alle Tatsachen, Beobachtungen und deterministisch abgeleiteten Signale, die eine fachliche Entscheidung tragen. ADR-0001 legt `core.decision.models.DecisionResult` als kanonisches fachliches Decision-Ergebnis fest. Dieses Modell enthält bereits eine Sammlung von `core.decision.models.Evidence`; die Explainability Projection aus ADR-0003 projiziert diese Evidence read-only als Explanation Items und verweist über Provenance auf die entsprechende Position im `DecisionResult`.

Der aktuelle Bestand bildet jedoch noch keinen konsistenten Evidence-Lebenszyklus:

* `core/decision/models.py` definiert `EvidenceType`, `Evidence` und `DecisionResult.evidence`. `Evidence` enthält Typ, Schlüssel, Wert, optionale Quelle und Beschreibung sowie Gewicht, ist aktuell aber veränderlich.
* `core/decision/decision_engine.py` orchestriert Attack Reasoning, Business Context, Risk, Priority, Action, Confidence, Recommendations und einen `EvidenceBuilder`. Evidence wird dort nach mehreren fachlichen Berechnungen aus Attack Reasoning aufgebaut und anschließend dem `DecisionResult` übergeben.
* `core/decision/evidence.py` exportiert inzwischen die Evidence-Klasse aus `core.decision.models`; der vorhandene `EvidenceBuilder` und der ältere aggregierte Decision-Trace-Pfad verwenden jedoch noch Aufruf- und Feldannahmen einer früheren Evidence-Struktur.
* `core/decision/decision_context.py` hält eine untypisierte, veränderliche Evidence-Liste. `core/decision/decision_trace_builder.py` erzeugt Evidence erneut und schreibt sie in diesen Context zurück.
* `core/decision/decision_trace.py` speichert Evidence zusammen mit Decision-, AI-, Explainability-, Correlation-, Timeline- und Präsentationsdaten. Nach ADR-0001 ist diese Struktur kein kanonisches Decision-Ergebnis.
* Der `RiskEngine` berechnet Risk direkt aus einem untypisierten Input-Dictionary. Correlations erscheinen im älteren Context und Trace als Stringlisten; ein eigenständiger kanonischer Correlation- oder Evidence-Collection-Vertrag ist im betrachteten Backend nicht vorhanden.
* `core/explainability/decision_trace_builder.py` liest ausschließlich `DecisionResult`, transformiert dessen Evidence strukturell und erzeugt keine zusätzlichen Evidence-Fakten.

Damit sind Erzeugung, Ownership, Mutabilität und Reihenfolge der Evidence noch uneindeutig. Ohne einen kanonischen Vertrag drohen parallele Evidence-Modelle, nachträgliche Veränderungen der Entscheidungsgrundlage, zyklische Abhängigkeiten zwischen Decision und Explainability sowie nicht auditierbare KI- oder Engine-Aussagen.

## Entscheidung

PredatorAI verwendet eine einzige kanonische **Decision Evidence Architecture**. Evidence ist ein fachlicher, unveränderlicher und provenance-pflichtiger Nachweis, der einer Decision als überprüfbare Grundlage zur Verfügung stand.

### Definition von Evidence

Evidence repräsentiert genau eine beobachtete oder deterministisch abgeleitete, entscheidungsrelevante Aussage einschließlich ihrer Herkunft. Sie ist weder die Entscheidung selbst noch deren sprachliche Erklärung. Ein kanonisches Evidence-Element muss konzeptionell mindestens besitzen:

* stabile Identität innerhalb des Evidence-Vertrags,
* expliziten Evidence-Typ,
* einen semantisch eindeutigen Schlüssel und Wert,
* Provenance mit Quelltyp und stabiler Quellreferenz,
* Kennzeichnung, ob es sich um Source Evidence oder Derived Evidence handelt,
* sowie die für Audit und Vertragsversionierung erforderlichen technischen Metadaten.

Diese ADR legt die Architekturmerkmale fest, aber keine neue Python-Klasse, Feldnamen, Serialisierung oder Persistenzstruktur.

**Source Evidence** ist eine unveränderte, normalisierte Beobachtung aus einer autoritativen Quelle, beispielsweise Finding, Asset, Control, Threat Intelligence, Exposure oder Business Context. **Derived Evidence** ist ein deterministisches Ergebnis einer fachlich autorisierten Engine, beispielsweise ein Correlation- oder Risk-Signal. Derived Evidence muss seine Eingangs-Evidence referenzieren können und darf keine nicht belegte Tatsache behaupten.

Ein fachlicher Score, eine Korrelation oder ein Modelloutput ist nur dann Evidence, wenn er als überprüfbares Ergebnis eines freigegebenen Produzenten mit vollständiger Provenance vorliegt. Freitext, bloße Annahmen, Explainability-Texte, Recommendations und fehlende Informationen sind keine Evidence.

### Single Source of Truth und Ownership

Der kanonische Evidence-Vertrag gehört zur Domain-Schicht. Für eine konkrete abgeschlossene Decision ist der im kanonischen `DecisionResult` enthaltene, unveränderliche **Decision Evidence Snapshot** die einzige Wahrheit darüber, welche Evidence diese Decision tatsächlich getragen hat.

Quellsysteme bleiben jeweils autoritativ für ihre ursprünglichen Rohdaten. Sie sind jedoch nicht die Wahrheit darüber, welcher Datenstand für eine konkrete Decision verwendet wurde. Evidence Producer besitzen die Erzeugung ihrer typisierten Evidence-Ausgaben. Die kontrollierte Application-Grenze der Evidence Collection besitzt Sammlung, Validierung, Normalisierung, Deduplizierung und Abschluss des Snapshots. Die Decision Engine konsumiert diesen Snapshot und gibt ihn unverändert mit dem `DecisionResult` weiter.

Nach Abschluss des Snapshots darf keine Komponente Evidence hinzufügen, entfernen oder verändern. Eine Neubewertung mit neuer oder geänderter Evidence erzeugt eine neue Decision-Ausführung und einen neuen Evidence Snapshot; sie überschreibt nicht rückwirkend die Grundlage einer bestehenden Decision.

### Lebenszyklus

Der kanonische Lebenszyklus lautet:

```text
Authoritative Sources
        │
        ▼
Evidence Producers
        │  source or derived evidence + provenance
        ▼
Evidence Collection Boundary
        │  validate · normalize · deduplicate · order
        ▼
Immutable Decision Evidence Snapshot
        │
        ├──► Domain Engines / Decision
        │            │
        │            ▼
        │      DecisionResult
        │            │
        │            └── owns the exact snapshot used
        │
        ├──► Execution Trace references production/consumption events
        └──► Explainability reads from DecisionResult only
```

1. Autoritative Quellen stellen Rohbeobachtungen bereit.
2. Autorisierte Producer transformieren diese in typisierte Source Evidence. Fachliche Engines dürfen ausschließlich ihre eigenen deterministisch abgeleiteten Ergebnisse als Derived Evidence erzeugen.
3. Die Evidence Collection Boundary prüft Vertragsgültigkeit, Provenance, Referenzen und Duplikate. Sie trifft keine Decision und berechnet keine fachliche Priorität.
4. Vor der finalen Decision wird die relevante Evidence als unveränderlicher, deterministisch geordneter Snapshot abgeschlossen.
5. Risk-, Correlation- und weitere fachliche Engines konsumieren Evidence und dürfen neue Derived Evidence ausschließlich vor Abschluss beziehungsweise über einen explizit geordneten Collection-Schritt zurückgeben. Ein Producer darf seine eigene Ausgabe nicht rekursiv wieder als unbegrenzte Eingabe verwenden.
6. Die Decision Engine konsumiert den abgeschlossenen Snapshot und erzeugt `DecisionResult`. Der im Ergebnis enthaltene Snapshot dokumentiert exakt die verwendete Entscheidungsgrundlage.
7. Explainability projiziert ausschließlich die Evidence des `DecisionResult`. Ein Execution Trace dokumentiert Erzeugung, Annahme oder Ablehnung über stabile Referenzen, besitzt aber die fachliche Evidence nicht.

### Erzeuger und Leser

Evidence erzeugen dürfen ausschließlich explizit registrierte und fachlich verantwortete Producer:

* Adapter autoritativer Quellsysteme für Source Evidence,
* Domain Engines für ihre deterministisch Derived Evidence,
* kontrollierte, policy-konforme Intelligence-Komponenten, sofern ihre Ausgabe denselben Validierungs- und Provenance-Vertrag erfüllt.

Evidence Collection, Decision-Orchestrierung, API, Frontend, Explainability, Reporting und Execution Trace dürfen keine fachlichen Evidence-Fakten erfinden. Collection darf Evidence validieren, normalisieren, deduplizieren und verwerfen, aber keine fehlenden Werte plausibilisieren. Decision-Komponenten dürfen Evidence auswerten; sie ändern den abgeschlossenen Snapshot nicht. Presentation-Komponenten lesen ausschließlich freigegebene Projektionen.

KI-Komponenten erhalten keine Sonderrolle. Eine KI-Aussage wird nicht allein durch Modellerzeugung zu kanonischer Evidence. Soll sie künftig Evidence liefern, muss ein separat akzeptierter Vertrag Produzent, Modell- und Eingabeversion, Provenance, Validierung, Unsicherheit und menschliche beziehungsweise technische Freigabe definieren. Diese ADR implementiert oder spezifiziert keinen LLM-Pfad.

### Dependency Direction

Die erlaubte Hauptrichtung lautet:

```text
Infrastructure Source Adapters
            │
            ▼
Domain Evidence Contract ◄── Domain Evidence Producers
            │
            ▼
Application Evidence Collection
            │
            ▼
Domain Risk / Correlation / Decision Consumers
            │
            ▼
DecisionResult
      ├──► Explainability Projection
      ├──► API/Presentation Projections
      └──► stable references from Execution Trace
```

Der Domain-Evidence-Vertrag importiert weder Application, Infrastructure, Explainability, API noch Frontend. Producer dürfen nicht von `DecisionResult` oder Explainability abhängen, um Evidence für dieselbe Decision zu erzeugen. Explainability und Presentation hängen ausschließlich in Leserichtung vom abgeschlossenen `DecisionResult` ab. Execution Trace und Evidence dürfen sich über stabile Identitäten korrelieren, aber nicht gegenseitig besitzen. Diese Regeln verhindern zyklische Abhängigkeiten.

### Abgrenzung der Konzepte

* **Evidence** beantwortet: „Welche belegte Beobachtung oder deterministische Ableitung stand zur Verfügung?“
* **Decision** beantwortet: „Welches fachliche Ergebnis wurde auf dieser Grundlage beschlossen?“ `DecisionResult` besitzt die exakte verwendete Evidence-Snapshot-Referenz beziehungsweise -Einbettung, bleibt aber ein Decision-Vertrag.
* **Explainability** beantwortet: „Wie wird die vorhandene Decision einschließlich ihrer Evidence nachvollziehbar dargestellt?“ Sie ist gemäß ADR-0003 ein read-only Read Model und erzeugt keine Evidence.
* **Execution Trace** beantwortet: „Welche Verarbeitungsschritte fanden in welcher Reihenfolge statt?“ Er referenziert Evidence-Artefakte und Collection-Ereignisse, ist aber weder Evidence-Speicher noch Decision-Ergebnis.
* **Correlation** verbindet vorhandene Evidence nach freigegebenen Regeln und darf daraus Derived Evidence erzeugen. Die Korrelation selbst ersetzt weder Quell-Evidence noch Decision.
* **Risk** bewertet vorhandene Evidence nach freigegebenen Regeln und darf sein Ergebnis als Derived Evidence ausgeben. Risk ist keine Roh-Evidence und darf Provenance zu seinen Eingängen nicht verlieren.

### Immutable Evidence und Erweiterbarkeit

Kanonische Evidence und der abgeschlossene Snapshot sind unveränderlich. Veränderliche Listen, Dictionaries oder Value-Objekte dürfen nicht über die Abschlussgrenze geteilt werden. Deterministische Identität und Reihenfolge dürfen nicht von Speicheradresse, Laufreihenfolge nebenläufiger Producer oder UI-Sortierung abhängen.

Erweiterbarkeit erfolgt additiv durch neue Evidence-Typen und Producer hinter dem kanonischen Vertrag. Ein neuer Producer benötigt einen klaren Owner, eindeutige Semantik, Provenance, deterministische Normalisierung, Versionsstrategie und Contract-Tests. Er darf weder ein paralleles Evidence-Modell noch einen zweiten Collection-Pfad einführen. Unbekannte Evidence-Typen müssen kontrolliert abgelehnt oder als explizit unterstützte Erweiterung behandelt werden; stillschweigende Umdeutung ist unzulässig.

### Auditfähigkeit

Für jede in einer Decision verwendete Evidence muss nachvollziehbar sein:

* welcher Producer und welche Quelle sie erzeugten,
* welche Quellreferenz und Version zugrunde lagen,
* ob sie Source oder Derived Evidence ist,
* welche Eingangs-Evidence eine Ableitung trug,
* zu welchem Decision Evidence Snapshot sie gehörte,
* und welcher Execution Trace ihre Verarbeitung beobachtete.

Auditfähigkeit verlangt stabile Referenzen und Integrität, aber diese ADR entscheidet keine Datenbank, Aufbewahrungsdauer, Signatur, Hash-Strategie oder Serialisierung.

## Begründung

Die Entscheidung baut auf dem bereits akzeptierten `DecisionResult` auf, statt eine zweite Decision- oder Evidence-Wahrheit einzuführen. Ein unveränderlicher Snapshot macht die tatsächliche Entscheidungsgrundlage reproduzierbar und verhindert, dass spätere Quelländerungen oder Presentation-Projektionen historische Decisions rückwirkend verändern.

Die Trennung zwischen Producer, Collection, Consumer und Projektion gibt jeder Schicht eine überprüfbare Verantwortung. Source und Derived Evidence ermöglichen Risk- und Correlation-Ergebnisse, ohne Rohbeobachtungen und fachliche Ableitungen zu vermischen. Die gerichtete Abhängigkeit wahrt ADR-0001 bis ADR-0003 und ermöglicht künftige KI-Produzenten nur unter denselben Provenance- und Validierungsregeln.

## Konsequenzen

### Positiv

* Eine Decision besitzt eine eindeutige, reproduzierbare Evidence-Grundlage.
* Evidence, Decision, Explainability und Execution Trace bleiben getrennte Verträge.
* Provenance und stabile Referenzen verbessern Auditierbarkeit und Fehleranalyse.
* Neue Quellen, Correlation- und Risk-Produzenten können additiv integriert werden.
* KI-Ausgaben können den kanonischen Pfad nicht ohne expliziten Vertrag umgehen.
* Die Dependency Direction verhindert zirkuläre und parallele Evidence-Architekturen.

### Negativ

* Der aktuelle mutable `DecisionResult`- und Listenbestand erfüllt die Ziel-Invarianten noch nicht vollständig.
* Der ältere Context-/DecisionTrace-/EvidenceBuilder-Pfad ist Migration Debt.
* Ein vollständiger Snapshot kann Speicher- und Kopierkosten erhöhen.
* Producer benötigen stabile Identitäten, Provenance und Versionierung.
* Mehrstufige Derived Evidence verlangt eine explizite, azyklische Ausführungsordnung.

## Alternativen

### `DecisionResult.evidence` ohne separaten Lifecycle verwenden

Die vorhandene Liste könnte lediglich als beliebige Sammlung weitergeführt werden. Dies wurde abgelehnt, weil Ownership, Zeitpunkt, Provenance, Mutabilität und Producer-Verantwortung ungeklärt blieben.

### Der ältere `core.decision.DecisionTrace` als Evidence Owner

Diese Struktur enthält bereits Evidence neben vielen weiteren Feldern. Sie wurde nicht gewählt, weil ADR-0001 ihren kanonischen Anspruch ausdrücklich verworfen hat und sie Decision-, AI-, Explainability-, Timeline- und Präsentationsverantwortungen vermischt.

### Explainability als Evidence Store

Explainability könnte alle dargestellten Begründungen als Evidence behandeln. Dies widerspricht ADR-0003: Eine read-only Projektion darf keine fachlichen Fakten erzeugen oder besitzen.

### Execution Trace als Evidence Store

Ein Execution Trace könnte Werte jedes Verarbeitungsschritts vollständig aufnehmen. Dies würde Audit-Ereignis und fachliches Artefakt vermischen, Daten duplizieren und ADR-0002 verletzen. Der Trace referenziert Evidence stattdessen stabil.

### Unmittelbarer Zugriff aller Engines auf Rohquellen

Jede Engine könnte Finding-, Asset-, Threat- und Business-Daten selbst laden. Dies erzeugte uneinheitliche Datenstände, zyklische Infrastrukturabhängigkeiten und nicht reproduzierbare Decisions. Der kontrollierte Collection-Pfad wurde daher bevorzugt.

### KI-Ausgaben als implizite Evidence akzeptieren

Dies wurde abgelehnt, weil generierte Aussagen ohne nachweisbare Quelle und Validierung keine belastbare Evidence sind. Ein späterer KI-Evidence-Vertrag benötigt eine eigene Architekturentscheidung.

## Abgrenzung

Dieser ADR erstellt keine Python-Klassen, Enums, Builder, DTOs, APIs, Datenbanken, Serialisierung, Tests oder Frontend-Strukturen. Er ändert weder Decision-, Risk-, Correlation-, Confidence- noch Recommendation-Logik. Er implementiert keine Evidence Collection, keine Persistenz, kein LLM und keinen Migrationsschritt. Konkrete Identitäts-, Versions-, Hash-, Retention- und Transportformate benötigen separat freigegebene Entscheidungen oder Implementierungstasks.

## Migration

Diese ADR führt keine Migration aus. Nach einer Annahme darf die Zielarchitektur nur in kleinen, separat freigegebenen Schritten eingeführt werden:

1. Bestehende Evidence-Produzenten und -Verbraucher inventarisieren und gegen Source/Derived sowie Producer/Reader klassifizieren.
2. Den bestehenden `core.decision.models.Evidence`-Vertrag auf Identität, Provenance und tiefe Unveränderlichkeit prüfen, ohne eine zweite Modellfamilie einzuführen.
3. Den kanonischen Evidence-Collection-Einstieg vor der Decision-Orchestrierung definieren.
4. Risk- und Correlation-Abhängigkeiten in eine explizite, azyklische Reihenfolge überführen.
5. Den älteren Context-/DecisionTrace-/EvidenceBuilder-Pfad verbraucherweise migrieren; keine Big-Bang-Ersetzung und kein Parallelbetrieb als neue Zielarchitektur.
6. Explainability und Execution Trace ausschließlich über den finalen Snapshot beziehungsweise stabile Referenzen anbinden.

Bestehende öffentliche Verträge bleiben durch diesen Dokumentationstask unverändert. Jede spätere Änderung benötigt Kompatibilitätsprüfung, Tests und Rollback-Strategie.

## Qualitäts- und Sicherheitsauswirkungen

### Qualität und Kompatibilität

Spätere Implementierungen benötigen Contract-Tests für Unveränderlichkeit, deterministische Ordnung, Provenance, Deduplizierung und unveränderte Übergabe an `DecisionResult`. Bestehende Verbraucher dürfen nicht ohne versionierte Migration auf eine neue Struktur umgestellt werden. Dieser ADR verursacht selbst keinen Laufzeit- oder Breaking Change.

### Security und Datenschutz

Evidence kann sensible Asset-, Finding-, Threat-, Control- und Business-Daten enthalten. Producer und Verbraucher benötigen Least-Privilege-Zugriff; Projektionen müssen Daten minimieren und klassifizierte Inhalte filtern. Provenance darf keine Secrets enthalten. Untrusted Source Values müssen an Systemgrenzen validiert werden. Eine UI-Sichtbarkeit ist keine Autorisierung.

### Auditierbarkeit

Unveränderliche Snapshots, stabile Identitäten und gerichtete Provenance ermöglichen die Rekonstruktion der Entscheidungsgrundlage. Execution Trace ergänzt die zeitliche Verarbeitung, ersetzt aber nicht die Evidence-Integrität. Konkrete manipulationssichere Speicherung bleibt außerhalb dieses ADRs.

### Performance und Betrieb

Snapshots und Ableitungsketten können Kopier-, Speicher- und Ladeaufwand verursachen. Optimierungen dürfen Unveränderlichkeit und Auditfähigkeit nicht durch gemeinsam veränderliche Objekte oder implizite Lazy-Quellen unterlaufen. Retention, Archivierung und externe Speicherung werden separat entschieden.

### KI-Kompatibilität

Der Vertrag ist producer-neutral und kann künftig kontrollierte KI-Ausgaben aufnehmen. Dafür gelten dieselben Anforderungen an Provenance, Versionierung, Validierung und Unveränderlichkeit; KI erhält keinen direkten Schreibzugriff auf abgeschlossene Snapshots. Diese ADR erteilt keine Freigabe für KI- oder LLM-Evidence.

## Referenzen

* AIDP TASK-0021
* `AGENTS.md`
* `ARCHITECTURE.md`
* ADR-0001 – DecisionResult as Canonical Decision Contract
* ADR-0002 – Canonical Execution Trace Contract
* ADR-0003 – Canonical Explainability Projection Contract
* ADR-0004 – Explainability Completeness Contract
* `core/decision/models.py`
* `core/decision/decision_engine.py`
* `core/decision/evidence.py`
* `core/decision/evidence_builder.py`
* `core/decision/decision_context.py`
* `core/decision/decision_trace.py`
* `core/decision/decision_trace_builder.py`
* `core/decision/risk_engine.py`
* `core/explainability/decision_trace.py`
* `core/explainability/decision_trace_builder.py`

## Architektur-Review

Status: APPROVED  
Bemerkungen: Architecture Review für TASK-0021 mit `PASS` abgeschlossen. Die kanonische Evidence-Architektur definiert Ownership, Lebenszyklus, Unveränderlichkeit und eine azyklische Dependency Direction konsistent zu ADR-0001 bis ADR-0005. Die dokumentierte Migration Debt und die noch offenen Detailverträge sind keine Blocker und benötigen separat freigegebene Folgetasks.  
Freigabe: Architect, 2026-08-05
