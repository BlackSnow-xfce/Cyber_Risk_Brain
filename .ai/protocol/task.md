# AIDP Task Protocol

## Zweck

Jeder Implementierungsauftrag wird als eigenständiger Task dokumentiert.

Ein Task besitzt einen vollständigen Lebenszyklus und darf ausschließlich gemäß diesem Protokoll bearbeitet werden.

---

## Status

READY

Der Task ist freigegeben und darf begonnen werden.

IN_PROGRESS

Der Task wird aktuell bearbeitet.

REVIEW

Die Implementierung ist abgeschlossen und wartet auf Architekturprüfung.

DONE

Der Task wurde erfolgreich geprüft und abgeschlossen.

REJECTED

Der Task wurde nicht freigegeben und muss überarbeitet werden.

---

## Pflichtfelder

Jeder Task muss mindestens enthalten:

* Task-ID
* Sprint
* Phase
* Verantwortlicher
* Status
* Ziel
* Betroffene Dateien
* Regeln
* Abschlusskriterien

---

## Regeln

Ein Task beschreibt ausschließlich einen logisch zusammenhängenden Arbeitsschritt.

Ein Task darf niemals mehrere unabhängige Features enthalten.

Nicht beauftragte Änderungen sind untersagt.

Architekturentscheidungen dürfen ausschließlich durch den Architect erfolgen.

---

## Abschluss

Ein Task gilt erst dann als abgeschlossen, wenn

* die Implementierung beendet wurde,
* alle vorgeschriebenen Prüfungen erfolgreich waren,
* der Architect den Task freigegeben hat.

Erst danach darf der Status auf DONE wechseln.

---

## Pflichtprüfungen

Sofern nicht ausdrücklich anders angegeben:

* npm run typecheck
* Browserprüfung bei UI-Änderungen

---

## Ausgabe des Implementation Agent

Nach Abschluss muss mindestens dokumentiert werden:

* geänderte Dateien
* ausgeführte Prüfungen
* Ergebnis der Prüfungen
* Besonderheiten
* offene Risiken
