# PredatorAI v3 Architecture Charter

Status: **BASELINE**  
Version: 1.0  
Scope: Architekturleitlinien für PredatorAI v3  
Freigabe: Architect, 2026-08-14, TASK-0043 `PASS / APPROVED`

Diese Charta konsolidiert den durch ADR-0001 bis ADR-0007 und die freigegebenen Architekturartefakte dokumentierten Architekturstand. Sie ist die freigegebene Architecture Baseline 1.0. Dauerhafte Änderungen an dieser Baseline benötigen weiterhin einen freigegebenen AIDP-Scope und, sofern relevant, einen neuen Architecture Decision Record.

## Vision

PredatorAI ist eine Enterprise Cyber Reasoning Platform. Sie verbindet Cybersecurity-Daten, fachlichen Kontext und nachvollziehbare Analyse zu belastbaren Entscheidungen für unterschiedliche Enterprise-Rollen.

Die Plattform soll Ergebnisse liefern, die:

- fachlich nachvollziehbar,
- deterministisch reproduzierbar, soweit der jeweilige Ausführungspfad deterministisch definiert ist,
- auditierbar,
- auf ihre Eingaben und Begründungen zurückführbar,
- sicher erweiterbar,
- und langfristig wartbar sind.

Architekturqualität, Erklärbarkeit und klare Verantwortungsgrenzen haben Vorrang vor kurzfristigem Feature-Umfang.

## Architecture Baseline

Die fachliche und taktische Architektur ist für den aktuellen Stand vollständig dokumentiert. Vor First Live Intelligence werden keine weiteren fachlichen Architekturartefakte benötigt.

Die Architecture Baseline 1.0 umfasst:

- zwölf kanonische Domain Boundaries mit eindeutiger Ownership,
- Canonical Entities und immutable Value Objects,
- Aggregate Boundaries und gerichtete Aggregate Relationships,
- eine azyklische Domain-Dependency-Matrix,
- Domain Integration Principles gemäß ADR-0007,
- Domain Services, Domain Policies und fachliche Domain Events,
- Application Services sowie getrennte Command- und Query-Grenzen,
- DecisionResult, Evidence, Explainability und Execution Trace als getrennte Verantwortungen gemäß ADR-0001 bis ADR-0006,
- Mission Console Workspaces als Presentation-Grenze gemäß ADR-0005.

Technische Runtime-, Delivery-, Persistenz- und Integrationsentscheidungen sind keine fehlende Facharchitektur. Sie werden nur innerhalb späterer, ausdrücklich freigegebener Implementierungs- oder Runtime-Scopes konkretisiert.

## Architecture Principles

### Backend as Single Source of Truth

Das Backend ist die fachliche Single Source of Truth. Fachliche Entscheidungen, Bewertungen, Regeln und Invarianten werden im Backend definiert. Das Frontend visualisiert Ergebnisse und steuert Benutzerinteraktionen, erzeugt aber keine konkurrierende Fachwahrheit.

### One Canonical Model per Concept

Ein fachliches Konzept besitzt genau ein kanonisches Modell. Projektionen für API, Explainability oder UI dürfen dieses Modell nicht duplizieren oder ersetzen.

### Explicit Responsibilities

Komponenten, Module und Schichten erhalten klar abgegrenzte Verantwortlichkeiten. Orchestrierung, Fachlogik, technische Integration und Darstellung werden nicht vermischt.

### Dependencies Point Inward

Äußere Schichten dürfen von inneren Schichten abhängen. Die Domain darf nicht von UI-Frameworks, HTTP, Persistenz, externen Diensten oder konkreten Infrastrukturimplementierungen abhängen.

### Explainability by Design

Fachliche Ergebnisse müssen auf ihre relevanten Eingaben, Evidenzen und Begründungen zurückgeführt werden können. Explainability ist ein expliziter Bestandteil der Architektur und keine nachträglich ergänzte UI-Funktion.

### Determinism before Automation

Nachvollziehbare und reproduzierbare Verarbeitung hat Vorrang vor autonomer Automatisierung. KI-, LLM- oder heuristische Komponenten dürfen deterministische Kernpfade nicht verdecken und benötigen explizite Schnittstellen und Governance.

### No Parallel Architectures

Neue Fähigkeiten erweitern bestehende Verantwortungsgrenzen. Doppelte Engines, konkurrierende Modelle, alternative Composition Roots und parallele Datenflüsse sind ohne freigegebene Migration unzulässig.

### Evolution through Small Changes

Architektur wird durch kleine, überprüfbare und rückverfolgbare Änderungen weiterentwickelt. Refactoring wird gegenüber einer parallelen Neuerstellung bevorzugt.

## Layered Architecture

PredatorAI folgt einer geschichteten Architektur. Die Verzeichnisstruktur ist historisch gewachsen und bildet diese Grenzen noch nicht überall vollständig ab; die folgenden Regeln definieren die verbindliche Zielrichtung für neue Änderungen.

### Presentation Layer

Beispiele:

- Frontend Workspaces und Pages
- React-Komponenten
- Dashboard- und Explainability-Darstellungen
- API- und Delivery-Endpunkte

Verantwortung:

- Ergebnisse darstellen
- Benutzerinteraktionen entgegennehmen
- Navigation und Präsentationszustand verwalten
- transportbezogene Eingaben an Systemgrenzen validieren
- kanonische Ergebnisse für konkrete Benutzerrollen projizieren

Nicht erlaubt:

- fachliche Risiko- oder Prioritätsberechnung
- Decision-, Recommendation- oder Reasoning-Regeln
- konkurrierende Domainmodelle
- versteckte Fachlogik in UI-Komponenten

### Application Layer

Beispiele:

- Application Services
- Orchestratoren
- Use-Case-Koordination
- Composition Roots

Verantwortung:

- einen Anwendungsfall koordinieren
- Domain-Funktionen in definierter Reihenfolge aufrufen
- Lifecycle- und Ausführungsgrenzen verwalten
- Abhängigkeiten über explizite Schnittstellen verbinden
- Ergebnisse und Fehler kontrolliert an Delivery-Schichten übergeben

Die Application-Schicht koordiniert Fachlogik, definiert aber keine neuen fachlichen Regeln.

### Domain Layer

Der bestehende fachliche Kern liegt insbesondere unter `core/decision` und den zugehörigen Core-Modulen. Die verbindlichen fachlichen Verantwortungen sind in den Architekturartefakten unter `.ai/architecture/` dokumentiert. Künftige Implementierungen müssen ihre konkrete Modulzuordnung gegen diese Grenzen prüfen.

Verantwortung:

- fachliche Modelle und Invarianten
- Decision-, Risk-, Confidence- und Recommendation-Konzepte
- nachvollziehbare fachliche Auswertung
- frameworkunabhängige Verträge

Nicht erlaubt:

- React- oder UI-Abhängigkeiten
- HTTP- oder Datenbankzugriffe
- konkrete Connector-Implementierungen
- globale technische Zustandsverwaltung

### Infrastructure Layer

Beispiele:

- externe Connectoren
- Datenbankzugriffe
- Threat-Intelligence- und Scanner-Integrationen
- technische LLM-Adapter
- Datei-, Netzwerk- und Persistenzimplementierungen

Verantwortung:

- technische Schnittstellen implementieren
- externe Systeme anbinden
- Daten transportieren und persistieren
- technische Fehler in kontrollierte Application-Ergebnisse übersetzen

Infrastructure darf Domainmodelle verwenden, aber keine konkurrierenden Fachmodelle etablieren.

## Dependency Rules

Die erlaubte Hauptrichtung lautet:

```text
Presentation → Application → Domain
Infrastructure → Application/Domain Contracts
```

Zusätzlich gilt:

- Domain importiert weder Presentation noch Infrastructure.
- Presentation ruft Fachlogik über Application-Verträge auf.
- Application erhält konkrete Infrastrukturabhängigkeiten durch Injection oder Composition.
- Infrastructure wird an kontrollierten Composition Roots zusammengesetzt.
- Zirkuläre Abhängigkeiten zwischen Schichten sind unzulässig.
- Barrel-Exports dürfen Verantwortungsgrenzen vereinfachen, aber keine Zyklen oder versteckten Abhängigkeiten erzeugen.
- Shared- oder Utility-Module dürfen nicht als Ablage für unklare Fachverantwortung dienen.

## Core Domain

### Decision

Decision ist das zentrale fachliche Domänenkonzept. Das bestehende kanonische Decision-Modell darf nicht durch ältere Response-Modelle oder neue parallele Ergebnisse ersetzt werden.

Eine Decision beschreibt das fachliche Ergebnis. Sie ist nicht gleichbedeutend mit dem zeitlichen Ausführungsablauf oder dessen UI-Erklärung.

### Evidence and Reasoning

Evidence beschreibt fachliche Grundlagen. Reasoning beschreibt den nachvollziehbaren Analyseweg. Beide Konzepte müssen getrennt von Presentation und technischer Ausführungssteuerung bleiben.

### Recommendation

Recommendation beschreibt eine fachlich begründete Empfehlung. Die Darstellung einer Recommendation und eine spätere technische Ausführung sind getrennte Verantwortlichkeiten.

### Explainability

Explainability ist eine read-only Sicht auf vorhandene fachliche Ergebnisse und deren Begründungen. Sie darf keine Entscheidung erzeugen, verändern oder zur zweiten fachlichen Quelle werden.

Die vorhandenen Trace-Strukturen unter `core/decision` und `core/explainability` besitzen unterschiedliche Verantwortlichkeiten. Eine Konsolidierung oder Umbenennung ist nicht Bestandteil dieser Charta und benötigt eine eigene Architekturentscheidung.

### Future Reasoning Intelligence Boundary

Künftige Session-, Execution-Trace- oder Orchestrierungsmodelle gehören nicht automatisch zur Domain. Ihre konkrete Runtime-Zuordnung bleibt ein Runtime-Thema und darf die akzeptierte Trennung von DecisionResult, Evidence, Explainability und Execution Trace nicht verändern.

Diese Charta führt keine Reasoning Session und keinen neuen Execution Trace ein.

## Engineering Rules

- Vor jeder Änderung werden bestehende Typen, Komponenten, Services und Ausführungspfade geprüft.
- Änderungen bleiben innerhalb des freigegebenen Tasks und erzeugen den kleinsten sinnvollen Diff.
- Funktionierender Code wird nicht aus Stilgründen umgeschrieben.
- Wiederverwendung und Refactoring werden gegenüber Duplikation bevorzugt.
- Businesslogik bleibt außerhalb des Frontends.
- Öffentliche Schnittstellen werden strikt und verständlich typisiert.
- Versteckte Seiteneffekte, globale Zustandsänderungen und unnötige Kopplung werden vermieden.
- Abhängigkeiten werden an klaren Composition Roots zusammengesetzt.
- Neue Architekturabstraktionen benötigen einen konkreten technischen Nutzen.
- Dauerhafte Architekturentscheidungen benötigen ein Review und gegebenenfalls einen ADR.
- Dateien werden nicht gelöscht, verschoben oder umbenannt, ohne Scope und Auswirkungen zu prüfen.
- Sicherheits-, Build-, Laufzeit- und Architekturprobleme haben Vorrang vor kosmetischen Änderungen.

Die detaillierten Repository-Regeln in `AGENTS.md` bleiben verbindlich. Bei Widersprüchen hat `AGENTS.md` Vorrang, bis diese Charta ausdrücklich freigegeben und die Abweichung dokumentiert wurde.

## AIDP

Der AI Development Protocol Lifecycle lautet:

```text
READY → IN_PROGRESS → REVIEW → DONE
```

Dabei gilt:

- Nur ein explizit freigegebener READY-Task darf begonnen werden.
- Jeder Task beschreibt einen logisch zusammenhängenden und klar abgegrenzten Arbeitsschritt.
- Input, erlaubter Output, Regeln und Abschlusskriterien werden vor der Umsetzung festgelegt.
- Nicht beauftragte Änderungen sind untersagt.
- Der Implementation Agent dokumentiert Änderungen, Prüfungen, Besonderheiten und Risiken.
- Nach der Implementierung wechselt ein Task nach REVIEW, nicht direkt nach DONE.
- Erst der Architect darf einen erfolgreich geprüften Task als DONE freigeben.
- Architekturentscheidungen werden durch den Architect verantwortet.
- Abhängige Folgetasks werden erst freigegeben, wenn ihre Voraussetzungen erfüllt sind.

Die Dateien unter `.ai/` bilden den versionskontrollierten Kommunikations-, Task- und Review-Kanal. `AGENTS.md` bleibt die übergeordnete Grundlage für Repository-Verhalten.

## Quality Gates

Quality Gates werden proportional zum Scope angewendet. Ein Task darf Prüfungen nur auslassen, wenn dies im freigegebenen Task ausdrücklich begründet ist.

### Backend

Aktueller Mindeststandard für Codeänderungen:

- relevante Python-Tests ausführen, soweit vorhanden
- zentrale Import- und Laufzeitpfade prüfen
- keine unerwarteten Änderungen außerhalb des Scopes
- Frontend-Typecheck zusätzlich ausführen, wenn gemeinsame Verträge oder Frontend-Auswirkungen betroffen sind

Der bestehende Standard-Testbefehl für relevante Python-Änderungen ist `python -m pytest`. Welche zusätzlichen Prüfungen erforderlich sind, bestimmt der jeweilige freigegebene Task proportional zu seinem Scope.

### Frontend

Für Frontend-Codeänderungen gilt mindestens:

- `npm run typecheck`
- Buildprüfung bei buildrelevanten Änderungen
- Browser-Smoke-Test bei UI-relevanten Änderungen
- Prüfung auf unbeabsichtigte Layout- oder Workflowänderungen

### Architecture

Architekturrelevante Änderungen benötigen:

- dokumentierten Scope
- Prüfung der Abhängigkeitsrichtung
- Prüfung auf doppelte Modelle oder Verantwortlichkeiten
- Bewertung von Kompatibilität und Migration
- ADR bei dauerhaft relevanten Entscheidungen
- explizite Freigabe durch den Architect

### Completion

Ein Task ist erst abgeschlossen, wenn:

- alle Abschlusskriterien erfüllt sind,
- vorgeschriebene Prüfungen erfolgreich waren,
- das Ergebnis nachvollziehbar dokumentiert wurde,
- keine unerwarteten Änderungen bestehen,
- und das Architektur-Review die Freigabe erteilt hat.

## Roles

### Architect

Verantwortlich für:

- Architekturentscheidungen
- Sprint- und Task-Zuschnitt
- Definition von Verantwortungsgrenzen
- Review von Architektur, Code und Risiken
- Freigabe oder Ablehnung eines Tasks
- Pflege dauerhaft relevanter Architekturentscheidungen

### Implementation Agent

Verantwortlich für:

- Umsetzung ausschließlich des freigegebenen Tasks
- Einhaltung von Scope, AIDP und `AGENTS.md`
- Ausführung und Dokumentation der Quality Gates
- transparente Meldung von Risiken und Abweichungen
- Übergabe des Ergebnisses nach REVIEW

Der Implementation Agent finalisiert keine Architekturentscheidung ohne Freigabe.

### Project Owner

Verantwortlich für:

- Produktziele und Priorisierung
- Freigabe wesentlicher Richtungsentscheidungen
- Bewertung von Nutzen und Risiko
- finale Produktentscheidungen

### Shared Responsibility

Alle Rollen schützen gemeinsam:

- fachliche Konsistenz
- Security und Auditierbarkeit
- Wartbarkeit
- nachvollziehbare Änderungen
- eine einheitliche Enterprise-Architektur

## Bereinigte Review-Fragen

Die früheren fachlichen Review-Fragen sind durch den vorhandenen Architekturstand beantwortet:

- `DecisionResult` ist gemäß ADR-0001 die kanonische Single Source of Truth einer abgeschlossenen Decision.
- Execution Trace, Explainability und Decision Evidence sind gemäß ADR-0002, ADR-0003, ADR-0004 und ADR-0006 getrennte Verantwortungen.
- Der Python-Teststandard ist durch die bestehende Test Foundation und die Quality Gates definiert.
- Die initial erforderlichen Architekturentscheidungen liegen mit ADR-0001 bis ADR-0007 im Status `ACCEPTED` vor.
- Domain-, Application- und Presentation-Verantwortungen sind durch die kanonischen Architekturartefakte und ADR-0005 abgegrenzt.

## Verbleibende offene Punkte

Es bestehen keine ungeklärten fachlichen Architekturfragen vor First Live Intelligence. Verbleibende Punkte sind ausschließlich wie folgt klassifiziert:

### Governance

- TASK-0026 bleibt bis zu einer eigenen dokumentierten Architect-Entscheidung im REVIEW und ist nicht Bestandteil des fachlichen Architekturabschlusses.

### Runtime

- Konkreter Composition Root und Runtime-Zuschnitt für einen möglichen künftigen Reasoning Intelligence Layer.
- Konkrete Runtime-Einbindung späterer Ingestion-, Scanner- oder Live-Intelligence-Fähigkeiten.

Diese Punkte verändern keine bestehende fachliche Domain-, Aggregate- oder Contract-Grenze und werden erst in einem separat freigegebenen Runtime-Scope entschieden.

### Implementation

- Konkrete Zuordnung bestehender und künftiger Python-Module zu Application, Domain und Infrastructure.
- Technische Handler, APIs, DTOs, Persistenzadapter und Infrastrukturimplementierungen für freigegebene Use Cases.
- Produktcode-Umsetzung der dokumentierten fachlichen und taktischen Grenzen.

Diese Punkte sind Umsetzungsarbeit innerhalb der Baseline und keine fehlenden fachlichen Architekturartefakte.

## Baseline Governance

- ADR-0001 bis ADR-0007 bleiben `ACCEPTED`.
- Die Architekturartefakte unter `.ai/architecture/` bilden die freigegebene fachliche und taktische Architecture Baseline 1.0.
- Neue fachliche Artefakte werden nicht zur Vollständigkeit erfunden, sondern benötigen eine konkrete, nachweisbare Lücke und einen freigegebenen AIDP-Task.
- Diese Architecture Baseline erlaubt keine ungesteuerte Migration oder Scope-Erweiterung; jede Implementierung bleibt an ihren freigegebenen Task gebunden.
