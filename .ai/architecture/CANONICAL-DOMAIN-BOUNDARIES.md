# PredatorAI v3 – Canonical Domain Boundaries

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument definiert die kanonischen fachlichen Domänen von PredatorAI, ihren jeweiligen Zweck, ihre Ownership und ihre Grenzen. Es bildet die technologieunabhängige Grundlage für nachfolgende Architekturarbeit in Sprint 14B.

Die bestehenden Rollen-Workspaces wurden ausschließlich als Analysequelle verwendet. Ein Workspace ist gemäß ADR-0005 eine rollenbezogene Arbeits- und Präsentationsgrenze. Er konsumiert Fähigkeiten mehrerer Domänen, besitzt aber keine fachlichen Daten allein aufgrund ihrer Darstellung.

## Verbindliche Grundlagen

* Das Backend bleibt fachliche Single Source of Truth.
* Pro fachlichem Konzept existiert genau eine verantwortliche Domäne.
* ADR-0001 bis ADR-0006 bleiben unverändert verbindlich.
* `DecisionResult` bleibt das kanonische Ergebnis einer abgeschlossenen Decision.
* Decision Evidence bleibt unveränderlich und provenance-pflichtig.
* Explainability bleibt ein abgeleitetes, read-only Application Read Model.
* Der Execution Trace bleibt ein Application-/Audit-Artefakt und kein fachliches Domainmodell.
* Rollen, Navigation, Seiten und Mission Consoles begründen keine eigene Domain Ownership.

## Canonical Domains

| Domäne | Zweck | Besitzt kanonisch | Besitzt ausdrücklich nicht |
|---|---|---|---|
| Enterprise Context | Einheitlicher fachlicher Kontext des geschützten Unternehmens | Identität und fachliche Einordnung von Assets, Business Services, Organisationseinheiten, Crown Jewels, Kritikalität und deren fachlichen Beziehungen | technische Beobachtungen, Risiken, Entscheidungen, Berechtigungen |
| Security Observation | Autoritative Erfassung sicherheitsrelevanter Beobachtungen | Findings, Alerts, Exposures und normalisierte sicherheitsrelevante Zustände einschließlich Quellbezug und Beobachtungsstatus | Threat Intelligence, Hunt-Hypothesen, Incidents, Evidence-Snapshots, Entscheidungen |
| Threat Intelligence | Verwaltung bewerteter Informationen über Bedrohungsakteure, Techniken, Indikatoren und Kampagnen | Threat-Intelligence-Fakten, deren Herkunft, Gültigkeit und fachliche Beziehungen | unternehmensinterne Beobachtungen, Hunt-Lifecycle, Incident-Lifecycle, Entscheidungen |
| Threat Hunting | Steuerung proaktiver, hypothesen- und untersuchungsorientierter Hunts | Hunt, Hypothese, Untersuchungsabsicht, Suchkontext und Hunt-Lifecycle | Quelltelemetrie, Findings, Threat-Intelligence-Fakten, Incidents oder DecisionResult |
| Incident Response | Koordination eines bestätigten oder vermuteten Sicherheitsvorfalls über seinen Response-Lifecycle | Incident, Response-Phase, koordinierte Maßnahmen, betroffene Referenzen, Kommunikations- und Abschlussstatus | Findings, Evidence-Fakten, Asset-Stammdaten, Plattform-Jobs oder Enterprise-Risiken |
| Decision Evidence | Bereitstellung der überprüfbaren Tatsachengrundlage einer Decision | Unveränderliche, provenance-pflichtige Source und Derived Evidence gemäß ADR-0006 | Decision, Erklärung, Execution Trace oder ursprüngliche Quellobjekte |
| Cyber Decision | Erzeugung und Besitz der kanonischen fachlichen Cyber-Entscheidung | Decision-Lifecycle und `DecisionResult` einschließlich des exakt verwendeten Evidence-Snapshots gemäß ADR-0001 und ADR-0006 | Quellsystemdaten, Explainability, Execution Trace oder Enterprise-Risk-Lifecycle |
| Enterprise Risk | Steuerung identifizierter Unternehmensrisiken über Bewertung, Ownership und Behandlung | Risk Record, fachliche Risiko-Ownership, Treatment, Acceptance, Eskalation und Portfolio-Zuordnung | einzelne technische Findings, Incidents, DecisionResult, Policies oder Compliance-Nachweise |
| Governance and Compliance | Definition und Bewertung verbindlicher Governance-Anforderungen | Policies, Controls, Compliance-Anforderungen, Exceptions und deren fachlicher Prüfstatus | Enterprise-Risk-Ownership, technische Findings, Plattformberechtigungen oder Executive-Darstellungen |
| Identity and Access | Festlegung, wer innerhalb welcher organisatorischen Grenze handeln oder Daten nutzen darf | Principals, Rollen, Berechtigungen, Organisationszuordnung und Autorisierungsregeln | Workspace-Darstellung, fachliche Risikoverantwortung, Security-Daten oder Plattformkonfiguration |
| Data Integration | Kontrollierte Aufnahme und Zuordnung externer Datenquellen zur Plattform | Integrationsdefinitionen, Connector-Zuordnung, Import- und Synchronisationszustand sowie technische Quell-Lineage | fachliche Interpretation aufgenommener Daten, Decisions, Risiken oder Betriebszustand der Gesamtplattform |
| Platform Operations | Sicherer Betrieb und kontrollierte Konfiguration der PredatorAI-Plattform | Plattformkonfiguration, Servicezustand, Hintergrundaufträge, technische Benachrichtigungen, Auditaktivität, Feature-Freigaben und Lizenzstatus | Security-Incidents, Business Risks, fachliche Decisions oder Quellsystemdaten |

## Detaillierte Verantwortungsgrenzen

### Enterprise Context

Enterprise Context beantwortet ausschließlich, **was** im Unternehmen geschützt wird und welche fachlichen Beziehungen und Kritikalitäten dafür autoritativ gelten. Andere Domänen referenzieren diese Identitäten, kopieren oder besitzen sie aber nicht. Security Observation beschreibt einen beobachteten Zustand eines referenzierten Assets; Enterprise Risk beschreibt die mögliche Unternehmensauswirkung; Incident Response beschreibt die Einbindung in einen Vorfall.

### Security Observation

Security Observation beantwortet ausschließlich, **was sicherheitsrelevant beobachtet wurde**. Ein Finding oder Alert wird nicht dadurch zum Incident, Hunt, Evidence oder DecisionResult. Die Domäne darf auf Enterprise Context und Threat Intelligence referenzieren. Die Auswahl einer Beobachtung als entscheidungsrelevant gehört dagegen zur Decision-Evidence-Grenze.

### Threat Intelligence

Threat Intelligence besitzt bewertete externe oder kuratierte Bedrohungsinformationen. Eine Übereinstimmung einer solchen Information mit internen Beobachtungen bleibt eine Korrelation beziehungsweise Beobachtung und verändert die Quelle nicht. Threat Hunting und Cyber Decision dürfen Intelligence referenzieren, übernehmen aber nicht deren Ownership.

### Threat Hunting

Threat Hunting beantwortet, **welche Hypothese proaktiv untersucht wird und in welchem Hunt-Zustand sie sich befindet**. Ergebnisse werden als Referenzen auf autoritative Beobachtungen, Intelligence oder Evidence geführt. Ein bestätigter Vorfall wechselt nicht stillschweigend die Ownership: Seine Übergabe erzeugt beziehungsweise aktualisiert ein Objekt der Incident-Response-Domäne unter Erhalt der Referenzen.

### Incident Response

Incident Response beantwortet, **wie ein Sicherheitsvorfall koordiniert, begrenzt, beseitigt, wiederhergestellt und dokumentiert wird**. Die Domäne besitzt den Response-Lifecycle und seine Maßnahmen, nicht die zugrunde liegenden Finding-, Asset- oder Evidence-Fakten. Business Impact wird über Enterprise Context und gegebenenfalls Enterprise Risk referenziert; er wird im Incident nicht als zweite Wahrheit gepflegt.

### Decision Evidence

Decision Evidence beantwortet, **welche überprüfbaren Aussagen einer konkreten Decision zur Verfügung standen**. Gemäß ADR-0006 besitzen Quelldomänen ihre ursprünglichen Fakten; die Evidence-Grenze besitzt deren normalisierte, unveränderliche und provenance-pflichtige entscheidungsrelevante Repräsentation. Der finale Evidence-Snapshot ist Bestandteil des kanonischen `DecisionResult`, ohne die Ownership der Quellobjekte zu übernehmen.

### Cyber Decision

Cyber Decision beantwortet, **welche fachliche Entscheidung auf Basis welcher Evidence getroffen wurde**. Diese Domäne allein besitzt das kanonische Decision-Ergebnis. Risiko-, Korrelations- oder Empfehlungsbeiträge dürfen Eingaben beziehungsweise Bestandteile des Ergebnisses sein, begründen aber keine parallele Decision-Quelle. Enterprise Risk kann ein DecisionResult als Eingang für den langfristigen Risk-Lifecycle verwenden, ohne es umzuschreiben.

### Enterprise Risk

Enterprise Risk beantwortet, **welches Unternehmensrisiko besteht, wer es verantwortet und wie es behandelt wird**. Sie besitzt die langlebige Risikosteuerung und das Portfolio, nicht die technische Beobachtung oder Einzelentscheidung. Governance and Compliance liefert Anforderungen und Ausnahmebedingungen; die konkrete fachliche Risikoakzeptanz und Treatment-Entscheidung verbleiben in Enterprise Risk.

### Governance and Compliance

Governance and Compliance beantwortet, **welche verbindlichen Anforderungen gelten und in welchem Prüfzustand sie sich befinden**. Eine Policy oder Compliance Exception ist kein Enterprise Risk. Verstöße können Beobachtungen oder Evidence begründen; Risiken und Decisions werden jedoch in ihren jeweiligen Domänen verantwortet.

### Identity and Access

Identity and Access beantwortet, **wer welche Handlung oder welchen Datenzugriff ausführen darf**. Rollen wie SOC Analyst, Threat Hunter, Incident Responder, Risk Manager, Executive, CISO und Administrator sind Autorisierungskontexte, keine fachlichen Dateneigentümer. Ein Workspace darf Berechtigungen darstellen und berücksichtigen, sie aber weder definieren noch ersetzen.

### Data Integration

Data Integration beantwortet, **aus welcher externen Quelle Daten technisch aufgenommen wurden und in welchem Übertragungszustand sie sich befinden**. Nach kontrollierter fachlicher Zuordnung übernimmt die jeweilige Zieldomäne die kanonische fachliche Ownership. Connector- oder Synchronisationszustände sind keine Security Findings und keine Evidence, solange sie nicht durch eine autorisierte fachliche Verarbeitung als solche klassifiziert wurden.

### Platform Operations

Platform Operations beantwortet, **wie die Plattform betrieben, überwacht und technisch konfiguriert wird**. Plattform-Health und Hintergrundaufträge dürfen nicht als Cyberlage, Incident oder Enterprise Risk interpretiert werden. Technische Auditaktivität gehört hierher; der Reasoning Execution Trace bleibt davon getrennt das in ADR-0002 definierte Application-/Audit-Artefakt einer einzelnen Reasoning-Ausführung.

## Abgeleitete Architekturartefakte

Die folgenden Strukturen sind bewusst keine zusätzlichen kanonischen fachlichen Domänen:

* **Decision Explainability:** read-only Application Read Model aus kanonischen Quellen gemäß ADR-0003 und ADR-0004. Es besitzt keine fachlichen Fakten.
* **Execution Trace:** geordneter technischer Nachweis einer Reasoning-Ausführung gemäß ADR-0002. Er besitzt keine Decision- oder Evidence-Semantik.
* **Workspace und Mission Console:** rollenbezogene Presentation- und Arbeitskontextgrenze gemäß ADR-0005. Sie besitzt keine kanonischen Fachdaten.
* **Dashboard, Report und Timeline:** Darstellungen beziehungsweise Projektionen; ihre Gruppierung erzeugt keine Ownership.
* **API, Service, Event und Datenbank:** mögliche technische Realisierungen oder Integrationsverträge; sie werden durch dieses Dokument weder definiert noch einer Implementierungsstruktur zugeordnet.

## Ownership-Regeln

1. Jedes fachliche Objekt besitzt genau eine kanonische Owner-Domäne.
2. Andere Domänen verwenden stabile Referenzen oder autorisierte Projektionen; sie führen keine konkurrierende Kopie als Wahrheit.
3. Eine Übergabe zwischen Arbeitsabläufen überträgt nicht automatisch Ownership. Entsteht ein neues fachliches Objekt, behält es Referenzen zu seinen Quellen.
4. Abgeleitete Aussagen müssen auf ihre autoritativen Eingaben zurückführbar bleiben.
5. Presentation State, Workspace State und technische Ausführungszustände dürfen fachlichen Zustand weder ersetzen noch plausibilisieren.
6. Autorisierung kontrolliert Zugriff und Handlungen, verändert aber nicht die fachliche Ownership.

## Fachliche Abhängigkeitsrichtung

Die fachliche Informationsrichtung ist azyklisch:

```text
External Sources
      │
      ▼
Data Integration
      │
      ├──────────────► Enterprise Context
      ├──────────────► Security Observation
      └──────────────► Threat Intelligence
                              │
Enterprise Context ───────────┼──────────────┐
Security Observation ─────────┼──────────┐   │
Threat Intelligence ──────────┘          │   │
                                         ▼   │
Threat Hunting ─────────────────► Decision Evidence
Incident Response ──────────────►         │
Governance and Compliance ──────►         ▼
                                  Cyber Decision
                                         │
                                         ▼
                                  Enterprise Risk

Identity and Access controls authorized use across boundaries.
Platform Operations operates the platform without owning domain facts.
Explainability projects canonical Decision data read-only.
```

Die Pfeile beschreiben zulässige fachliche Informationsnutzung, keine API-, Service-, Event- oder Modulentscheidung. Rückmeldungen in einen Workflow dürfen neue fachliche Vorgänge auslösen, aber keine rückwärtsgerichtete Mutation der autoritativen Quelle bewirken.

## Workspace-neutrale Zuordnung

Die Workspace-Analyse bestätigt die Grenzen, definiert sie jedoch nicht:

| Arbeitswelt | Primär konsumierte Domänen |
|---|---|
| SOC Analyst | Security Observation, Enterprise Context, Cyber Decision, Decision Evidence, Threat Intelligence |
| Threat Hunter | Threat Hunting, Security Observation, Threat Intelligence, Enterprise Context, Decision Evidence |
| Incident Response | Incident Response, Security Observation, Enterprise Context, Decision Evidence, Cyber Decision |
| Risk Manager | Enterprise Risk, Enterprise Context, Governance and Compliance, Cyber Decision |
| Executive und CISO | Enterprise Risk, Enterprise Context, Governance and Compliance, Cyber Decision; ausschließlich geeignete Projektionen |
| Administrator | Platform Operations, Data Integration, Identity and Access |

Mehrfachnutzung ist beabsichtigt. Sie bedeutet weder geteilte Ownership noch eine Verschmelzung der Domänen. Insbesondere sind SOC Analyst, Threat Hunter, Incident Response, Risk Manager, Executive, CISO und Administrator Rollen beziehungsweise Arbeitswelten und keine Canonical Domains.

## Nicht Bestandteil

Dieses Dokument definiert keine Domain-Klassen, Dataclasses, DTOs, APIs, Services, Events, Datenbanken, Persistenz, Serialisierung, Builder, UI, Workspace-Änderung oder Produktimplementierung. Es legt weder konkrete Aggregate noch Feldnamen, Transportverträge, Deployment-Einheiten, Modulzuschnitte oder Teamstrukturen fest. Solche Entscheidungen benötigen bei Bedarf einen separat freigegebenen AIDP-Task.

## Statische Konsistenzprüfung

* Jede aufgeführte Domäne besitzt genau einen klar benannten fachlichen Gegenstand.
* Gemeinsam genutzte Konzepte sind einer Owner-Domäne zugeordnet und werden außerhalb nur referenziert oder projiziert.
* Decision, Evidence, Explainability und Execution Trace bleiben entsprechend ADR-0001, ADR-0002, ADR-0003, ADR-0004 und ADR-0006 getrennt.
* Workspace- und Rollenstrukturen bleiben entsprechend ADR-0005 außerhalb der fachlichen Ownership.
* Das Dokument trifft keine Technologie- oder Implementierungsentscheidung.

## Referenzen

* `ARCHITECTURE.md`
* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0003-explainability-projection.md`
* `.ai/decisions/ADR-0004-explainability-completeness.md`
* `.ai/decisions/ADR-0005-mission-console-workspace-architecture.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/tasks/done/TASK-0027.md`

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
