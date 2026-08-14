# PredatorAI AI Development Channel

## Zweck

Dieses Verzeichnis ist der gemeinsame, versionskontrollierte Kommunikations- und Übergabekanal zwischen den am PredatorAI-Projekt beteiligten AI-Agenten.

Die bestehende Datei `AGENTS.md` im Projektroot bleibt die verbindliche Grundlage für Implementierungsregeln und Repository-Verhalten.

## Rollen

### ChatGPT – Architecture and Review

Verantwortlich für:

* Architekturentscheidungen
* Sprintplanung
* Definition klar abgegrenzter Implementierungsaufträge
* Prüfung der Ergebnisse
* Dokumentation wichtiger Entscheidungen
* Freigabe des nächsten Arbeitsschritts

### Codex – Implementation

Verantwortlich für:

* Umsetzung des aktuell freigegebenen Tasks
* Änderungen ausschließlich innerhalb des definierten Scopes
* Einhaltung der Regeln aus `AGENTS.md`
* Ausführung der vorgeschriebenen Prüfungen
* Dokumentation des Umsetzungsergebnisses
* Übergabe zur Architekturprüfung

### User – Project Owner

Verantwortlich für:

* Zielsetzung und Priorisierung
* Freigabe von Architektur und Umsetzung
* Kontrolle der tatsächlichen Änderungen
* finale Produktentscheidungen

## Grundprinzipien

* Eine Datei nach der anderen
* Vollständige Dateien statt Snippets
* Keine nicht beauftragten Änderungen
* Keine parallelen Architekturen
* Keine Businesslogik im Frontend
* Backend bleibt Single Source of Truth
* Architekturqualität hat Vorrang vor Geschwindigkeit
* Nach jeder Codeänderung wird `npm run typecheck` ausgeführt
* UI-relevante Änderungen werden zusätzlich im Browser geprüft
* Jeder Task besitzt einen eindeutigen Status und eine nachvollziehbare Übergabe

## Verzeichnisübersicht

### context

Enthält den aktuellen Projekt-, Architektur- und Entwicklungsstatus.

### sprints

Enthält die Ziele, Phasen und Ergebnisse der aktiven und abgeschlossenen Sprints.

### tasks

Enthält einzelne Implementierungsaufträge, sortiert nach ihrem Lifecycle:

* `ready`
* `in-progress`
* `review`
* `done`

### reviews

Enthält Architektur-, Code- und UX-Reviews abgeschlossener Implementierungen.

### decisions

Enthält dauerhaft relevante Architekturentscheidungen.

### protocol

Definiert Task-Lifecycle, Übergaben, Reviews und Statusänderungen.

## Task-Lifecycle

ready
↓
in-progress
↓
review
↓
done

Ein Task darf erst begonnen werden, wenn er unter `tasks/ready` liegt.

Nach der Implementierung wird er nicht direkt abgeschlossen, sondern zur Prüfung nach `tasks/review` übergeben.

Erst nach erfolgreichem Review wird er unter `tasks/done` abgelegt.

## Aktueller Einsatz

Der AI Development Channel wird ab Sprint 12 für die Weiterentwicklung von PredatorAI v3 verwendet.

Der erste fachliche Einsatz ist Sprint 12 Phase 1:

Reasoning Orchestration and Reasoning Session Lifecycle.
