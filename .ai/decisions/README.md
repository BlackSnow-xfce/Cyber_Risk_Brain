# PredatorAI Architecture Decision Records

## Zweck

Dieses Verzeichnis enthält dauerhaft relevante Architecture Decision Records (ADRs) für PredatorAI v3.

Ein ADR dokumentiert eine einzelne, konkrete Architekturentscheidung einschließlich Kontext, Alternativen und Konsequenzen. ADRs ergänzen die Leitplanken aus `ARCHITECTURE.md`; sie ersetzen weder die Architecture Charter noch die Implementierungsregeln aus `AGENTS.md`.

ADRs schaffen Nachvollziehbarkeit darüber:

- welches Architekturproblem bestand,
- welche Entscheidung getroffen wurde,
- warum diese Entscheidung getroffen wurde,
- welche Alternativen geprüft wurden,
- und welche positiven sowie negativen Konsequenzen akzeptiert werden.

## Geltungsbereich

Ein ADR ist erforderlich, wenn eine Entscheidung mindestens eine der folgenden Eigenschaften besitzt:

- sie verändert Verantwortungs- oder Layergrenzen,
- sie legt ein kanonisches Domainmodell oder einen Systemvertrag fest,
- sie beeinflusst die Abhängigkeitsrichtung,
- sie führt einen neuen Architekturmechanismus oder Composition Root ein,
- sie betrifft mehrere Module, Workspaces oder Services dauerhaft,
- sie ersetzt eine zuvor akzeptierte Architekturentscheidung,
- sie hat wesentliche Auswirkungen auf Security, Auditierbarkeit, Skalierbarkeit oder Betrieb.

Kein ADR ist erforderlich für:

- rein lokale Implementierungsdetails,
- Fehlerkorrekturen ohne Architekturwirkung,
- kosmetische Änderungen,
- kurzfristige Untersuchungen ohne Entscheidung,
- oder Task-Ergebnisse, die ausschließlich eine bereits akzeptierte Entscheidung umsetzen.

Im Zweifel entscheidet der Architect, ob ein ADR notwendig ist.

## Beziehung zu AIDP

Jeder ADR wird über einen eigenen AIDP-Task erstellt oder geändert.

Dabei gilt:

1. Der Architect definiert Ziel, Scope und Review-Kriterien.
2. Der ADR wird zunächst mit Status `PROPOSED` erstellt.
3. Der Implementation Agent dokumentiert ausschließlich die freigegebene Entscheidungsvorlage.
4. Der ADR und der zugehörige Task wechseln zur Architekturprüfung nach `REVIEW`.
5. Nur der Architect darf den ADR als `ACCEPTED`, `REJECTED` oder `SUPERSEDED` freigeben.
6. Die Implementierung einer Entscheidung erfolgt erst über nachgelagerte, separat freigegebene Tasks.

Ein ADR-Task darf keine verdeckte Produktimplementierung enthalten.

## Nummerierung und Dateinamen

Dateien verwenden folgendes Schema:

```text
ADR-NNNN-kurzer-beschreibender-titel.md
```

Regeln:

- `NNNN` ist eine vierstellige, fortlaufende Nummer.
- Nummern werden in aufsteigender Reihenfolge vergeben.
- Eine einmal verwendete Nummer wird niemals erneut vergeben.
- Der Titelteil verwendet ausschließlich Kleinbuchstaben, Ziffern und Bindestriche.
- Der Dateiname bleibt nach der erstmaligen Anlage stabil.
- Eine verworfene oder abgelöste Entscheidung behält ihre Datei und Nummer.
- Reservierte oder geplante Nummern sind erst vergeben, wenn die zugehörige ADR-Datei erstellt wurde.

Beispiel:

```text
ADR-0001-decision-result.md
```

## Status-Lifecycle

### PROPOSED

Die Entscheidung ist vollständig beschrieben und wartet auf Architekturprüfung. Sie ist noch nicht verbindlich und darf nicht als Freigabe für eine Implementierung interpretiert werden.

### ACCEPTED

Der Architect hat die Entscheidung freigegeben. Sie ist ab dem dokumentierten Entscheidungsdatum verbindlich, bis sie durch einen neuen ADR abgelöst wird.

### SUPERSEDED

Die Entscheidung wurde vollständig oder teilweise durch einen neueren, akzeptierten ADR ersetzt. Der ältere ADR bleibt unverändert als historischer Nachweis erhalten und referenziert den ablösenden ADR.

### REJECTED

Die vorgeschlagene Entscheidung wurde nach Prüfung nicht freigegeben. Sie bleibt als Nachweis des geprüften Vorschlags und seiner Ablehnungsgründe erhalten.

Der reguläre Lifecycle lautet:

```text
PROPOSED → ACCEPTED
PROPOSED → REJECTED
ACCEPTED → SUPERSEDED
```

## Pflichtabschnitte

Jeder ADR enthält mindestens folgende Struktur:

```markdown
# ADR-NNNN – Titel

## Status

PROPOSED

## Datum

YYYY-MM-DD

## Verantwortliche

Architect:
Implementation:

## Kontext

Welches konkrete Architekturproblem muss entschieden werden?

## Entscheidung

Welche einzelne Architekturentscheidung wird getroffen?

## Begründung

Warum ist diese Entscheidung für PredatorAI technisch angemessen?

## Konsequenzen

### Positiv

-

### Negativ

-

## Alternativen

Welche realistischen Alternativen wurden geprüft und warum nicht gewählt?

## Abgrenzung

Was ist ausdrücklich nicht Bestandteil dieser Entscheidung?

## Migration

Welche bestehenden Strukturen sind betroffen und wie kann die Entscheidung ohne Parallelarchitektur eingeführt werden?

## Qualitäts- und Sicherheitsauswirkungen

Welche Auswirkungen bestehen auf Tests, Security, Auditierbarkeit, Performance, Kompatibilität und Betrieb?

## Referenzen

- zugehörige AIDP-Tasks
- relevante Quelldateien
- relevante Architecture-Charter-Abschnitte
- ersetzte oder ergänzte ADRs

## Architektur-Review

Status:
Bemerkungen:
Freigabe:
```

Zusätzliche Abschnitte sind erlaubt, wenn sie für die konkrete Entscheidung notwendig sind. Pflichtabschnitte dürfen nicht entfernt werden.

## Änderungsregeln

### PROPOSED ADRs

Ein vorgeschlagener ADR darf innerhalb seines freigegebenen AIDP-Tasks überarbeitet werden. Änderungen müssen im Task-Ergebnis nachvollziehbar dokumentiert werden.

### ACCEPTED ADRs

Der fachliche Inhalt eines akzeptierten ADRs wird nicht rückwirkend umgeschrieben.

Nachträglich erlaubt sind ausschließlich:

- Korrekturen offensichtlicher Schreibfehler ohne Bedeutungsänderung,
- Ergänzungen fehlender Referenzen,
- und die Kennzeichnung als `SUPERSEDED` mit Referenz auf den ablösenden ADR.

Ändert sich die Entscheidung, wird ein neuer ADR mit neuer Nummer erstellt.

### REJECTED ADRs

Ein abgelehnter ADR wird nicht nachträglich in einen akzeptierten ADR umgewandelt. Ein fachlich überarbeiteter Vorschlag erhält eine neue Nummer und referenziert den abgelehnten ADR.

### SUPERSEDED ADRs

Ein abgelöster ADR bleibt erhalten. Der Status verweist eindeutig auf den neuen ADR; der neue ADR referenziert seinerseits die abgelöste Entscheidung.

## Referenzregeln

- ADRs referenzieren AIDP-Tasks über ihre vollständige Task-ID.
- Referenzen auf andere ADRs verwenden Nummer und Titel.
- Referenzen auf Quellcode verwenden Repository-relative Pfade.
- Geplante, aber noch nicht erstellte ADRs dürfen nicht als akzeptierte Grundlage zitiert werden.
- Eine Implementierung darf sich nur auf `ACCEPTED` ADRs als verbindliche Architekturentscheidung berufen.
- Widersprüche zwischen akzeptierten ADRs müssen durch einen neuen ADR aufgelöst werden.
- Bei einem Widerspruch zu `AGENTS.md` gilt `AGENTS.md`, bis der Konflikt ausdrücklich durch den Architect geklärt wurde.

## ADR-Index

### Accepted

| ADR | Titel | Status |
|---|---|---|
| [ADR-0001](ADR-0001-decision-result.md) | DecisionResult as Canonical Decision Contract | ACCEPTED |
| [ADR-0002](ADR-0002-execution-trace.md) | Canonical Execution Trace Contract | ACCEPTED |
| [ADR-0003](ADR-0003-explainability-projection.md) | Canonical Explainability Projection Contract | ACCEPTED |
| [ADR-0004](ADR-0004-explainability-completeness.md) | Explainability Completeness Contract | ACCEPTED |
| [ADR-0005](ADR-0005-mission-console-workspace-architecture.md) | Mission Console Workspace Architecture | ACCEPTED |
| [ADR-0006](ADR-0006-decision-evidence-architecture.md) | Decision Evidence Architecture | ACCEPTED |
| [ADR-0007](ADR-0007-domain-integration-principles.md) | Domain Integration Principles | ACCEPTED |
| [ADR-0008](ADR-0008-decision-lifecycle-human-governance.md) | Decision Lifecycle & Human Decision Governance | ACCEPTED |
| [ADR-0009](ADR-0009-security-incident-context-domain-ownership.md) | Security Incident Context & Domain Ownership | ACCEPTED |

### Proposed

Noch keine ADRs.

### Superseded

Noch keine ADRs.

### Rejected

Noch keine ADRs.

### Planned

Noch keine ADRs.

`PLANNED` ist kein ADR-Status. Geplante Einträge dienen nur der Sprintplanung. Ein Eintrag wechselt erst mit Erstellung einer eigenen ADR-Datei in den Status `PROPOSED`.

## Governance

- Der Architect verantwortet Statusentscheidungen und fachliche Freigaben.
- Der Implementation Agent hält Scope und Dokumentationsstruktur ein.
- Der Project Owner entscheidet über wesentliche Produkt- und Prioritätsauswirkungen.
- Der Index wird bei jeder Erstellung, Annahme, Ablehnung oder Ablösung eines ADRs im selben freigegebenen AIDP-Task aktualisiert.
- Fehlende Implementierung bedeutet nicht, dass ein akzeptierter ADR ungültig ist; der Umsetzungsstatus wird über AIDP-Tasks verfolgt.
- Ein ADR dokumentiert Architektur. Er ersetzt weder Tests noch Implementierungs- oder Betriebsdokumentation.
