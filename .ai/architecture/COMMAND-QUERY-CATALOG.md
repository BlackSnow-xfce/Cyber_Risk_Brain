# PredatorAI v3 – Command & Query Catalog

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument definiert die kanonischen fachlichen Anwendungsgrenzen von PredatorAI nach CQRS-Prinzipien. Ein Command beabsichtigt eine fachliche Zustandsänderung innerhalb der Aggregate-Grenzen seiner Owner Domain. Eine Query liest vorhandene fachliche Aussagen und verändert niemals Zustand.

Commands und Queries werden ausschließlich durch bestehende Application Services orchestriert. Domain Services treffen fachliche Entscheidungen, Domain Policies begrenzen diese Entscheidungen und Aggregates behalten Ownership, Invarianten und Konsistenz. Referenzen auf Domain Events verwenden ausschließlich bestehende Events und legen keinen technischen Mechanismus fest.

## CQRS-Regeln

1. Ein fachlicher Aufruf ist entweder Command oder Query, niemals beides.
2. Commands dürfen nur Aggregate ihrer Owner Domain verändern; Aggregate anderer Domains sind ausschließlich autoritative Eingaben.
3. Queries lesen vorhandene Aggregate-Aussagen, erzeugen keine Fakten, verändern keinen Zustand und lösen keine Domain Events aus.
4. Application Services koordinieren; sie enthalten keine Geschäftslogik.
5. Domain Services entscheiden fachlich; Commands und Queries ersetzen sie nicht.
6. Aggregates bleiben alleinige Zustands- und Konsistenzgrenzen.
7. Ein fehlendes bestehendes Domain Event wird ausdrücklich dokumentiert und nicht durch diesen Katalog ergänzt.
8. Persistenz, Infrastruktur, technische Autorisierung und Transport sind keine Verantwortung eines Commands oder einer Query.

## Command-Übersicht

| ID | Command | Owner Domain | Verantwortlicher Application Service | Betroffene Owner-Aggregate |
|---|---|---|---|---|
| CMD-001 | Coordinate Data Intake | Data Integration | Data Intake Application Service | Integration Aggregate; Synchronization Run Aggregate; Import Run Aggregate |
| CMD-002 | Classify Enterprise Context | Enterprise Context | Enterprise Context Classification Application Service | Asset Context Aggregate; Business Service Context Aggregate; Organizational Unit Context Aggregate |
| CMD-003 | Assess Threat Intelligence | Threat Intelligence | Threat Intelligence Assessment Application Service | Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate |
| CMD-004 | Correlate Security Observations | Security Observation | Security Observation Correlation Application Service | Finding Aggregate; Alert Aggregate; Exposure Aggregate |
| CMD-005 | Assess Governance Compliance | Governance and Compliance | Governance Compliance Assessment Application Service | Governance Policy Aggregate; Compliance Requirement Aggregate |
| CMD-006 | Qualify Decision Evidence | Decision Evidence | Decision Evidence Qualification Application Service | Evidence Aggregate |
| CMD-007 | Evaluate Cyber Decision | Cyber Decision | Cyber Decision Evaluation Application Service | Decision Aggregate |
| CMD-008 | Assess Enterprise Risk | Enterprise Risk | Enterprise Risk Assessment Application Service | Enterprise Risk Aggregate |

Authorization Evaluation besitzt bewusst keinen Command: Eine fachliche Autorisierungsentscheidung bewertet vorhandene Aussagen und verändert keinen fachlichen Zustand. Sie ist daher ausschließlich als Query katalogisiert.

## Command-Details

### CMD-001 – Coordinate Data Intake

**Owner Domain:** Data Integration  
**Verantwortlicher Application Service:** Data Intake Application Service  
**Betroffene Aggregate:** Integration Aggregate; Synchronization Run Aggregate; Import Run Aggregate.  
**Fachlicher Zweck:** Einen vorhandenen Import- oder Synchronisierungsvorgang widerspruchsfrei einer vorhandenen Integration zuordnen.  
**Fachliche Vorbedingungen:** Integration und genau ein betroffener Run bestehen als eigenständige Aggregate; ihre vorhandene Source Lineage ist verfügbar.  
**Fachliches Ergebnis:** Der betroffene Run besitzt eine fachlich konsistente Zuordnung zu seinem Integrationskontext; die Aggregate bleiben getrennt.  
**Berücksichtigte Domain Policies:** Intake Lineage Integrity Policy.  
**Referenzierte Domain Events:** Integration Context Established als fachliche Vorbedingung. Kein bestehendes Domain Event beschreibt den Zuordnungsabschluss; der Command führt keines neu ein.  
**Fachliche Begründung:** Die Zuordnung verändert domäneneigenen Zustand über einen bestehenden Application und Domain Service, ohne Aufnahme oder technische Ausführung zu definieren.

### CMD-002 – Classify Enterprise Context

**Owner Domain:** Enterprise Context  
**Verantwortlicher Application Service:** Enterprise Context Classification Application Service  
**Betroffene Aggregate:** Asset Context Aggregate; Business Service Context Aggregate; Organizational Unit Context Aggregate.  
**Fachlicher Zweck:** Vorhandene Unternehmenskontexte autoritativ und domänenweit widerspruchsfrei einordnen.  
**Fachliche Vorbedingungen:** Die betroffenen Context Aggregates bestehen; erforderliche Herkunft ist ausschließlich über das Integration Aggregate autoritativ verfügbar.  
**Fachliches Ergebnis:** Jedes betroffene Context Aggregate enthält ausschließlich seine eigene konsistente Klassifikationsaussage.  
**Berücksichtigte Domain Policies:** Authoritative Context Classification Policy.  
**Referenzierte Domain Events:** Integration Context Established als mögliche Vorbedingung; Asset Context Classified; Business Service Context Classified; Organizational Context Established als bestehende Ergebnisereignisse der jeweils tatsächlich geänderten Aggregate.  
**Fachliche Begründung:** Eine Klassifikation kann mehrere unabhängige Context-Grenzen betreffen, ohne sie zu verschmelzen oder fehlende Aussagen zu erzeugen.

### CMD-003 – Assess Threat Intelligence

**Owner Domain:** Threat Intelligence  
**Verantwortlicher Application Service:** Threat Intelligence Assessment Application Service  
**Betroffene Aggregate:** Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate.  
**Fachlicher Zweck:** Vorhandene Intelligence-Aussagen unter Erhalt ihrer eigenständigen Bedeutung und Herkunft bewerten.  
**Fachliche Vorbedingungen:** Mindestens eine vorhandene Intelligence-Aussage ist bewertbar; vorhandene Herkunft stammt autoritativ aus Data Integration.  
**Fachliches Ergebnis:** Jedes tatsächlich betroffene Intelligence Aggregate besitzt seine eigene konsistente Bewertung; keine Aussage wird zwischen Aggregates kopiert.  
**Berücksichtigte Domain Policies:** Intelligence Provenance and Assessment Integrity Policy.  
**Referenzierte Domain Events:** Integration Context Established als mögliche Vorbedingung; Threat Indicator Assessed und Threat Technique Assessed als bestehende Ergebnisereignisse. Für Threat Actor und Threat Campaign existiert bewusst kein eigenes Event.  
**Fachliche Begründung:** Die Bewertung koordiniert unabhängige Intelligence-Aussagen über den bestehenden Assessment Service und bewahrt deren Provenance.

### CMD-004 – Correlate Security Observations

**Owner Domain:** Security Observation  
**Verantwortlicher Application Service:** Security Observation Correlation Application Service  
**Betroffene Aggregate:** Finding Aggregate; Alert Aggregate; Exposure Aggregate.  
**Fachlicher Zweck:** Vorhandene Observation-Aussagen fachlich gemeinsam einordnen, ohne ihre Ownership oder Eigenständigkeit zu verändern.  
**Fachliche Vorbedingungen:** Mindestens zwei autoritative Observations bestehen; verwendeter Asset- oder Indicator-Kontext ist bereits vorhanden.  
**Fachliches Ergebnis:** Nur die tatsächlich betroffenen Observation Aggregates berücksichtigen das fachliche Korrelationsergebnis innerhalb ihrer eigenen Grenzen.  
**Berücksichtigte Domain Policies:** Observation Correlation Integrity Policy.  
**Referenzierte Domain Events:** Asset Context Classified; Threat Indicator Assessed; Finding Established; Alert Established; Exposure Established ausschließlich als bestehende Eingangstatsachen. Für das Korrelationsergebnis existiert kein eigenes Domain Event; dieser Katalog führt keines ein.  
**Fachliche Begründung:** Der Command ermöglicht eine explizite Zustandsänderungsabsicht, delegiert die Korrelationsentscheidung jedoch vollständig an den bestehenden Domain Service.

### CMD-005 – Assess Governance Compliance

**Owner Domain:** Governance and Compliance  
**Verantwortlicher Application Service:** Governance Compliance Assessment Application Service  
**Betroffene Aggregate:** Governance Policy Aggregate; Compliance Requirement Aggregate.  
**Fachlicher Zweck:** Geltung und Compliance anhand vorhandener Context- und Finding-Aussagen fachlich bewerten.  
**Fachliche Vorbedingungen:** Governance Policy oder Compliance Requirement besteht; benötigter Unternehmenskontext und gegebenenfalls Finding sind autoritativ vorhanden.  
**Fachliches Ergebnis:** Policy-Geltung und Compliance Assessment verbleiben konsistent in ihren jeweiligen Aggregates; Exceptions werden nicht als Risk Acceptance umgedeutet.  
**Berücksichtigte Domain Policies:** Governance Applicability and Exception Integrity Policy.  
**Referenzierte Domain Events:** Organizational Context Established; Business Service Context Classified; Finding Established als Eingangstatsachen; Governance Policy Changed und Compliance Requirement Assessed als bestehende Ergebnisereignisse.  
**Fachliche Begründung:** Der Command koordiniert zwei Governance-Grenzen und zulässige externe Aussagen, während der Domain Service die fachliche Bewertung trifft.

### CMD-006 – Qualify Decision Evidence

**Owner Domain:** Decision Evidence  
**Verantwortlicher Application Service:** Decision Evidence Qualification Application Service  
**Betroffene Aggregate:** Evidence Aggregate.  
**Fachlicher Zweck:** Eine vorhandene autoritative Quellaussage als entscheidungsrelevante Evidence qualifizieren.  
**Fachliche Vorbedingungen:** Eine zulässige Source-Aussage aus Security Observation, Threat Intelligence, Threat Hunting oder Governance and Compliance besteht und ist nachvollziehbar.  
**Fachliches Ergebnis:** Das Evidence Aggregate besitzt eine unveränderliche, provenance-pflichtige Evidence-Aussage; die Quelle bleibt unverändert.  
**Berücksichtigte Domain Policies:** Evidence Admissibility and Provenance Policy.  
**Referenzierte Domain Events:** Finding Established; Alert Established; Exposure Established; Threat Indicator Assessed; Hunt Concluded; Governance Policy Changed als mögliche Eingangstatsachen; Evidence Qualified als Ergebnisereignis.  
**Fachliche Begründung:** Nur ein expliziter Command darf die Entstehung kanonischer Evidence beabsichtigen; Eignung und Herkunft entscheidet der Qualification Service.

### CMD-007 – Evaluate Cyber Decision

**Owner Domain:** Cyber Decision  
**Verantwortlicher Application Service:** Cyber Decision Evaluation Application Service  
**Betroffene Aggregate:** Decision Aggregate.  
**Fachlicher Zweck:** Eine Cyber Decision aus qualifizierter Evidence und zulässigen Context- und Governance-Aussagen bewerten und abschließen.  
**Fachliche Vorbedingungen:** Qualifizierte Evidence besteht; erforderlicher Business-Service-Kontext und geltende Governance Policy sind vorhanden; die Decision ist noch nicht abgeschlossen.  
**Fachliches Ergebnis:** Das Decision Aggregate besitzt genau ein kanonisches abgeschlossenes `DecisionResult` mit dem exakt verwendeten Evidence-Snapshot.  
**Berücksichtigte Domain Policies:** Canonical Decision Basis Policy.  
**Referenzierte Domain Events:** Evidence Qualified; Business Service Context Classified; Governance Policy Changed als Eingangstatsachen; Decision Completed als Ergebnisereignis.  
**Fachliche Begründung:** Der Command bildet die einzige fachliche Schreibgrenze für den Decision-Abschluss und verhindert parallele Decision-Wahrheiten.

### CMD-008 – Assess Enterprise Risk

**Owner Domain:** Enterprise Risk  
**Verantwortlicher Application Service:** Enterprise Risk Assessment Application Service  
**Betroffene Aggregate:** Enterprise Risk Aggregate.  
**Fachlicher Zweck:** Ein vorhandenes Enterprise Risk anhand autoritativer Decision-, Business- und Governance-Aussagen bewerten oder priorisieren.  
**Fachliche Vorbedingungen:** Das Enterprise Risk besteht; erforderliche Eingangsaussagen sind vorhanden und werden nicht verändert.  
**Fachliches Ergebnis:** Bewertung oder Priorisierung ist innerhalb des Enterprise Risk Aggregate konsistent aktualisiert; Treatment und Acceptance verbleiben bei dessen Root.  
**Berücksichtigte Domain Policies:** Risk Ownership and Treatment Authority Policy.  
**Referenzierte Domain Events:** Decision Completed; Business Service Context Classified; Governance Policy Changed als Eingangstatsachen. Enterprise Risk Treatment Decided wird nur dann referenziert, wenn der bestehende Aggregate-Lifecycle tatsächlich eine Treatment- oder Acceptance-Entscheidung abschließt; für reine Bewertung existiert kein eigenes Event.  
**Fachliche Begründung:** Der Command trennt die beabsichtigte Risk-Zustandsänderung von lesender Portfolioauskunft und delegiert Bewertung und Priorisierung an den bestehenden Domain Service.

## Query-Übersicht

| ID | Query | Owner Domain | Verantwortlicher Application Service | Gelesene Aggregate |
|---|---|---|---|---|
| QRY-001 | Read Data Intake Context | Data Integration | Data Intake Application Service | Integration Aggregate; Synchronization Run Aggregate; Import Run Aggregate |
| QRY-002 | Read Enterprise Context Classification | Enterprise Context | Enterprise Context Classification Application Service | Asset Context Aggregate; Business Service Context Aggregate; Organizational Unit Context Aggregate |
| QRY-003 | Read Threat Intelligence Assessment | Threat Intelligence | Threat Intelligence Assessment Application Service | Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate |
| QRY-004 | Read Security Observation Correlation Context | Security Observation | Security Observation Correlation Application Service | Finding Aggregate; Alert Aggregate; Exposure Aggregate; Asset Context Aggregate; Threat Indicator Aggregate |
| QRY-005 | Read Governance Compliance Assessment | Governance and Compliance | Governance Compliance Assessment Application Service | Governance Policy Aggregate; Compliance Requirement Aggregate; Organizational Unit Context Aggregate; Business Service Context Aggregate; Finding Aggregate |
| QRY-006 | Evaluate Authorization | Identity and Access | Authorization Evaluation Application Service | Principal Aggregate; Access Role Aggregate; Permission Aggregate; Authorization Rule Aggregate; Organizational Unit Context Aggregate |
| QRY-007 | Read Decision Evidence Qualification | Decision Evidence | Decision Evidence Qualification Application Service | Evidence Aggregate; Finding Aggregate; Alert Aggregate; Exposure Aggregate; Threat Indicator Aggregate; Hunt Aggregate; Governance Policy Aggregate |
| QRY-008 | Read Cyber Decision | Cyber Decision | Cyber Decision Evaluation Application Service | Decision Aggregate; Evidence Aggregate; Business Service Context Aggregate; Governance Policy Aggregate |
| QRY-009 | Read Enterprise Risk Assessment | Enterprise Risk | Enterprise Risk Assessment Application Service | Enterprise Risk Aggregate; Decision Aggregate; Business Service Context Aggregate; Governance Policy Aggregate |

## Query-Details

### QRY-001 – Read Data Intake Context

**Owner Domain:** Data Integration  
**Verantwortlicher Application Service:** Data Intake Application Service  
**Gelesene Aggregate:** Integration Aggregate; Synchronization Run Aggregate; Import Run Aggregate.  
**Fachlicher Zweck:** Vorhandene Integrationszuordnung, Run-Zustand und Source Lineage gemeinsam auskunftsfähig machen.  
**Erwartetes fachliches Ergebnis:** Ausschließlich vorhandene, getrennt verantwortete Aussagen der drei Aggregate.  
**Konsistenzanforderungen:** Jeder Aggregate-Zustand wird in seiner eigenen Gültigkeit gelesen; fehlende Zuordnungen werden als fehlend ausgewiesen und nicht erzeugt.  
**Fachliche Begründung:** Der lesende Bedarf unterstützt die Intake-Koordination, ohne Run oder Integration zu verändern.

### QRY-002 – Read Enterprise Context Classification

**Owner Domain:** Enterprise Context  
**Verantwortlicher Application Service:** Enterprise Context Classification Application Service  
**Gelesene Aggregate:** Asset Context Aggregate; Business Service Context Aggregate; Organizational Unit Context Aggregate.  
**Fachlicher Zweck:** Autoritative vorhandene Context- und Klassifikationsaussagen lesen.  
**Erwartetes fachliches Ergebnis:** Die vorhandenen Identitäts-, Kritikalitäts- und Kontextaussagen mit klarer Aggregate-Herkunft.  
**Konsistenzanforderungen:** Keine Aussage wird zwischen Context Aggregates zusammengeführt oder plausibilisiert.  
**Fachliche Begründung:** Konsumenten benötigen verlässlichen Context, ohne über eine Query Klassifikation auszulösen.

### QRY-003 – Read Threat Intelligence Assessment

**Owner Domain:** Threat Intelligence  
**Verantwortlicher Application Service:** Threat Intelligence Assessment Application Service  
**Gelesene Aggregate:** Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate.  
**Fachlicher Zweck:** Vorhandene Intelligence-Bewertungen unter Erhalt ihrer jeweiligen Herkunft lesen.  
**Erwartetes fachliches Ergebnis:** Eigenständige, nicht vermischte Intelligence-Aussagen der gelesenen Aggregate.  
**Konsistenzanforderungen:** Provenance und fachliche Bedeutung bleiben unverändert; fehlende Bewertung bleibt sichtbar.  
**Fachliche Begründung:** Der lesende Bedarf ist von der zustandsändernden Intelligence-Bewertung strikt getrennt.

### QRY-004 – Read Security Observation Correlation Context

**Owner Domain:** Security Observation  
**Verantwortlicher Application Service:** Security Observation Correlation Application Service  
**Gelesene Aggregate:** Finding Aggregate; Alert Aggregate; Exposure Aggregate; Asset Context Aggregate; Threat Indicator Aggregate.  
**Fachlicher Zweck:** Vorhandene Observations und ihren zulässigen autoritativen Kontext ohne erneute Korrelation lesen.  
**Erwartetes fachliches Ergebnis:** Getrennte Observation-, Asset- und Indicator-Aussagen mit erkennbarer Ownership.  
**Konsistenzanforderungen:** Die Query erzeugt keine Korrelation und verändert keine Disposition; Cross-Domain-Aussagen bleiben read-only.  
**Fachliche Begründung:** Sichtbarkeit des Korrelationskontexts darf keine versteckte Schreib- oder Bewertungsoperation sein.

### QRY-005 – Read Governance Compliance Assessment

**Owner Domain:** Governance and Compliance  
**Verantwortlicher Application Service:** Governance Compliance Assessment Application Service  
**Gelesene Aggregate:** Governance Policy Aggregate; Compliance Requirement Aggregate; Organizational Unit Context Aggregate; Business Service Context Aggregate; Finding Aggregate.  
**Fachlicher Zweck:** Vorhandene Governance-Geltung und Compliance-Bewertung mit ihren autoritativen Grundlagen lesen.  
**Erwartetes fachliches Ergebnis:** Bestehende Policy-, Requirement-, Assessment-, Context- und Finding-Aussagen ohne Neubewertung.  
**Konsistenzanforderungen:** Exception und Risk Acceptance bleiben getrennt; die Query verändert weder Assessment noch Quelle.  
**Fachliche Begründung:** Governance-Auskunft muss von der zustandsändernden Bewertungsabsicht getrennt bleiben.

### QRY-006 – Evaluate Authorization

**Owner Domain:** Identity and Access  
**Verantwortlicher Application Service:** Authorization Evaluation Application Service  
**Gelesene Aggregate:** Principal Aggregate; Access Role Aggregate; Permission Aggregate; Authorization Rule Aggregate; Organizational Unit Context Aggregate.  
**Fachlicher Zweck:** Auf Basis vorhandener autoritativer Aussagen fachlich ermitteln, ob eine konkrete Handlung oder Datennutzung zulässig ist.  
**Erwartetes fachliches Ergebnis:** Eine fachliche Autorisierungsentscheidung ohne Zustandsänderung an Principal, Rolle, Permission, Regel oder Organisationskontext.  
**Konsistenzanforderungen:** Die Contextual Authorization Policy gilt; nur der Authorization Decision Service entscheidet, fehlende Berechtigungen werden nicht plausibilisiert.  
**Fachliche Begründung:** Autorisierung ist eine fachliche Entscheidung, aber keine Zustandsänderung, und gehört deshalb auf die Query-Seite.

### QRY-007 – Read Decision Evidence Qualification

**Owner Domain:** Decision Evidence  
**Verantwortlicher Application Service:** Decision Evidence Qualification Application Service  
**Gelesene Aggregate:** Evidence Aggregate; Finding Aggregate; Alert Aggregate; Exposure Aggregate; Threat Indicator Aggregate; Hunt Aggregate; Governance Policy Aggregate.  
**Fachlicher Zweck:** Vorhandene Evidence und ihre autoritativen Quellen lesen, ohne eine neue Qualifikation anzustoßen.  
**Erwartetes fachliches Ergebnis:** Unveränderte Evidence-Aussage mit Herkunft und vorhandenen Source-Aussagen.  
**Konsistenzanforderungen:** Evidence bleibt immutable und provenance-pflichtig; fehlende Fakten werden nicht erzeugt.  
**Fachliche Begründung:** Die Überprüfung vorhandener Evidence muss strikt von ihrer Qualifikation getrennt sein.

### QRY-008 – Read Cyber Decision

**Owner Domain:** Cyber Decision  
**Verantwortlicher Application Service:** Cyber Decision Evaluation Application Service  
**Gelesene Aggregate:** Decision Aggregate; Evidence Aggregate; Business Service Context Aggregate; Governance Policy Aggregate.  
**Fachlicher Zweck:** Eine vorhandene Decision mit ihrer zulässigen fachlichen Grundlage lesen.  
**Erwartetes fachliches Ergebnis:** Das kanonische vorhandene `DecisionResult` und unveränderte Referenzen auf Evidence, Business Context und Governance.  
**Konsistenzanforderungen:** `DecisionResult` bleibt Single Source of Truth; Explainability erzeugt keine zusätzlichen Fakten; die Query schließt keine Decision ab.  
**Fachliche Begründung:** Decision-Auskunft darf keine erneute Evaluation oder parallele Decision-Aussage erzeugen.

### QRY-009 – Read Enterprise Risk Assessment

**Owner Domain:** Enterprise Risk  
**Verantwortlicher Application Service:** Enterprise Risk Assessment Application Service  
**Gelesene Aggregate:** Enterprise Risk Aggregate; Decision Aggregate; Business Service Context Aggregate; Governance Policy Aggregate.  
**Fachlicher Zweck:** Vorhandene Risk-Bewertung und ihre autoritativen Eingänge lesen.  
**Erwartetes fachliches Ergebnis:** Bestehende Rating-, Treatment-, Acceptance-, Decision-, Context- und Governance-Aussagen mit klarer Ownership.  
**Konsistenzanforderungen:** Die Query priorisiert nicht neu und verändert weder Enterprise Risk noch Eingangsaussagen.  
**Fachliche Begründung:** Risk-Auskunft ist von Bewertung und Priorisierung als Command strikt getrennt.

## Domains ohne eigene Commands und Queries

Threat Hunting, Incident Response und Platform Operations besitzen gemäß `APPLICATION-SERVICES.md` keinen kanonischen Application Service. Da jeder Command und jede Query zwingend durch einen bestehenden Application Service verantwortet wird, werden für diese Domains keine künstlichen Anwendungsgrenzen eingeführt. Ihre vorhandenen Aggregate-Verantwortungen bleiben unverändert.

## Referenz- und Verantwortungsprüfung

| Kategorie | Ergebnis |
|---|---|
| Commands | 8 eindeutige zustandsändernde Anwendungsgrenzen |
| Queries | 9 eindeutige ausschließlich lesende Anwendungsgrenzen |
| Owner Domains | Jede Grenze besitzt genau eine Owner Domain |
| Application Services | Ausschließlich die 9 bestehenden Application Services referenziert |
| Aggregate | Ausschließlich bestehende Aggregate referenziert |
| Policies | Ausschließlich die 9 bestehenden Domain Policies berücksichtigt |
| Events | Ausschließlich bestehende Domain Events referenziert; fehlende Ergebnisereignisse ausdrücklich benannt |
| Geschäftslogik | Verbleibt bei Aggregates, Domain Services und Domain Policies |
| Persistenz und Infrastruktur | Keine Verantwortung definiert |

## Konsistenz mit ADR-0001 bis ADR-0007

* ADR-0001: Evaluate Cyber Decision ist die einzige Command-Grenze, die den Abschluss eines `DecisionResult` beabsichtigt.
* ADR-0002: Execution Trace ist weder Command-Ergebnis noch Query-Domainmodell.
* ADR-0003 und ADR-0004: Explainability bleibt read-only und erzeugt in Queries keine fehlenden Fakten.
* ADR-0005: Workspaces und Rollen begründen keine Command-, Query- oder Daten-Ownership.
* ADR-0006: Qualify Decision Evidence bewahrt Unveränderlichkeit, Provenance und getrennte Source-Ownership.
* ADR-0007: Alle Cross-Domain-Leseabhängigkeiten folgen den definierten Layern; Commands verändern keine fremden Aggregate.

## Nicht Bestandteil

Dieses Dokument definiert keinen Produktcode, REST, FastAPI, HTTP, Controller, DTOs, Endpunkte, Authentifizierung, technische Autorisierung, Persistenz, Infrastruktur, Klassen, Interfaces, Methoden, Handler, Repositorys, Event-Verarbeitung, Messaging, Payloads oder technische Verträge. Es verändert kein bestehendes Architekturartefakt und keine Architekturentscheidung.

## Statische Konsistenzprüfung

* Acht Commands und neun Queries besitzen eindeutige Namen und jeweils genau eine Owner Domain.
* Alle 17 Anwendungsgrenzen referenzieren genau einen bestehenden Application Service.
* Alle verwendeten Aggregate, Policies und Events stammen aus den bestehenden Katalogen.
* Commands und Queries überschneiden sich nicht; Queries sind ohne Zustandsänderung und Event-Auslösung beschrieben.
* Commands verändern ausschließlich Owner-Domain-Aggregates; fremde Aggregate dienen nur als autoritative Eingaben.
* Keine Geschäftslogik, Persistenz-, Infrastruktur- oder technische Schnittstellenverantwortung wurde eingeführt.

## Referenzen

* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `.ai/architecture/DOMAIN-DEPENDENCIES.md`
* `.ai/architecture/DOMAIN-SERVICES.md`
* `.ai/architecture/DOMAIN-POLICIES.md`
* `.ai/architecture/DOMAIN-EVENTS.md`
* `.ai/architecture/APPLICATION-SERVICES.md`
* ADR-0001 bis ADR-0007
* AIDP TASK-0041

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
