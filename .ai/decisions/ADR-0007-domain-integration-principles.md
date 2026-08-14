# ADR-0007 – Domain Integration Principles

## Status

ACCEPTED

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI besitzt mehrere klar abgegrenzte fachliche Domänen. ADR-0001 bis ADR-0006 sichern bereits zentrale Verträge für DecisionResult, Execution Trace, Explainability, Explainability Completeness, Workspace-Architektur und Decision Evidence. Diese Entscheidungen schützen einzelne fachliche Wahrheiten und ihre Projektionen, definieren aber noch keine übergreifenden Grundsätze dafür, wie unterschiedliche Domänen fachlich zusammenarbeiten dürfen.

Die Architekturarbeit aus TASK-0031 bis TASK-0033 konkretisiert diese Lücke:

* TASK-0031 beschreibt Aggregate als domäneninterne Konsistenzgrenzen.
* TASK-0032 beschreibt gerichtete fachliche Beziehungen zwischen Aggregaten unterschiedlicher Domänen.
* TASK-0033 ordnet die daraus abgeleiteten Domain-Abhängigkeiten in eine azyklische Layer-Richtung ein und verbietet unbegründete Rückreferenzen.

Ohne verbindliche Integrationsprinzipien könnten spätere Lösungen interne Modelle einer autoritativen Domäne direkt verwenden, fachliche Daten außerhalb ihrer Owner-Domäne verändern, Aggregate über Domain Boundaries ausdehnen oder parallele Wahrheiten erzeugen. Solche Kopplung würde die kanonischen Verträge aus ADR-0001 bis ADR-0006 schwächen und Änderungen an einer Domäne unkontrolliert auf andere Domänen übertragen.

Es muss deshalb entschieden werden, welche fachlichen Leitplanken jede spätere Domain-Integration unabhängig von ihrer technischen Realisierung einhalten muss.

## Entscheidung

PredatorAI verwendet verbindliche **Domain Integration Principles** für jede fachliche Zusammenarbeit zwischen unterschiedlichen Domänen.

### 1. Exklusive Domain Ownership

Jeder fachliche Gegenstand besitzt genau eine autoritative Owner-Domäne. Ownership endet an der Domain Boundary und wird durch Referenz, Nutzung, Ableitung oder Darstellung nicht übertragen. Gemeinsame oder konkurrierende Ownership ist unzulässig.

### 2. Integration nur über definierte fachliche Verträge

Eine Domain darf eine andere Domain nur über einen ausdrücklich definierten fachlichen Integrationsvertrag nutzen. Ein solcher Vertrag beschreibt mindestens fachlichen Zweck, zulässige Richtung, Eigentümer und Konsument sowie die Bedeutung der bereitgestellten fachlichen Aussage. Die konkrete Ausgestaltung dieser Verträge ist nicht Bestandteil dieses ADRs.

### 3. Aggregate bleiben innerhalb ihrer Domain Boundary

Ein Aggregate gehört vollständig zu genau einer Domain. Aggregate Roots und enthaltene Entities dürfen keine gemeinsame Konsistenzgrenze über Domain Boundaries bilden. Domänenübergreifende Zusammenarbeit erweitert oder verschmilzt keine Aggregate.

### 4. Konsumenten bleiben von internen Modellen entkoppelt

Eine konsumierende Domain darf nicht von den internen Entity-, Value-Object-, Aggregate- oder Lifecycle-Strukturen der autoritativen Domain abhängig werden. Sie nutzt ausschließlich die fachliche Bedeutung des freigegebenen Vertrags. Interne Änderungen der Owner-Domäne dürfen keine neue fachliche Wahrheit beim Konsumenten erzwingen.

### 5. Abhängigkeiten folgen der freigegebenen Domain-Richtung

Fachliche Integration ist ausschließlich in einer gemäß TASK-0033 erlaubten Richtung zulässig. Die konsumierende Source Domain hängt von der autoritativen Target Domain ab. Rückreferenzen gegen die Domain-Layer, wechselseitige fachliche Abhängigkeiten und unbegründete Peer-Abhängigkeiten sind unzulässig.

### 6. Änderungen erfolgen ausschließlich durch den fachlichen Owner

Nur die Owner-Domäne darf ihre autoritativen fachlichen Daten und deren Bedeutung verändern. Ein Konsument darf gelesene, referenzierte oder abgeleitete Informationen nicht als Änderung der Target-Domain behandeln. Benötigt der Konsument eine eigene fachliche Aussage, verantwortet er diese innerhalb seiner eigenen Domain Boundary und hält die Herkunft eindeutig getrennt.

### 7. Keine parallele fachliche Wahrheit

Integration darf kanonische Daten nicht als zweite autoritative Quelle duplizieren. Lokale Darstellung, fachliche Ableitung oder temporäre Nutzung begründen keine neue Ownership. Bei widersprüchlichen Aussagen bleibt die Owner-Domäne autoritativ.

### 8. Read Models und Audit-Artefakte bleiben abgeleitet

Explainability bleibt gemäß ADR-0003 und ADR-0004 ein read-only Application Read Model. Execution Trace bleibt gemäß ADR-0002 ein Application-/Audit-Artefakt. Beide dürfen fachliche Integrationen sichtbar oder nachvollziehbar machen, aber weder Domain Ownership noch einen Integrationsvertrag ersetzen.

### 9. Decision und Evidence behalten ihre kanonischen Grenzen

`DecisionResult` bleibt gemäß ADR-0001 das einzige kanonische Ergebnis einer abgeschlossenen Decision. Decision Evidence bleibt gemäß ADR-0006 unveränderlicher, provenance-pflichtiger Nachweis. Domain-Integration darf weder Decisions aus Projektionen rekonstruieren noch Evidence nachträglich aus einer gewünschten Decision plausibilisieren.

## Begründung

Die Prinzipien bewahren die bereits festgelegten kanonischen Wahrheiten, während PredatorAI fachlich über mehrere Domänen wachsen kann. Exklusive Ownership macht eindeutig, wo eine fachliche Aussage geändert werden darf. Vertraglich begrenzte Nutzung verhindert, dass interne Modelle zur versteckten Plattformkopplung werden. Domäneninterne Aggregate-Grenzen halten Konsistenz lokal und vermeiden gemeinsam veränderliche Cross-Domain-Zustände.

Die gerichteten Abhängigkeiten aus TASK-0033 ermöglichen eine azyklische fachliche Architektur. Eine konsumierende Domain kann autoritative Aussagen verwenden, ohne die Target-Domain von sich abhängig zu machen. Dadurch bleiben fachliche Erweiterungen lokal bewertbar und die Herkunft einer Aussage nachvollziehbar.

Diese Entscheidung ergänzt ADR-0001 bis ADR-0006, ohne deren Verträge zu verändern:

* ADR-0001 schützt `DecisionResult` als kanonische Decision-Wahrheit.
* ADR-0002 trennt Execution Trace von Domain Ownership.
* ADR-0003 und ADR-0004 halten Explainability abgeleitet und read-only.
* ADR-0005 hält Workspaces als rollenbezogene Presentation-Grenzen außerhalb fachlicher Ownership.
* ADR-0006 schützt Evidence-Ownership, Provenance und gerichtete Ableitung.

## Konsequenzen

### Positiv

* Fachliche Kopplung zwischen Domänen wird reduziert und explizit kontrollierbar.
* Ownership und Änderungsverantwortung bleiben eindeutig.
* Aggregate können innerhalb ihrer Domain Boundary unabhängig weiterentwickelt werden.
* Konsumenten bleiben gegenüber internen Modellen der Owner-Domäne entkoppelt.
* Neue Domänen und Verbraucher lassen sich ergänzen, ohne bestehende fachliche Wahrheiten zu duplizieren.
* Azyklische Abhängigkeiten verbessern Verständlichkeit, Änderbarkeit und Fehlerisolation.
* Ownership, Herkunft und erlaubte Nutzung werden besser auditierbar.
* Decision-, Evidence- und Explainability-Verträge bleiben über Domänengrenzen konsistent.

### Negativ

* Jede neue fachliche Integration benötigt zusätzliche Architektur- und Vertragsdokumentation.
* Änderungen an einer fachlichen Aussage erfordern eine bewusste Prüfung betroffener Verträge und Konsumenten.
* Direkte Wiederverwendung interner Domainmodelle ist ausgeschlossen, auch wenn sie kurzfristig einfacher erscheinen würde.
* Strikte Richtungsregeln können zusätzliche fachliche Projektionen oder Übersetzungen erfordern; deren konkrete Form bleibt separat zu entscheiden.
* Architecture Review und Governance-Aufwand steigen mit der Zahl der Domain-Integrationen.

## Alternativen

### Direkter Zugriff auf interne Domainmodelle

Konsumenten könnten Entities oder Aggregate einer anderen Domain unmittelbar verwenden. Diese Alternative wird verworfen, weil interne Änderungen dadurch zu domänenübergreifenden Breaking Changes würden und Ownership unklar wäre.

### Gemeinsame Cross-Domain-Aggregate

Mehrere Domains könnten eine gemeinsame Konsistenzgrenze besitzen. Diese Alternative wird verworfen, weil sie Domain Boundaries aufhebt, gemeinsame Ownership erzeugt und die in TASK-0031 definierten Aggregate-Grenzen verletzt.

### Gemeinsame kanonische Plattformmodelle für alle Domains

Alle Domains könnten dieselben universellen fachlichen Modelle verwenden. Diese Alternative wird verworfen, weil unterschiedliche Verantwortlichkeiten in mehrdeutige Universalmodelle zusammenfallen und parallele Interpretationen derselben Daten entstehen würden.

### Unbeschränkte bidirektionale Domain-Abhängigkeiten

Domains könnten sich gegenseitig fachlich referenzieren und verändern. Diese Alternative wird verworfen, weil sie Zyklen, Rückreferenzen und unklare Änderungsverantwortung erzeugt und TASK-0033 widerspricht.

### Technischen Mechanismus vor fachlichem Vertrag festlegen

Die Integration könnte zuerst über eine konkrete Kommunikationstechnologie definiert werden. Diese Alternative wird verworfen, weil ein technischer Mechanismus weder Ownership noch fachliche Bedeutung oder zulässige Abhängigkeitsrichtung entscheidet.

## Abgrenzung

Dieser ADR definiert keine konkreten Domain-Integrationsverträge und keine Vertragsfelder. Er entscheidet weder REST noch GraphQL, APIs, DTOs, Events, Kafka, RabbitMQ, Messaging, Commands, Queries, Services, Repositorys, Persistenz, Datenbanken, Serialisierung, Schemas, Netzwerkkommunikation, Protokolle oder technische Konsistenzmechanismen.

Er führt keinen Anti-Corruption Layer ein, definiert keine Produktimplementierung, verändert keine Domainmodelle und erteilt keine Freigabe für Produktcode. Bestehende ADRs und die Architekturartefakte aus TASK-0031 bis TASK-0033 werden nicht verändert.

## Migration

Dieser ADR verändert kein Laufzeitverhalten und führt keine Migration aus. Nach einer Annahme gelten folgende architektonische Leitplanken für separat freigegebene Folgearbeit:

1. Bestehende und geplante Domain-Integrationen werden gegen Owner, Konsument und erlaubte Abhängigkeitsrichtung eingeordnet.
2. Für jede benötigte Integration wird ein eigener fachlicher Vertrag dokumentiert, ohne interne Modelle als öffentlichen Vertrag zu verwenden.
3. Bestehende direkte Kopplungen werden nur über separat freigegebene Tasks bewertet und schrittweise abgelöst.
4. Eine Umstellung darf keine parallele fachliche Wahrheit oder zweite Integrationsarchitektur als Zielzustand erzeugen.
5. Technische Realisierung, Kompatibilität und Übergangsstrategie werden erst nach Freigabe der jeweiligen fachlichen Verträge entschieden.

Bis ADR-0007 akzeptiert ist, stellt dieser Vorschlag keine Implementierungsfreigabe dar.

## Qualitäts- und Sicherheitsauswirkungen

### Wartbarkeit und Erweiterbarkeit

Lokale Ownership und vertragliche Entkopplung begrenzen die Auswirkungen fachlicher Änderungen. Neue Verbraucher müssen eine vorhandene autoritative Bedeutung respektieren, statt interne Modelle zu übernehmen. Der zusätzliche Dokumentationsaufwand ist Teil der Architekturqualität.

### Security und Autorisierung

Fachliche Nutzungsberechtigung ist keine Zugriffsfreigabe. Eine erlaubte Domain-Abhängigkeit hebt Autorisierung, Datenminimierung oder Vertraulichkeit nicht auf. Dieser ADR definiert keine Zugriffstechnik und keine Autorisierungsimplementierung.

### Auditierbarkeit

Eindeutiger Owner, gerichtete Abhängigkeit und getrennte Änderungsverantwortung ermöglichen die Nachvollziehbarkeit, wo eine fachliche Aussage entstand und wer sie ändern durfte. Read Models oder Konsumenten dürfen diese Herkunft nicht verschleiern.

### Performance und Betrieb

Der ADR legt keine Laufzeit- oder Kommunikationsform fest und verursacht selbst keine Performance- oder Betriebsänderung. Spätere technische Entscheidungen dürfen die fachlichen Grenzen nicht aus Optimierungsgründen umgehen.

### Kompatibilität

Bestehende Produktverträge bleiben unverändert. Änderungen an freigegebenen fachlichen Integrationsverträgen benötigen später eine eigene Kompatibilitätsbetrachtung. Dieser ADR selbst erzeugt keinen Breaking Change.

## Referenzen

* AIDP TASK-0034
* TASK-0031 – Define Aggregate Boundaries
* TASK-0032 – Define Cross-Domain Relationships
* TASK-0033 – Define Domain Dependency Rules
* `AGENTS.md`
* `ARCHITECTURE.md`
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `.ai/architecture/DOMAIN-DEPENDENCIES.md`
* ADR-0001 – DecisionResult as Canonical Decision Contract
* ADR-0002 – Canonical Execution Trace Contract
* ADR-0003 – Canonical Explainability Projection Contract
* ADR-0004 – Explainability Completeness Contract
* ADR-0005 – Mission Console Workspace Architecture
* ADR-0006 – Decision Evidence Architecture

## Architektur-Review

Status: APPROVED  
Bemerkungen: Architecture Review mit `PASS` abgeschlossen. ADR-0007 erfüllt den freigegebenen Scope vollständig, ist strukturell vollständig, fachlich konsistent zu ADR-0001 bis ADR-0006 und enthält keine widersprüchlichen oder technischen Implementierungsentscheidungen. Die Prinzipien sichern exklusive Domain Ownership, domäneninterne Aggregate-Grenzen und gerichtete fachliche Abhängigkeiten.  
Freigabe: Architect, 2026-08-05
