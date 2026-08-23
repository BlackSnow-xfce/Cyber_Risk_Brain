# ADR-0010 – LLM Trust Boundary and Independent Security Enforcement

## Status

ACCEPTED

## Datum

2026-08-19

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI wird künftig LLMs für erklärende oder unterstützende Aufgaben
verwenden. Ein LLM und jede von ihm erzeugte Ausgabe sind jedoch nicht als
Security Authority geeignet. Prompting, System Instructions und eine erwartete
Modellbefolgung sind keine belastbaren Sicherheitsgrenzen.

Ohne eine explizite Architekturentscheidung könnten LLM-Ausgaben als
Autorisierung, vertrauenswürdige Evidence oder Grundlage privilegierter
Aktionen fehlinterpretiert werden. Externe, abgerufene und nutzergelieferte
Inhalte müssen außerdem als Daten behandelt werden und dürfen durch ihre
Aufnahme in einen LLM-Kontext keine Instruction Authority erhalten.

## Entscheidung

PredatorAI behandelt jedes LLM und jede LLM-generierte Ausgabe als
**untrusted component**. Sicherheitsrelevante Entscheidungen und Kontrollen
werden unabhängig vom LLM durch serverseitige Domain-/Application-Boundaries
durchgesetzt.

### Sicherheitsinvarianten

* **SI-01:** LLM-Ausgabe ist niemals Autorisierung.
* **SI-02:** Nicht autorisierte Daten gelangen nicht in einen LLM-Kontext.
* **SI-03:** Retrieved Content und extern gelieferte Inhalte erhalten durch
  ihre Aufnahme in einen LLM-Kontext keine Instruction Authority.
* **SI-04:** Ein LLM führt keine privilegierten Aktionen direkt aus.
* **SI-05:** Tool-Ausführung unterliegt unabhängiger Autorisierung und
  Policy-Enforcement.
* **SI-06:** Secrets werden keinem LLM offengelegt, solange dies nicht durch
  eine zukünftige Security-Architekturentscheidung ausdrücklich freigegeben
  ist.
* **SI-07:** Sicherheitskontrollen bleiben wirksam, wenn das LLM fehlerhaft,
  böswillig oder erfolgreich prompt-injiziert ist.

Authentication und Authorization sind unabhängig vom LLM. Authorization findet
vor dem Zugriff auf geschützte Daten und vor Retrieval statt. Das LLM darf den
autorisierten Datenumfang weder bestimmen noch erweitern.

System Policy, Application Context, User Input, Retrieved Content,
Threat Intelligence und Tool Results bleiben semantisch unterscheidbar.
Externe Inhalte sind Daten, keine vertrauenswürdige Instruction Authority.
LLM-Ausgaben sind untrusted Vorschläge beziehungsweise Ergebnisse.

Privilegierte oder risikoreiche Aktionen benötigen unabhängiges Policy-
Enforcement und können Human-in-the-loop erfordern.

## Begründung

Die Entscheidung hält Backend- und Security-Ownership außerhalb des LLMs und
erhält die bestehende Single Source of Truth. Sie verhindert, dass ein Modell
durch Prompt-Injection, fehlerhafte Interpretation oder manipulierte externe
Inhalte Zugriff, Datenumfang oder Aktionserlaubnis erweitert.

## Konsequenzen

### Positiv

* Security Controls bleiben unabhängig vom Modellverhalten wirksam.
* Autorisierung und Datenzugriff behalten eine deterministische serverseitige
  Owner-Boundary.
* Externe Inhalte, User Input und Tool Results können sicher als untrusted
  Daten behandelt werden.
* Privilegierte Aktionen bleiben policy- und gegebenenfalls HITL-geschützt.

### Negativ

* Künftige LLM-Integrationen benötigen zusätzliche Context-, Retrieval- und
  Tool-Governance.
* Prompting allein reicht nicht als Sicherheitsmechanismus.
* Eine vollständige Provider-, DLP-, Output-Filtering- und Tool-Policy-
  Architektur ist noch offen.

## Alternativen

* **Prompt-basierte Security Enforcement:** abgelehnt; Prompts sind keine
  unabhängige Sicherheitsgrenze.
* **LLM-basierte Authorization:** abgelehnt; ein untrusted Modell darf keinen
  autorisierten Datenumfang festlegen.
* **Retrieve first, filter output later:** abgelehnt; nicht autorisierte Daten
  dürfen die LLM-Grenze bereits vorher nicht erreichen.
* **Direkte privilegierte LLM-to-Tool-Ausführung:** abgelehnt; Tool Execution
  benötigt eine unabhängige Authorization- und Policy-Boundary.

## Abgrenzung

Diese ADR definiert ausschließlich die LLM Trust Boundary und die
unabhängige Security Enforcement-Regel.

Nicht Bestandteil sind:

* RAG oder Retrieval-Implementierung;
* Agenten- oder Tool-Execution-Infrastruktur;
* Authorization- oder Identity-Infrastruktur;
* Output Filtering, DLP oder Provider Governance;
* neue LLM-Aufrufe;
* ein AIContext-Contract oder konkrete Produktintegration;
* SOAR-, Response- oder Containment-Ausführung.

## Migration

Neue LLM-Boundaries müssen Datenzugriff, Retrieval, Tool-Aufrufe und
privilegierte Aktionen durch unabhängige serverseitige Policies führen.
Bestehende kanonische Finding-, Asset-, Threat-Intelligence-, Evidence- und
Decision-Contracts bleiben unverändert und dürfen nicht durch LLM-Ausgaben
dupliziert oder überschrieben werden.

## Qualitäts- und Sicherheitsauswirkungen

Die ADR stärkt Prompt-Injection-Resilienz, Least Privilege und Auditierbarkeit.
Sie verlangt für spätere AI-Integrationen explizite Tests für untrusted Input,
Authorization-before-Retrieval, Tool-Policy und das Verhalten bei fehlerhaften
oder manipulierten Modellantworten. Es entsteht durch diese ADR keine neue
Runtime-Infrastruktur.

## Referenzen

* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/decisions/README.md`
* `AGENTS.md`

## Architektur-Review

Status: ACCEPTED  
Bemerkungen: LLMs und LLM-Ausgaben bleiben untrusted; alle sicherheitsrelevanten Kontrollen liegen unabhängig vom LLM.  
Freigabe: Architect / Product Owner, 2026-08-19
