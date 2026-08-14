# PredatorAI v3 – Aggregate Relationships

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument definiert ausschließlich die kanonischen fachlichen Beziehungen zwischen Aggregaten unterschiedlicher PredatorAI-Domänen. Es beschreibt, welche fachliche Grenze eine autoritative Aussage einer anderen Grenze referenziert, nutzt oder für ihren eigenen Zweck benötigt.

Es beschreibt keine APIs, Commands, Queries, Events, Services, Repositorys, Persistenz, Datenflüsse, Netzwerkkommunikation oder Implementierung.

## Begriffe

* **Source Domain / Source Aggregate:** die fachlich nutzende oder abhängige Grenze.
* **Target Domain / Target Aggregate:** die fachlich autoritative Grenze. Ihre Ownership bleibt unverändert.
* **Referenz:** Die Source benennt einen autoritativen fachlichen Gegenstand des Target, ohne ihn zu besitzen.
* **Nutzung:** Die Source verwendet eine autoritative Aussage des Target, ohne deren Bedeutung oder Lebenslauf zu übernehmen.
* **Fachliche Abhängigkeit:** Die Source kann ihren eigenen fachlichen Zweck ohne eine gültige Aussage des Target nicht vollständig erfüllen.
* **Richtung:** immer `Source Aggregate → Target Aggregate`; der Pfeil beschreibt keine technische Kommunikation.

## Architekturregeln

1. Eine Beziehung überträgt weder Entity- noch Value-Object- oder Aggregate-Ownership.
2. Source und Target bleiben innerhalb ihrer bestehenden Domain- und Aggregate-Grenzen.
3. Nur fachlich notwendige oder durch die bestehenden Architekturartefakte ausdrücklich begründete Beziehungen werden kanonisch dokumentiert.
4. Eine nicht dokumentierte mögliche Nutzung ist keine freigegebene kanonische Beziehung.
5. Beziehungen innerhalb eines Aggregates oder zwischen Aggregaten derselben Domäne sind nicht Bestandteil dieses Dokuments.
6. Die fachliche Abhängigkeitsrichtung ist azyklisch. Rückwärtsgerichtete Mutation des Target ist unzulässig.
7. Mehrere Beziehungen zwischen denselben Domänen bleiben getrennt, wenn unterschiedliche Aggregate oder fachliche Zwecke betroffen sind.

## Canonical Cross-Domain Relationships

| ID | Source Domain | Target Domain | Source Aggregate | Target Aggregate | Fachlicher Zweck | Begründung der Abhängigkeit | Art |
|---|---|---|---|---|---|---|---|
| REL-001 | Enterprise Context | Data Integration | Asset Context Aggregate | Integration Aggregate | Autoritative Quellherkunft eines aufgenommenen Asset-Kontexts nutzen. | Der Asset-Kontext darf eine kontrolliert aufgenommene externe Herkunft nutzen, ohne Integrations-Lineage zu besitzen. | Nutzung |
| REL-002 | Threat Intelligence | Data Integration | Threat Actor Aggregate | Integration Aggregate | Herkunft aufgenommener Threat-Actor-Informationen nutzen. | Die Intelligence-Aussage bleibt nur nachvollziehbar, wenn ihre kontrollierte externe Aufnahme fachlich zuordenbar ist. | Nutzung |
| REL-003 | Threat Intelligence | Data Integration | Threat Technique Aggregate | Integration Aggregate | Herkunft aufgenommener Threat-Technique-Informationen nutzen. | Die Technique bleibt Intelligence-Eigentum; die technische Quellzuordnung verbleibt beim Integration Aggregate. | Nutzung |
| REL-004 | Threat Intelligence | Data Integration | Threat Indicator Aggregate | Integration Aggregate | Herkunft aufgenommener Threat-Indicator-Informationen nutzen. | Ein kuratierter Indicator darf seine technische Aufnahme nachvollziehen, ohne die Data-Integration-Ownership zu übernehmen. | Nutzung |
| REL-005 | Threat Intelligence | Data Integration | Threat Campaign Aggregate | Integration Aggregate | Herkunft aufgenommener Threat-Campaign-Informationen nutzen. | Die Campaign-Aussage und die technische Quellzuordnung besitzen getrennte fachliche Verantwortung. | Nutzung |
| REL-006 | Security Observation | Enterprise Context | Finding Aggregate | Asset Context Aggregate | Den schutzrelevanten Unternehmensgegenstand eines Finding benennen. | Ein Finding besitzt den Asset-Kontext nicht und muss dessen autoritative Identität referenzieren. | Referenz |
| REL-007 | Security Observation | Enterprise Context | Alert Aggregate | Asset Context Aggregate | Den schutzrelevanten Unternehmensgegenstand eines Alert benennen. | Ein Alert bleibt eine Beobachtung; der referenzierte Unternehmensgegenstand bleibt Eigentum von Enterprise Context. | Referenz |
| REL-008 | Security Observation | Enterprise Context | Exposure Aggregate | Asset Context Aggregate | Den schutzrelevanten Unternehmensgegenstand eines Exposure benennen. | Ein Exposure beschreibt einen Zustand, nicht die Identität oder Bedeutung des betroffenen Asset. | Referenz |
| REL-009 | Security Observation | Threat Intelligence | Finding Aggregate | Threat Indicator Aggregate | Autoritative Threat-Indicator-Aussagen zur fachlichen Kontextualisierung eines Finding nutzen. | Die Kontextualisierung darf Intelligence verwenden, ohne den Indicator umzudeuten oder zu besitzen. | Nutzung |
| REL-010 | Security Observation | Threat Intelligence | Alert Aggregate | Threat Indicator Aggregate | Autoritative Threat-Indicator-Aussagen zur fachlichen Kontextualisierung eines Alert nutzen. | Der Alert bleibt interne Beobachtung und der Indicator bleibt autoritative Threat Intelligence. | Nutzung |
| REL-011 | Security Observation | Threat Intelligence | Exposure Aggregate | Threat Indicator Aggregate | Autoritative Threat-Indicator-Aussagen zur fachlichen Kontextualisierung eines Exposure nutzen. | Die fachlichen Aussagen bleiben getrennt; die Nutzung erzeugt keine gemeinsame Ownership. | Nutzung |
| REL-012 | Threat Hunting | Security Observation | Hunt Aggregate | Finding Aggregate | Bestehende Findings als autoritative Untersuchungsgrundlage nutzen. | Ein Hunt darf Findings untersuchen, aber weder deren Aussage noch deren Lebenslauf übernehmen. | Nutzung |
| REL-013 | Threat Hunting | Security Observation | Hunt Aggregate | Alert Aggregate | Bestehende Alerts als autoritative Untersuchungsgrundlage nutzen. | Die proaktive Untersuchung benötigt beobachtete Hinweise, ohne daraus neue Alert-Ownership abzuleiten. | Nutzung |
| REL-014 | Threat Hunting | Threat Intelligence | Hunt Aggregate | Threat Indicator Aggregate | Kuratierte Indicators als fachliche Hunting-Grundlage nutzen. | Hunting benötigt autoritatives Bedrohungswissen, während dessen Ownership bei Threat Intelligence verbleibt. | Nutzung |
| REL-015 | Threat Hunting | Threat Intelligence | Hunt Aggregate | Threat Technique Aggregate | Autoritative Techniques zur Formulierung und Bewertung eines Hunts nutzen. | Der Hunt verwendet das kanonische Technique-Vokabular, definiert es aber nicht selbst. | Nutzung |
| REL-016 | Governance and Compliance | Enterprise Context | Governance Policy Aggregate | Organizational Unit Context Aggregate | Den fachlichen Geltungsbereich einer Governance Policy benennen. | Eine Policy besitzt Organisationsbereiche nicht und muss deren autoritative Identität referenzieren. | Referenz |
| REL-017 | Governance and Compliance | Enterprise Context | Compliance Requirement Aggregate | Business Service Context Aggregate | Den geschäftlichen Geltungsbereich einer Compliance Requirement benennen. | Die Anforderung benötigt autoritativen Business-Kontext, ohne einen Business Service zu besitzen. | Referenz |
| REL-018 | Governance and Compliance | Security Observation | Compliance Requirement Aggregate | Finding Aggregate | Autoritative Findings als fachliche Grundlage einer Compliance-Bewertung nutzen. | Compliance darf beobachtete Feststellungen bewerten, aber weder Finding-Ownership noch Security-Observation-Semantik übernehmen. | Nutzung |
| REL-019 | Decision Evidence | Security Observation | Evidence Aggregate | Finding Aggregate | Ein Finding als autoritative Quelle entscheidungsrelevanter Evidence nutzen. | Evidence benötigt eine überprüfbare Quellaussage; das ursprüngliche Finding verbleibt bei Security Observation. | Fachliche Abhängigkeit |
| REL-020 | Decision Evidence | Security Observation | Evidence Aggregate | Alert Aggregate | Einen Alert als autoritative Quelle entscheidungsrelevanter Evidence nutzen. | Die Evidence-Repräsentation muss auf die ursprüngliche Beobachtung zurückführbar bleiben. | Fachliche Abhängigkeit |
| REL-021 | Decision Evidence | Security Observation | Evidence Aggregate | Exposure Aggregate | Ein Exposure als autoritative Quelle entscheidungsrelevanter Evidence nutzen. | Evidence übernimmt die entscheidungsrelevante Nachweisrepräsentation, nicht den ursprünglichen Exposure-Lebenslauf. | Fachliche Abhängigkeit |
| REL-022 | Decision Evidence | Threat Intelligence | Evidence Aggregate | Threat Indicator Aggregate | Einen Threat Indicator als autoritative Quelle entscheidungsrelevanter Evidence nutzen. | Die Evidence muss ihre Intelligence-Herkunft bewahren, ohne den Indicator zu duplizieren. | Fachliche Abhängigkeit |
| REL-023 | Decision Evidence | Threat Hunting | Evidence Aggregate | Hunt Aggregate | Ein fachliches Hunt-Ergebnis als Quelle entscheidungsrelevanter Evidence nutzen. | Die Nachweisrepräsentation benötigt einen autoritativen Untersuchungskontext; Hunt-Ownership verbleibt bei Threat Hunting. | Fachliche Abhängigkeit |
| REL-024 | Decision Evidence | Governance and Compliance | Evidence Aggregate | Governance Policy Aggregate | Eine verbindliche Governance-Aussage als entscheidungsrelevante Evidence-Grundlage nutzen. | Der Nachweis muss die autoritative Policy-Bedeutung erhalten, ohne sie zu besitzen. | Fachliche Abhängigkeit |
| REL-025 | Cyber Decision | Decision Evidence | Decision Aggregate | Evidence Aggregate | Die überprüfbare Tatsachengrundlage einer Decision nutzen. | Eine kanonische Decision darf ihre fachliche Aussage ausschließlich auf autorisierte Evidence stützen; Evidence bleibt gemäß ADR-0006 getrennt verantwortlich. | Fachliche Abhängigkeit |
| REL-026 | Cyber Decision | Enterprise Context | Decision Aggregate | Business Service Context Aggregate | Autoritativen Business-Service-Kontext für die Decision nutzen. | Die Decision benötigt Unternehmensbedeutung, darf aber den Business Service weder definieren noch verändern. | Nutzung |
| REL-027 | Cyber Decision | Governance and Compliance | Decision Aggregate | Governance Policy Aggregate | Verbindliche Governance-Vorgaben bei der Decision nutzen. | Die Decision muss geltende Vorgaben respektieren, ohne Policy-Ownership zu übernehmen. | Nutzung |
| REL-028 | Incident Response | Security Observation | Security Incident Aggregate | Finding Aggregate | Autoritative Findings zur Vorfallskoordination nutzen. | Ein Security Incident koordiniert die Response, während das Finding eine eigenständige Beobachtung bleibt. | Nutzung |
| REL-029 | Incident Response | Enterprise Context | Security Incident Aggregate | Asset Context Aggregate | Betroffene schutzrelevante Unternehmensgegenstände referenzieren. | Incident Response besitzt keine Asset-Identität und muss den autoritativen Kontext bewahren. | Referenz |
| REL-030 | Incident Response | Decision Evidence | Security Incident Aggregate | Evidence Aggregate | Entscheidungsrelevante Nachweise zur koordinierten Response nutzen. | Die Response darf Evidence nutzen, ohne deren unveränderliche Nachweis-Ownership zu übernehmen. | Nutzung |
| REL-031 | Incident Response | Cyber Decision | Security Incident Aggregate | Decision Aggregate | Eine kanonische Decision als fachliche Handlungsgrundlage nutzen. | Incident Response koordiniert Maßnahmen, ändert aber weder Decision noch DecisionResult. | Nutzung |
| REL-032 | Enterprise Risk | Cyber Decision | Enterprise Risk Aggregate | Decision Aggregate | Kanonische Cyber-Decisions als Eingang der langfristigen Risikosteuerung nutzen. | Enterprise Risk darf DecisionResult auswerten, aber nicht als zweite Decision-Wahrheit fortschreiben. | Nutzung |
| REL-033 | Enterprise Risk | Enterprise Context | Enterprise Risk Aggregate | Business Service Context Aggregate | Den geschäftlich betroffenen Service eines Enterprise Risk referenzieren. | Die Risikosteuerung benötigt autoritativen Business-Kontext, besitzt aber keinen Business Service. | Referenz |
| REL-034 | Enterprise Risk | Governance and Compliance | Enterprise Risk Aggregate | Governance Policy Aggregate | Verbindliche Governance-Vorgaben in der Risikobehandlung nutzen. | Treatment und Acceptance müssen geltende Vorgaben berücksichtigen, ohne Governance-Ownership zu übernehmen. | Nutzung |
| REL-035 | Identity and Access | Enterprise Context | Principal Aggregate | Organizational Unit Context Aggregate | Den autoritativen organisatorischen Kontext eines Principal referenzieren. | Identity and Access besitzt keine Organizational Unit und muss deren fachliche Identität unverändert verwenden. | Referenz |
| REL-036 | Identity and Access | Enterprise Context | Authorization Rule Aggregate | Organizational Unit Context Aggregate | Den organisatorischen Geltungsbereich einer Autorisierungsregel referenzieren. | Eine Autorisierungsregel darf Organisationskontext begrenzen, aber nicht selbst definieren. | Referenz |
| REL-037 | Platform Operations | Identity and Access | Platform Configuration Aggregate | Authorization Rule Aggregate | Autoritative Zugriffsregeln für kontrollierte Konfigurationsverantwortung nutzen. | Plattformkonfiguration benötigt eine fachlich autorisierte Grenze, ohne Autorisierungsregeln zu besitzen. | Fachliche Abhängigkeit |
| REL-038 | Platform Operations | Identity and Access | Background Job Aggregate | Authorization Rule Aggregate | Autoritative Zugriffsregeln für kontrollierte betriebliche Verantwortung nutzen. | Der betriebliche Vorgang darf seine Autorisierungsgrenze nicht selbst definieren. | Fachliche Abhängigkeit |
| REL-039 | Platform Operations | Data Integration | Platform Service Aggregate | Integration Aggregate | Den autoritativen Integrationszustand im Plattformbetrieb nutzen. | Platform Operations überwacht den Betrieb, übernimmt aber weder Integrationsdefinition noch Quell-Lineage. | Nutzung |

## Abhängigkeitsrichtung

Die Beziehungen bilden folgende fachliche Schichtung. Die Darstellung zeigt nur die Richtung fachlicher Abhängigkeit und keine Verarbeitung oder Kommunikation:

```text
Platform Operations ───────► Identity and Access
        │
        └──────────────────► Data Integration

Identity and Access ───────► Enterprise Context ───────► Data Integration

Threat Intelligence ──────────────────────────────────► Data Integration

Security Observation ─────► Enterprise Context
        │
        └──────────────────► Threat Intelligence

Threat Hunting ────────────► Security Observation
        └──────────────────► Threat Intelligence

Governance and Compliance ─► Enterprise Context
        └──────────────────► Security Observation

Decision Evidence ─────────► Security Observation
        ├──────────────────► Threat Intelligence
        ├──────────────────► Threat Hunting
        └──────────────────► Governance and Compliance

Cyber Decision ────────────► Decision Evidence
        ├──────────────────► Enterprise Context
        └──────────────────► Governance and Compliance

Incident Response ─────────► Security Observation
        ├──────────────────► Enterprise Context
        ├──────────────────► Decision Evidence
        └──────────────────► Cyber Decision

Enterprise Risk ───────────► Cyber Decision
        ├──────────────────► Enterprise Context
        └──────────────────► Governance and Compliance
```

## Zyklusprüfung

Der dokumentierte fachliche Graph ist azyklisch. Keine Target-Grenze hängt über eine dokumentierte Rückrichtung wieder von ihrer Source ab.

Insbesondere werden potenzielle Rückkopplungen bewusst vermieden:

* Threat Hunting nutzt keine Decision Evidence; Evidence darf einen Hunt als autoritative Untersuchungsquelle nutzen.
* Decision Evidence nutzt keinen Security Incident; Incident Response darf Evidence zur Koordination nutzen.
* Cyber Decision verändert weder Evidence noch Enterprise Context oder Governance-Vorgaben.
* Enterprise Risk verändert keine zugrunde liegende Cyber Decision.
* Platform Operations besitzt weder Identity-and-Access- noch Data-Integration-Aussagen.

Eine fachliche Reaktion auf eine bestehende Aussage kann außerhalb der Target-Grenze einen neuen fachlichen Vorgang begründen. Sie ist keine rückwärtsgerichtete Mutation und wird in diesem Dokument nicht als Datenfluss modelliert.

## Ownership-Schutz

Für jede Beziehung bleibt das Target autoritativ. Die Source darf ausschließlich die dokumentierte fachliche Bedeutung verwenden. Sie darf das Target nicht kopieren, umdeuten, fortschreiben oder als eigene Wahrheit verwalten. Referenz, Nutzung und fachliche Abhängigkeit erweitern keine Aggregate-Grenze.

## Nicht Bestandteil

Dieses Dokument definiert keine APIs, DTOs, Commands, Queries, Domain Events, Messaging, Domain Services, Application Services, Repositorys, Persistenz, Datenbanken, Datenflüsse, Verarbeitungspipelines, Netzwerkkommunikation, Protokolle, Attribute, Referenzfelder, Kardinalitäten, Transaktionen, Module, Packages, Deployments oder Produktimplementierungen.

## Statische Konsistenzprüfung

* Alle 39 Beziehungen besitzen eindeutige IDs, Source und Target.
* Source und Target stammen aus dem bestehenden Domain- und Aggregate-Katalog.
* Jede Richtung verläuft von der nutzenden zur autoritativen Grenze.
* Jede Beziehung verwendet genau eine der Arten `Referenz`, `Nutzung` oder `Fachliche Abhängigkeit`.
* Keine Beziehung überschreitet oder verändert eine Aggregate- oder Domain-Ownership.
* Der fachliche Abhängigkeitsgraph ist azyklisch.
* Technische Kommunikation und Datenflüsse bleiben unmodelliert.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-OWNERSHIP-AND-RESPONSIBILITIES.md`
* `.ai/architecture/CANONICAL-ENTITIES.md`
* `.ai/architecture/CANONICAL-VALUE-OBJECTS.md`
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `ARCHITECTURE.md`
* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0003-explainability-projection.md`
* `.ai/decisions/ADR-0004-explainability-completeness.md`
* `.ai/decisions/ADR-0005-mission-console-workspace-architecture.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/tasks/done/TASK-0032.md`

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
