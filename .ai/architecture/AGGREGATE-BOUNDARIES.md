# PredatorAI v3 – Aggregate Boundaries

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument definiert die fachlichen Aggregate und Konsistenzgrenzen des kanonischen Domänenmodells von PredatorAI. Es ordnet bestehende Canonical Entities genau einer fachlichen Grenze zu und benennt pro Aggregate genau eine Aggregate Root.

Eine Konsistenzgrenze bedeutet hier ausschließlich, dass die enthaltenen fachlichen Gegenstände für ihre unmittelbare fachliche Gültigkeit gemeinsam verantwortet werden. Das Dokument entscheidet keine Transaktions-, Persistenz-, Kommunikations-, Modul- oder Implementierungsgrenze.

## Regeln

* Jedes Aggregate gehört genau einer bestehenden kanonischen Domäne.
* Jedes Aggregate besitzt genau eine Root aus dem bestehenden Canonical-Entity-Katalog.
* Jede Canonical Entity gehört höchstens einem Aggregate an.
* Keine Aggregate-Grenze überschreitet eine Domain Boundary.
* Ein Canonical Value Object darf von mehreren Aggregaten derselben Owner-Domäne verwendet werden.
* Die Verwendung eines Value Objects verändert weder dessen Bedeutung noch dessen Ownership.
* Beziehungen oder Koordination zwischen Aggregaten werden nicht beschrieben.
* Kleine Grenzen werden bevorzugt; gemeinsame Darstellung oder gemeinsame Nutzung allein rechtfertigt kein gemeinsames Aggregate.

## Enterprise Context

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Asset Context Aggregate | Asset | Verantwortet die konsistente fachliche Identität eines schutzrelevanten Unternehmensgegenstands. | Ein Asset muss unabhängig von Business Services und Organisationsstrukturen gültig bleiben; nur seine eigene fachliche Aussage liegt innerhalb dieser Grenze. | Asset | Asset Criticality |
| Business Service Context Aggregate | Business Service | Verantwortet die konsistente fachliche Identität einer geschäftlichen Leistung. | Die Gültigkeit eines Business Service erfordert keine gemeinsame Änderung mit einem Asset oder einer Organizational Unit. | Business Service | Business Service Criticality |
| Organizational Unit Context Aggregate | Organizational Unit | Verantwortet die konsistente fachliche Identität eines Organisationsbereichs. | Eine Organizational Unit besitzt eine eigenständige fachliche Gültigkeit und wird nicht mit Schutzobjekten zu einer gemeinsamen Konsistenzgrenze verschmolzen. | Organizational Unit | Keine |

Alle drei Aggregate gehören ausschließlich zur Domäne **Enterprise Context**.

## Security Observation

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Finding Aggregate | Finding | Verantwortet die konsistente fachliche Aussage einer Security-Feststellung. | Ein Finding bleibt unabhängig von Alert und Exposure gültig und darf nicht durch deren Lebensläufe verändert werden. | Finding | Observation Severity; Observation Disposition |
| Alert Aggregate | Alert | Verantwortet die konsistente fachliche Aussage eines prüfungsbedürftigen Sicherheitshinweises. | Ein Alert besitzt eine eigenständige Gültigkeit; seine gemeinsame Anzeige mit Findings begründet keine gemeinsame Konsistenz. | Alert | Observation Severity; Observation Disposition |
| Exposure Aggregate | Exposure | Verantwortet die konsistente fachliche Aussage eines exponierten Sicherheitszustands. | Ein Exposure kann unabhängig von Finding und Alert bestehen und wird deshalb separat konsistent gehalten. | Exposure | Exposure Level; Observation Severity; Observation Disposition |

Alle drei Aggregate gehören ausschließlich zur Domäne **Security Observation**.

## Threat Intelligence

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Threat Actor Aggregate | Threat Actor | Verantwortet die konsistente fachliche Aussage über eine Bedrohungsquelle. | Ein Threat Actor bleibt unabhängig von Technique, Indicator und Campaign identifizierbar und gültig. | Threat Actor | Intelligence Confidence; Threat Relevance |
| Threat Technique Aggregate | Threat Technique | Verantwortet die konsistente fachliche Bedeutung eines Bedrohungsvorgehens. | Eine Technique besitzt eine eigenständige fachliche Gültigkeit und erfordert keine gemeinsame Änderung anderer Intelligence-Entitäten. | Threat Technique | Intelligence Confidence; Threat Relevance |
| Threat Indicator Aggregate | Threat Indicator | Verantwortet die konsistente fachliche Aussage eines kuratierten Bedrohungshinweises. | Ein Indicator muss als eigenständige Intelligence-Aussage gültig bleiben, auch wenn andere Intelligence-Gegenstände unabhängig fortgeschrieben werden. | Threat Indicator | Intelligence Confidence; Indicator Classification; Threat Relevance |
| Threat Campaign Aggregate | Threat Campaign | Verantwortet die konsistente fachliche Aussage eines zusammenhängenden Bedrohungskontexts. | Eine Campaign besitzt einen eigenen fachlichen Lebenslauf und wird nicht mit einzelnen Intelligence-Gegenständen in eine gemeinsame Grenze gezogen. | Threat Campaign | Intelligence Confidence; Threat Relevance |

Alle vier Aggregate gehören ausschließlich zur Domäne **Threat Intelligence**.

## Threat Hunting

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Hunt Aggregate | Hunt | Verantwortet eine proaktive Untersuchung und die innerhalb dieser Untersuchung geführten Hypothesen. | Eine Hunt Hypothesis besitzt ihre fachliche Gültigkeit nur im Kontext des verantwortenden Hunt; beide müssen innerhalb derselben Grenze widerspruchsfrei bleiben. | Hunt; Hunt Hypothesis | Hunt Status; Hypothesis Disposition |

Das Aggregate gehört ausschließlich zur Domäne **Threat Hunting**.

## Incident Response

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Security Incident Aggregate | Security Incident | Verantwortet die fachlich konsistente Koordination eines Sicherheitsvorfalls. | Response Action, Incident Communication und Incident Review sind ausschließlich als koordinierte Bestandteile des konkreten Security Incident fachlich gültig und müssen dessen Response-Kontext respektieren. | Security Incident; Response Action; Incident Communication; Incident Review | Incident Severity; Response Phase; Response Action Status; Communication Status; Incident Outcome |

Das Aggregate gehört ausschließlich zur Domäne **Incident Response**.

## Decision Evidence

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Evidence Aggregate | Evidence | Verantwortet einen unveränderlichen, provenance-pflichtigen und entscheidungsrelevanten Nachweis. | Die fachliche Aussage, Art, Herkunft und Relevanz einer Evidence müssen als eine unteilbare Nachweisgrenze konsistent bleiben; ursprüngliche Quellobjekte liegen außerhalb. | Evidence | Evidence Kind; Evidence Provenance; Evidence Relevance |

Das Aggregate gehört ausschließlich zur Domäne **Decision Evidence** und bleibt ADR-0006 untergeordnet.

## Cyber Decision

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Decision Aggregate | Decision | Verantwortet eine fachliche Cyber-Entscheidung und ihr kanonisches abgeschlossenes Ergebnis. | Ein DecisionResult ist ausschließlich als Ergebnis der verantwortenden Decision fachlich gültig; der Abschluss muss eine widerspruchsfreie Decision-Aussage innerhalb einer Grenze sichern. | Decision; DecisionResult | Decision Priority; Decision Action; Attack Reasoning; Business Impact; Decision Confidence; Recommendation |

Das Aggregate gehört ausschließlich zur Domäne **Cyber Decision**. `DecisionResult` bleibt gemäß ADR-0001 die Single Source of Truth für das abgeschlossene fachliche Ergebnis.

## Enterprise Risk

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Enterprise Risk Aggregate | Enterprise Risk | Verantwortet den konsistenten fachlichen Lebenslauf eines Unternehmensrisikos einschließlich Behandlung und Annahme. | Risk Treatment und Risk Acceptance sind nur im Kontext des verantwortenden Enterprise Risk fachlich gültig; ihre Aussagen dürfen dessen Risikosteuerung nicht widersprechen. | Enterprise Risk; Risk Treatment; Risk Acceptance | Risk Rating; Risk Treatment Status; Risk Acceptance Rationale |

Das Aggregate gehört ausschließlich zur Domäne **Enterprise Risk**.

## Governance and Compliance

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Governance Policy Aggregate | Governance Policy | Verantwortet die konsistente Geltung einer Governance-Vorgabe, ihrer Controls und genehmigten Abweichungen. | Control und Governance Exception sind innerhalb dieser Grenze nur als Bestandteile der verantwortenden Governance Policy fachlich gültig. | Governance Policy; Control; Governance Exception | Control Effectiveness; Exception Rationale |
| Compliance Requirement Aggregate | Compliance Requirement | Verantwortet eine verbindliche Compliance-Anforderung und ihre fachliche Bewertung. | Eine Compliance Assessment besitzt ihre fachliche Bedeutung nur gegenüber der verantwortenden Compliance Requirement und muss mit deren Geltung konsistent bleiben. | Compliance Requirement; Compliance Assessment | Compliance Status |

Beide Aggregate gehören ausschließlich zur Domäne **Governance and Compliance**.

## Identity and Access

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Principal Aggregate | Principal | Verantwortet die konsistente fachliche Identität eines autorisierbaren Akteurs. | Der Principal bleibt unabhängig von Rollen-, Berechtigungs- und Regeldefinitionen gültig; gemeinsame Verwaltung würde getrennte Lebensläufe unnötig koppeln. | Principal | Keine |
| Access Role Aggregate | Access Role | Verantwortet die konsistente fachliche Bedeutung einer Zugriffsrolle. | Eine Access Role besitzt eine eigenständige Gültigkeit und wird nicht mit Principal oder Permission in eine gemeinsame Konsistenzgrenze verschmolzen. | Access Role | Access Scope |
| Permission Aggregate | Permission | Verantwortet die konsistente fachliche Bedeutung einer gewährbaren Berechtigung. | Eine Permission muss unabhängig von ihrer Nutzung in Rollen oder Regeln gültig bleiben. | Permission | Access Scope |
| Authorization Rule Aggregate | Authorization Rule | Verantwortet die konsistente fachliche Aussage einer verbindlichen Autorisierungsregel. | Eine Authorization Rule besitzt eine eigenständige Gültigkeit; ihre fachliche Aussage darf nicht durch den Lebenslauf eines Principal, einer Access Role oder Permission bestimmt werden. | Authorization Rule | Access Scope; Authorization Outcome |

Alle vier Aggregate gehören ausschließlich zur Domäne **Identity and Access**. Ihre mögliche fachliche Koordination ist keine Entscheidung dieses Dokuments.

## Data Integration

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Integration Aggregate | Integration | Verantwortet die konsistente Definition einer externen Anbindung, ihres technischen Zugangs und ihrer Quellherkunft. | Connector und Data Source sind innerhalb dieser Grenze nur als Bestandteile der verantwortenden Integration fachlich gültig; ihre Zuordnung muss widerspruchsfrei bleiben. | Integration; Connector; Data Source | Connector Status; Source Lineage |
| Synchronization Run Aggregate | Synchronization Run | Verantwortet die konsistente fachliche Aussage eines einzelnen Synchronisierungsvorgangs. | Ein Run muss nach seiner Ausführung unabhängig von Änderungen der Integrationsdefinition als eigener Vorgang gültig bleiben. | Synchronization Run | Synchronization Status; Source Lineage |
| Import Run Aggregate | Import Run | Verantwortet die konsistente fachliche Aussage eines einzelnen Importvorgangs. | Ein Import Run besitzt einen eigenständigen betrieblichen Lebenslauf und darf nicht mit einer veränderlichen Integrationsdefinition gekoppelt werden. | Import Run | Import Status; Source Lineage |

Alle drei Aggregate gehören ausschließlich zur Domäne **Data Integration**.

## Platform Operations

| Aggregate | Aggregate Root | Fachlicher Zweck | Begründung der Konsistenzgrenze | Enthaltene Canonical Entities | Verwendete Canonical Value Objects |
|---|---|---|---|---|---|
| Platform Service Aggregate | Platform Service | Verantwortet die konsistente betriebliche Aussage einer Plattformfähigkeit. | Ein Platform Service muss unabhängig von Konfigurationen, Jobs und Benachrichtigungen betrieblich adressierbar bleiben. | Platform Service | Platform Health; Service Status |
| Platform Configuration Aggregate | Platform Configuration | Verantwortet eine konsistente kontrollierte technische Plattformkonfiguration. | Eine Konfiguration besitzt eine eigene betriebliche Gültigkeit und wird nicht mit anderen Betriebsgegenständen zu einer gemeinsamen Grenze verbunden. | Platform Configuration | Keine |
| Background Job Aggregate | Background Job | Verantwortet die konsistente betriebliche Aussage eines asynchronen Plattformvorgangs. | Ein Background Job besitzt einen eigenständigen Lebenslauf und bleibt unabhängig von Service- oder Konfigurationsänderungen nachvollziehbar. | Background Job | Job Status |
| System Notification Aggregate | System Notification | Verantwortet die konsistente betriebliche Aussage einer technischen Plattformmitteilung. | Eine System Notification ist unabhängig adressierbar und erfordert keine gemeinsame Konsistenz mit ihrem dargestellten Betriebskontext. | System Notification | Notification Severity |
| Audit Record Aggregate | Audit Record | Verantwortet einen unveränderlichen betrieblichen Auditnachweis. | Ein Audit Record muss nach seiner Feststellung als eigenständige Nachweisgrenze unverändert bleiben und darf nicht mit veränderlichen Betriebsobjekten gekoppelt werden. | Audit Record | Keine |
| Feature Flag Aggregate | Feature Flag | Verantwortet die konsistente betriebliche Freigabe einer Plattformfähigkeit. | Ein Feature Flag besitzt eine eigenständige kontrollierte Gültigkeit und wird nicht mit Platform Configuration verschmolzen. | Feature Flag | Feature State |
| License Aggregate | License | Verantwortet die konsistente betriebliche Nutzungsberechtigung der Plattform. | Eine License besitzt einen eigenständigen Lebenslauf und muss unabhängig von Service- und Konfigurationszuständen gültig bleiben. | License | License Status |

Alle sieben Aggregate gehören ausschließlich zur Domäne **Platform Operations**.

## Vollständige Entity-Zuordnung

Diese Matrix dient ausschließlich dem Nachweis, dass jede Canonical Entity höchstens einer Aggregate-Grenze zugeordnet ist. Sie modelliert keine Beziehungen.

| Canonical Entity | Owner-Domäne | Zugeordnetes Aggregate | Aggregate Root |
|---|---|---|---|
| Asset | Enterprise Context | Asset Context Aggregate | Asset |
| Business Service | Enterprise Context | Business Service Context Aggregate | Business Service |
| Organizational Unit | Enterprise Context | Organizational Unit Context Aggregate | Organizational Unit |
| Finding | Security Observation | Finding Aggregate | Finding |
| Alert | Security Observation | Alert Aggregate | Alert |
| Exposure | Security Observation | Exposure Aggregate | Exposure |
| Threat Actor | Threat Intelligence | Threat Actor Aggregate | Threat Actor |
| Threat Technique | Threat Intelligence | Threat Technique Aggregate | Threat Technique |
| Threat Indicator | Threat Intelligence | Threat Indicator Aggregate | Threat Indicator |
| Threat Campaign | Threat Intelligence | Threat Campaign Aggregate | Threat Campaign |
| Hunt | Threat Hunting | Hunt Aggregate | Hunt |
| Hunt Hypothesis | Threat Hunting | Hunt Aggregate | Hunt |
| Security Incident | Incident Response | Security Incident Aggregate | Security Incident |
| Response Action | Incident Response | Security Incident Aggregate | Security Incident |
| Incident Communication | Incident Response | Security Incident Aggregate | Security Incident |
| Incident Review | Incident Response | Security Incident Aggregate | Security Incident |
| Evidence | Decision Evidence | Evidence Aggregate | Evidence |
| Decision | Cyber Decision | Decision Aggregate | Decision |
| DecisionResult | Cyber Decision | Decision Aggregate | Decision |
| Enterprise Risk | Enterprise Risk | Enterprise Risk Aggregate | Enterprise Risk |
| Risk Treatment | Enterprise Risk | Enterprise Risk Aggregate | Enterprise Risk |
| Risk Acceptance | Enterprise Risk | Enterprise Risk Aggregate | Enterprise Risk |
| Governance Policy | Governance and Compliance | Governance Policy Aggregate | Governance Policy |
| Control | Governance and Compliance | Governance Policy Aggregate | Governance Policy |
| Compliance Requirement | Governance and Compliance | Compliance Requirement Aggregate | Compliance Requirement |
| Governance Exception | Governance and Compliance | Governance Policy Aggregate | Governance Policy |
| Compliance Assessment | Governance and Compliance | Compliance Requirement Aggregate | Compliance Requirement |
| Principal | Identity and Access | Principal Aggregate | Principal |
| Access Role | Identity and Access | Access Role Aggregate | Access Role |
| Permission | Identity and Access | Permission Aggregate | Permission |
| Authorization Rule | Identity and Access | Authorization Rule Aggregate | Authorization Rule |
| Integration | Data Integration | Integration Aggregate | Integration |
| Connector | Data Integration | Integration Aggregate | Integration |
| Data Source | Data Integration | Integration Aggregate | Integration |
| Synchronization Run | Data Integration | Synchronization Run Aggregate | Synchronization Run |
| Import Run | Data Integration | Import Run Aggregate | Import Run |
| Platform Service | Platform Operations | Platform Service Aggregate | Platform Service |
| Platform Configuration | Platform Operations | Platform Configuration Aggregate | Platform Configuration |
| Background Job | Platform Operations | Background Job Aggregate | Background Job |
| System Notification | Platform Operations | System Notification Aggregate | System Notification |
| Audit Record | Platform Operations | Audit Record Aggregate | Audit Record |
| Feature Flag | Platform Operations | Feature Flag Aggregate | Feature Flag |
| License | Platform Operations | License Aggregate | License |

## Nicht zugeordnete Canonical Entities

Keine. Alle 43 Canonical Entities sind genau einer Aggregate-Grenze zugeordnet. Diese vollständige Zuordnung bedeutet nicht, dass alle Aggregate miteinander verbunden sind oder gemeinsam koordiniert werden.

## Wiederverwendung von Canonical Value Objects

Value Objects dürfen von mehreren Aggregaten ihrer Owner-Domäne verwendet werden. In diesem Artefakt betrifft dies insbesondere `Observation Severity`, `Observation Disposition`, `Intelligence Confidence`, `Threat Relevance`, `Access Scope`, `Source Lineage` und `Platform Health`. Die Wiederverwendung begründet keine gemeinsame Konsistenzgrenze und keine Beziehung zwischen den betreffenden Aggregaten.

## Nicht Bestandteil

Dieses Dokument definiert keine Attribute, Felder, Methoden, Geschäftslogik, Invarianten, Validierungsregeln, Repositorys, Persistenz, Datenbanken, APIs, DTOs, Domain Services, Application Services, Domain Events, Beziehungen, Referenzen, Kardinalitäten, Datenflüsse, Netzwerkkommunikation, Module, Packages, Transaktionen, Deployments oder Produktimplementierungen.

## Statische Konsistenzprüfung

* 31 Aggregate besitzen jeweils genau einen eindeutigen Namen, eine Owner-Domäne und eine Aggregate Root.
* Alle Aggregate Roots stammen aus dem Canonical-Entity-Katalog.
* Alle 43 Canonical Entities sind genau einmal zugeordnet.
* Keine Aggregate-Grenze überschreitet eine Domain Boundary.
* Verwendete Value Objects stammen aus dem bestehenden Katalog und der jeweiligen Owner-Domäne.
* Gemeinsam verwendete Value Objects begründen keine Entity- oder Aggregate-Beziehung.
* Beziehungen zwischen Aggregaten und technische Implementierungsdetails bleiben unmodelliert.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-OWNERSHIP-AND-RESPONSIBILITIES.md`
* `.ai/architecture/CANONICAL-ENTITIES.md`
* `.ai/architecture/CANONICAL-VALUE-OBJECTS.md`
* `ARCHITECTURE.md`
* `.ai/decisions/ADR-0001-decision-result.md`
* `.ai/decisions/ADR-0002-execution-trace.md`
* `.ai/decisions/ADR-0003-explainability-projection.md`
* `.ai/decisions/ADR-0004-explainability-completeness.md`
* `.ai/decisions/ADR-0005-mission-console-workspace-architecture.md`
* `.ai/decisions/ADR-0006-decision-evidence-architecture.md`
* `.ai/tasks/done/TASK-0031.md`

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
