# PredatorAI Engineering Rules

Version: 1.0

---

# Mission

PredatorAI ist eine Enterprise Cyber Reasoning Platform.

Der Fokus liegt auf:

- Explainable AI
- Cyber Reasoning
- Enterprise UX
- Skalierbarkeit
- Wartbarkeit
- Kleine Git-Diffs
- Hohe Codequalität

Arbeite wie ein Senior Software Engineer.

---

# Architecture

Backend ist die Single Source of Truth.

Das Frontend visualisiert Entscheidungen.

Keine Businesslogik im Frontend.

Keine künstlichen Daten.

Keine Demo-Implementierungen.

Keine Mock-Logik in produktiven Komponenten.

---

# Engineering Principles

Immer bevorzugen:

- Einfachheit
- Lesbarkeit
- Wiederverwendung
- Wartbarkeit
- Konsistenz

Vermeiden:

- doppelte Komponenten
- Copy & Paste
- unnötige Abstraktionen
- übermäßige Verschachtelung

---

# React

Verwende

- Functional Components
- TypeScript
- Hooks
- stabile React Keys

Nicht erlaubt

- key={index}, wenn eine stabile ID existiert
- unnötige Re-Renders
- Inline-Businesslogik

---

# TypeScript

Immer

- strikte Typisierung
- keine any
- keine unnötigen Type Assertions

Interfaces bevorzugen.

---

# Material UI

Bevorzugen

- Stack
- Box
- Paper
- Typography

Nicht ändern

- funktionierende spacing Props
- funktionierende Layouts

Nicht automatisch

- spacing → gap
- span → Typography
- div → Box

Nur wenn technisch notwendig.

---

# Dashboard

Dashboard zeigt ausschließlich

- Entscheidungen
- Risiken
- Zusammenhänge
- Explainability

Keine Datenfriedhöfe.

Keine Tabellen ohne Mehrwert.

---

# Decision Engine

Decision ist das zentrale Domänenmodell.

Nicht zurück zu

DecisionResponse

oder älteren Modellen.

Keine parallelen Modelle erzeugen.

---

# Workspaces

PredatorAI besitzt mehrere Enterprise Workspaces.

Executive

- KPIs
- Business Risk
- Executive Summary

CISO

- Governance
- Compliance
- Enterprise Risk

SOC Analyst

- Live Incidents
- Investigations
- Alerts

Threat Hunter

- Threat Hunting
- MITRE
- Pivoting

Incident Response

- Containment
- Timeline
- Evidence

Risk Manager

- Business Impact
- Priorisierung

Administrator

- Platform
- AI Models
- Integrationen

Keine Vermischung der Verantwortlichkeiten.

---

# Design

Enterprise.

Minimalistisch.

Dark First.

Keine verspielten Elemente.

Keine unnötigen Animationen.

Design folgt Funktion.

---

# Refactoring

Refactoring ist erlaubt wenn

- TypeScript Fehler
- Buildfehler
- Laufzeitfehler
- Sicherheitsproblem
- Architekturproblem
- Boilerplate automatisiert werden kann

Nicht erlaubt

- funktionierenden Code umschreiben
- kosmetische Änderungen
- große Git-Diffs ohne Nutzen

Immer den kleinsten sinnvollen Diff erzeugen.

---

# Code Reviews

Vor jeder Änderung prüfen

- existiert bereits eine Komponente?
- existiert bereits ein Hook?
- existiert bereits ein Typ?
- existiert bereits ein Workspace?

Keine Duplikate erzeugen.

---

# Imports

Nicht verwendete Imports entfernen.

Import-Reihenfolge konsistent halten.

Keine relativen Importketten wenn Alias existieren.

---

# Naming

Klar.

Kurz.

Beschreibend.

Keine Abkürzungen ohne Nutzen.

---

# Performance

Keine unnötigen Re-Renders.

Keine unnötigen Objekte.

Keine unnötigen Arrays.

Keine unnötigen Berechnungen.

---

# Git

Keine großflächigen Änderungen.

Keine Formatierungs-Commits.

Keine Datei löschen ohne Prüfung.

Keine Datei verschieben ohne Prüfung.

---

# Workflow

Nach jeder Änderung

cd frontend

npx tsc --noEmit

Falls Fehler

- beheben
- erneut Typecheck

Erst Exit Code 0 gilt als abgeschlossen.

---

# Autonomy

Arbeite selbstständig.

Treffe offensichtliche Entscheidungen eigenständig.

Frage nur wenn

- Architektur betroffen
- Datenmodell betroffen
- Datei löschen
- Breaking Change
- mehrere technisch gleichwertige Lösungen existieren

Ansonsten

Implementieren.

Typecheck.

Beheben.

Erneut testen.

---

# Abschlussbericht

Immer ausgeben

- Geänderte Dateien
- Warum geändert
- TypeScript Ergebnis
- Risiken
- Empfehlungen
- Nächster sinnvoller Schritt

---

# Quality Goal

Schreibe Code, den ein Enterprise-Team
auch in zwei Jahren noch gerne wartet.