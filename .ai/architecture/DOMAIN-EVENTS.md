# PredatorAI v3 – Domain Events Catalog

## Status

APPROVED – Architecture Baseline 1.0

## Datum

2026-08-05

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Zweck

Dieses Dokument katalogisiert die fachlich erforderlichen Domain Events von PredatorAI. Ein Domain Event beschreibt eine fachlich bedeutsame, bereits eingetretene Zustandsänderung innerhalb genau eines auslösenden Aggregates und genau einer produzierenden Domain.

Der Katalog definiert ausschließlich fachliche Bedeutung, zulässige Konsumenten, Konsistenz und Kausalität. Er definiert weder technische Veröffentlichung noch Transport, Speicherung oder Verarbeitung.

## Aufnahmeregeln

Ein Ereignis wird nur als kanonisches Domain Event aufgenommen, wenn:

1. eine bestehende Aggregate Root eine fachlich bedeutsame Zustandsänderung abgeschlossen hat,
2. diese Tatsache aufgrund einer bestehenden Aggregate-Beziehung für eine andere Domain relevant ist oder eine nachweisbare domäneninterne Koordination betrifft,
3. Produzent, auslösendes Aggregate und zulässige Konsumenten aus den bestehenden Architekturartefakten ableitbar sind,
4. das Ereignis keine Anweisung, keine technische Nachricht und keine zweite fachliche Wahrheit darstellt.

Bloße Anlage, Änderung oder Löschung ohne belegte fachliche Folgewirkung begründet kein eigenes Domain Event. Ein Event überträgt keine Ownership; fachliche Konsumenten entscheiden innerhalb ihrer eigenen Aggregate- und Policy-Grenzen, ob und wie die eingetretene Tatsache berücksichtigt wird.

## Katalogübersicht

| ID | Domain Event | Produzierende Domain | Auslösendes Aggregate | Reichweite |
|---|---|---|---|---|
| EVT-001 | Integration Context Established | Data Integration | Integration Aggregate | domänenübergreifend |
| EVT-002 | Asset Context Classified | Enterprise Context | Asset Context Aggregate | domänenübergreifend |
| EVT-003 | Business Service Context Classified | Enterprise Context | Business Service Context Aggregate | domänenübergreifend |
| EVT-004 | Organizational Context Established | Enterprise Context | Organizational Unit Context Aggregate | domänenübergreifend |
| EVT-005 | Threat Indicator Assessed | Threat Intelligence | Threat Indicator Aggregate | domänenübergreifend |
| EVT-006 | Threat Technique Assessed | Threat Intelligence | Threat Technique Aggregate | domänenübergreifend |
| EVT-007 | Finding Established | Security Observation | Finding Aggregate | domänenübergreifend |
| EVT-008 | Alert Established | Security Observation | Alert Aggregate | domänenübergreifend |
| EVT-009 | Exposure Established | Security Observation | Exposure Aggregate | domänenübergreifend |
| EVT-010 | Hunt Concluded | Threat Hunting | Hunt Aggregate | domänenübergreifend |
| EVT-011 | Governance Policy Changed | Governance and Compliance | Governance Policy Aggregate | domänenübergreifend |
| EVT-012 | Compliance Requirement Assessed | Governance and Compliance | Compliance Requirement Aggregate | domänenintern |
| EVT-013 | Evidence Qualified | Decision Evidence | Evidence Aggregate | domänenübergreifend |
| EVT-014 | Decision Completed | Cyber Decision | Decision Aggregate | domänenübergreifend |
| EVT-015 | Authorization Rule Changed | Identity and Access | Authorization Rule Aggregate | domänenübergreifend |
| EVT-016 | Incident Response Phase Changed | Incident Response | Security Incident Aggregate | domänenintern |
| EVT-017 | Enterprise Risk Treatment Decided | Enterprise Risk | Enterprise Risk Aggregate | domänenintern |

## EVT-001 – Integration Context Established

**Produzierende Domain:** Data Integration  
**Auslösendes Aggregate:** Integration Aggregate  
**Fachliche Bedeutung:** Eine externe Anbindung besitzt nun eine widerspruchsfreie Integrationsdefinition und autoritative Source Lineage.  
**Fachlicher Auslöser:** Das Integration Aggregate hat die fachliche Zuordnung von Integration, Connector, Data Source und Herkunft abgeschlossen.  
**Betroffene Aggregate:** Asset Context Aggregate; Threat Actor Aggregate; Threat Technique Aggregate; Threat Indicator Aggregate; Threat Campaign Aggregate; Platform Service Aggregate.  
**Zulässige fachliche Konsumenten:** Enterprise Context für Asset-Herkunft; Threat Intelligence für Intelligence-Herkunft; Platform Operations für den autoritativen Integrationszustand.  
**Ausdrücklich unzulässige Konsumenten:** Alle übrigen Domains; insbesondere Decision Evidence und Cyber Decision dürfen eine Integrationsdefinition nicht unmittelbar als fachlichen Nachweis oder Decision-Eingang verwenden.  
**Fachliche Konsistenzregeln:** Data Integration behält Definition und Lineage. Konsumenten dürfen diese nur referenzieren und nicht umdeuten. Die Data Intake Coordination bleibt beim Data Intake Coordination Service; das Event ersetzt sie nicht.  
**Reihenfolge/Kausalität:** Das Event folgt kausal auf die abgeschlossene Konsistenzentscheidung des Integration Aggregate. Spätere Context- oder Intelligence-Aussagen dürfen es nutzen, sind aber keine automatische Folge.  
**Fachliche Begründung:** REL-001 bis REL-005 und REL-039 belegen die fachliche Relevanz des Integration Aggregate für genau diese Konsumenten.

## EVT-002 – Asset Context Classified

**Produzierende Domain:** Enterprise Context  
**Auslösendes Aggregate:** Asset Context Aggregate  
**Fachliche Bedeutung:** Die fachliche Identität und Schutzrelevanz eines Assets sind autoritativ eingeordnet.  
**Fachlicher Auslöser:** Das Asset Context Aggregate hat seine Context-Aussage einschließlich vorhandener Kritikalität widerspruchsfrei festgestellt.  
**Betroffene Aggregate:** Finding Aggregate; Alert Aggregate; Exposure Aggregate; Security Incident Aggregate.  
**Zulässige fachliche Konsumenten:** Security Observation und Incident Response gemäß ihren bestehenden Asset-Referenzen.  
**Ausdrücklich unzulässige Konsumenten:** Domains ohne erlaubte Abhängigkeit zu Enterprise Context sowie Konsumenten, die Asset-Ownership übernehmen oder Kritikalität neu bestimmen würden.  
**Fachliche Konsistenzregeln:** Das Asset Context Aggregate bleibt alleiniger Owner. Die Authoritative Context Classification Policy gilt; fehlende Context-Aussagen werden nicht plausibilisiert.  
**Reihenfolge/Kausalität:** Die Klassifikation muss fachlich abgeschlossen sein, bevor sie als autoritativer Kontext genutzt wird. Findings, Alerts, Exposures oder Incidents entstehen dadurch nicht automatisch.  
**Fachliche Begründung:** REL-006 bis REL-008 und REL-029 verlangen einen unveränderten autoritativen Asset-Kontext.

## EVT-003 – Business Service Context Classified

**Produzierende Domain:** Enterprise Context  
**Auslösendes Aggregate:** Business Service Context Aggregate  
**Fachliche Bedeutung:** Identität und geschäftliche Schutzrelevanz eines Business Service sind autoritativ eingeordnet.  
**Fachlicher Auslöser:** Das Business Service Context Aggregate hat seine fachliche Context-Aussage widerspruchsfrei abgeschlossen.  
**Betroffene Aggregate:** Compliance Requirement Aggregate; Decision Aggregate; Enterprise Risk Aggregate.  
**Zulässige fachliche Konsumenten:** Governance and Compliance, Cyber Decision und Enterprise Risk.  
**Ausdrücklich unzulässige Konsumenten:** Domains ohne erlaubte Business-Service-Beziehung sowie jede Darstellung, die selbst Business Impact oder Kritikalität erzeugen würde.  
**Fachliche Konsistenzregeln:** Enterprise Context behält Ownership. Konsumenten berücksichtigen nur vorhandene Aussagen gemäß ihrer eigenen Services und Policies.  
**Reihenfolge/Kausalität:** Die autoritative Context-Aussage geht ihrer Nutzung in Compliance, Decision oder Risk fachlich voraus; sie löst keine automatische Neubewertung aus.  
**Fachliche Begründung:** REL-017, REL-026 und REL-033 belegen die gemeinsame, gerichtete Nutzung des Business Service Context Aggregate.

## EVT-004 – Organizational Context Established

**Produzierende Domain:** Enterprise Context  
**Auslösendes Aggregate:** Organizational Unit Context Aggregate  
**Fachliche Bedeutung:** Eine Organisationseinheit besitzt eine autoritative fachliche Identität und kann als Geltungsbereich referenziert werden.  
**Fachlicher Auslöser:** Das Organizational Unit Context Aggregate hat seine eigenständige Context-Aussage abgeschlossen.  
**Betroffene Aggregate:** Governance Policy Aggregate; Principal Aggregate; Authorization Rule Aggregate.  
**Zulässige fachliche Konsumenten:** Governance and Compliance sowie Identity and Access.  
**Ausdrücklich unzulässige Konsumenten:** Domains ohne erlaubte Organisationsbeziehung sowie Workspaces als vermeintliche Owner organisatorischer Identität.  
**Fachliche Konsistenzregeln:** Die Organisationseinheit bleibt Eigentum von Enterprise Context. Governance- und Autorisierungsaussagen dürfen ausschließlich referenzieren.  
**Reihenfolge/Kausalität:** Der autoritative Kontext muss vor seiner fachlichen Verwendung bestehen; weder Policy noch Principal oder Authorization Rule entstehen automatisch.  
**Fachliche Begründung:** REL-016, REL-035 und REL-036 verlangen eine stabile organisatorische Referenz.

## EVT-005 – Threat Indicator Assessed

**Produzierende Domain:** Threat Intelligence  
**Auslösendes Aggregate:** Threat Indicator Aggregate  
**Fachliche Bedeutung:** Ein Threat Indicator besitzt eine autoritative, hinsichtlich Relevanz und vorhandener Herkunft bewertete Intelligence-Aussage.  
**Fachlicher Auslöser:** Das Threat Indicator Aggregate hat seine eigenständige fachliche Bewertung abgeschlossen.  
**Betroffene Aggregate:** Finding Aggregate; Alert Aggregate; Exposure Aggregate; Hunt Aggregate; Evidence Aggregate.  
**Zulässige fachliche Konsumenten:** Security Observation, Threat Hunting und Decision Evidence.  
**Ausdrücklich unzulässige Konsumenten:** Cyber Decision als direkter Konsument sowie jede Domain ohne erlaubte Abhängigkeit zu Threat Intelligence.  
**Fachliche Konsistenzregeln:** Die Intelligence Provenance and Assessment Integrity Policy gilt. Konsumenten dürfen die Indicator-Aussage nicht verändern; Decision Evidence muss eine eigene qualifizierte Evidence-Aussage erzeugen.  
**Reihenfolge/Kausalität:** Die Bewertung geht ihrer Verwendung als Kontext, Hunting-Grundlage oder Evidence-Quelle voraus. Sie erzeugt keine Observation, keinen Hunt und keine Evidence automatisch.  
**Fachliche Begründung:** REL-009 bis REL-011, REL-014 und REL-022 belegen die fachliche Wirkung.

## EVT-006 – Threat Technique Assessed

**Produzierende Domain:** Threat Intelligence  
**Auslösendes Aggregate:** Threat Technique Aggregate  
**Fachliche Bedeutung:** Eine Threat Technique besitzt eine autoritative, eigenständig gültige Intelligence-Bewertung.  
**Fachlicher Auslöser:** Das Threat Technique Aggregate hat seine fachliche Einordnung abgeschlossen.  
**Betroffene Aggregate:** Hunt Aggregate.  
**Zulässige fachliche Konsumenten:** Threat Hunting.  
**Ausdrücklich unzulässige Konsumenten:** Alle übrigen Domains, insbesondere Cyber Decision und Decision Evidence ohne definierte direkte Technique-Beziehung.  
**Fachliche Konsistenzregeln:** Threat Intelligence bleibt Owner; der Hunt darf die Technique ausschließlich als kanonisches Vokabular nutzen.  
**Reihenfolge/Kausalität:** Die bewertete Technique kann einer Hunt-Bewertung vorausgehen, begründet aber keinen Hunt-Lifecycle.  
**Fachliche Begründung:** REL-015 belegt genau diese gerichtete fachliche Nutzung.

## EVT-007 – Finding Established

**Produzierende Domain:** Security Observation  
**Auslösendes Aggregate:** Finding Aggregate  
**Fachliche Bedeutung:** Eine autoritative Security-Feststellung ist fachlich gültig festgestellt.  
**Fachlicher Auslöser:** Das Finding Aggregate hat seine eigenständige Beobachtungsaussage konsistent abgeschlossen.  
**Betroffene Aggregate:** Hunt Aggregate; Compliance Requirement Aggregate; Evidence Aggregate; Security Incident Aggregate.  
**Zulässige fachliche Konsumenten:** Threat Hunting, Governance and Compliance, Decision Evidence und Incident Response.  
**Ausdrücklich unzulässige Konsumenten:** Cyber Decision als direkter Konsument und alle Domains ohne erlaubte Finding-Beziehung.  
**Fachliche Konsistenzregeln:** Die Observation Correlation Integrity Policy gilt. Das Finding bleibt bei Security Observation; andere Domains untersuchen, bewerten, qualifizieren oder referenzieren es ausschließlich innerhalb ihrer Grenzen.  
**Reihenfolge/Kausalität:** Das Finding muss bestehen, bevor es konsumiert wird. Es erzeugt weder Hunt, Compliance Assessment, Evidence noch Incident automatisch.  
**Fachliche Begründung:** REL-012, REL-018, REL-019 und REL-028 belegen vier zulässige fachliche Folgewirkungen.

## EVT-008 – Alert Established

**Produzierende Domain:** Security Observation  
**Auslösendes Aggregate:** Alert Aggregate  
**Fachliche Bedeutung:** Ein autoritativer prüfungsbedürftiger Sicherheitshinweis ist fachlich gültig festgestellt.  
**Fachlicher Auslöser:** Das Alert Aggregate hat seine eigenständige Beobachtungsaussage konsistent abgeschlossen.  
**Betroffene Aggregate:** Hunt Aggregate; Evidence Aggregate.  
**Zulässige fachliche Konsumenten:** Threat Hunting und Decision Evidence.  
**Ausdrücklich unzulässige Konsumenten:** Incident Response ohne definierte Alert-Beziehung, Cyber Decision als direkter Konsument und alle übrigen Domains.  
**Fachliche Konsistenzregeln:** Alert-Ownership verbleibt bei Security Observation. Hunting und Evidence-Qualifikation dürfen die Aussage weder umdeuten noch ihren Lebenslauf übernehmen.  
**Reihenfolge/Kausalität:** Ein Alert geht einer möglichen Untersuchung oder Evidence-Qualifikation voraus, löst beides aber nicht automatisch aus.  
**Fachliche Begründung:** REL-013 und REL-020 belegen die zulässigen Konsumenten.

## EVT-009 – Exposure Established

**Produzierende Domain:** Security Observation  
**Auslösendes Aggregate:** Exposure Aggregate  
**Fachliche Bedeutung:** Ein autoritativer exponierter Sicherheitszustand ist fachlich gültig festgestellt.  
**Fachlicher Auslöser:** Das Exposure Aggregate hat seine eigenständige Beobachtungsaussage konsistent abgeschlossen.  
**Betroffene Aggregate:** Evidence Aggregate.  
**Zulässige fachliche Konsumenten:** Decision Evidence.  
**Ausdrücklich unzulässige Konsumenten:** Cyber Decision als direkter Konsument sowie alle Domains ohne definierte Exposure-Beziehung.  
**Fachliche Konsistenzregeln:** Exposure-Ownership verbleibt bei Security Observation. Der Decision Evidence Qualification Service entscheidet getrennt über die Evidence-Eignung.  
**Reihenfolge/Kausalität:** Das Exposure muss der Evidence-Qualifikation vorausgehen; Evidence entsteht nicht automatisch.  
**Fachliche Begründung:** REL-021 belegt die einzige domänenübergreifende fachliche Folgewirkung.

## EVT-010 – Hunt Concluded

**Produzierende Domain:** Threat Hunting  
**Auslösendes Aggregate:** Hunt Aggregate  
**Fachliche Bedeutung:** Eine proaktive Untersuchung und ihre Hypothesen besitzen ein fachlich abgeschlossenes Untersuchungsergebnis.  
**Fachlicher Auslöser:** Das Hunt Aggregate hat den Hunt-Lifecycle mit einer konsistenten Hypothesen-Disposition abgeschlossen.  
**Betroffene Aggregate:** Evidence Aggregate.  
**Zulässige fachliche Konsumenten:** Decision Evidence.  
**Ausdrücklich unzulässige Konsumenten:** Cyber Decision als direkter Konsument sowie Domains ohne definierte Hunt-Beziehung.  
**Fachliche Konsistenzregeln:** Hunt und Hypothese bleiben Eigentum von Threat Hunting. Nur der Decision Evidence Qualification Service darf ein vorhandenes Ergebnis als Evidence-Quelle qualifizieren.  
**Reihenfolge/Kausalität:** Der Hunt-Abschluss muss einer möglichen Evidence-Qualifikation vorausgehen. Weder Evidence noch Decision folgen automatisch.  
**Fachliche Begründung:** REL-023 belegt die fachliche Relevanz eines Hunt-Ergebnisses für Decision Evidence.

## EVT-011 – Governance Policy Changed

**Produzierende Domain:** Governance and Compliance  
**Auslösendes Aggregate:** Governance Policy Aggregate  
**Fachliche Bedeutung:** Die autoritative Geltung einer Governance Policy einschließlich ihrer Controls und genehmigten Exceptions hat sich fachlich wirksam geändert.  
**Fachlicher Auslöser:** Das Governance Policy Aggregate hat eine Änderung seiner konsistenten Policy-Aussage abgeschlossen.  
**Betroffene Aggregate:** Evidence Aggregate; Decision Aggregate; Enterprise Risk Aggregate.  
**Zulässige fachliche Konsumenten:** Decision Evidence, Cyber Decision und Enterprise Risk.  
**Ausdrücklich unzulässige Konsumenten:** Domains ohne erlaubte Governance-Policy-Beziehung; insbesondere darf Incident Response keine Policy unmittelbar als eigene Handlungsentscheidung behandeln.  
**Fachliche Konsistenzregeln:** Die Governance Applicability and Exception Integrity Policy gilt. Governance and Compliance bleibt Owner; eine Exception wird weder zu Risk Acceptance noch DecisionResult.  
**Reihenfolge/Kausalität:** Die wirksame Policy-Aussage muss ihrer Berücksichtigung als Evidence-Grundlage, Decision-Vorgabe oder Risk-Vorgabe vorausgehen. Eine Neubewertung erfolgt nicht automatisch.  
**Fachliche Begründung:** REL-024, REL-027 und REL-034 belegen die zulässigen fachlichen Auswirkungen.

## EVT-012 – Compliance Requirement Assessed

**Produzierende Domain:** Governance and Compliance  
**Auslösendes Aggregate:** Compliance Requirement Aggregate  
**Fachliche Bedeutung:** Eine Compliance Requirement besitzt eine fachlich konsistente Bewertung gegenüber ihrem autoritativen Geltungsbereich.  
**Fachlicher Auslöser:** Das Compliance Requirement Aggregate hat sein Compliance Assessment abgeschlossen.  
**Betroffene Aggregate:** Governance Policy Aggregate ausschließlich zur domäneninternen koordinierten Bewertung.  
**Zulässige fachliche Konsumenten:** Ausschließlich Governance and Compliance, insbesondere der Governance Compliance Evaluation Service.  
**Ausdrücklich unzulässige Konsumenten:** Alle anderen Domains; es besteht keine freigegebene Cross-Domain-Beziehung, die Compliance Assessment als direkte Quelle verwendet.  
**Fachliche Konsistenzregeln:** Requirement und Assessment verbleiben im Compliance Requirement Aggregate. Der Service darf die Aussage mit Governance-Vorgaben koordinieren, aber keine Aggregate-Grenzen verschmelzen.  
**Reihenfolge/Kausalität:** Das Event folgt auf den Abschluss des Assessments. Eine besondere Reihenfolge zu anderen Aggregates ist nicht erforderlich.  
**Fachliche Begründung:** Der Governance Compliance Evaluation Service koordiniert Governance Policy und Compliance Requirement; der Bewertungsabschluss ist daher innerhalb der Owner Domain fachlich relevant.

## EVT-013 – Evidence Qualified

**Produzierende Domain:** Decision Evidence  
**Auslösendes Aggregate:** Evidence Aggregate  
**Fachliche Bedeutung:** Eine vorhandene autoritative Quellaussage ist als unveränderliche, provenance-pflichtige und entscheidungsrelevante Evidence qualifiziert.  
**Fachlicher Auslöser:** Das Evidence Aggregate hat Art, Herkunft, Relevanz und Aussage als unteilbare Nachweisgrenze abgeschlossen.  
**Betroffene Aggregate:** Decision Aggregate; Security Incident Aggregate.  
**Zulässige fachliche Konsumenten:** Cyber Decision und Incident Response.  
**Ausdrücklich unzulässige Konsumenten:** Source Domains als Rückschreibeziel, Enterprise Risk ohne direkte Evidence-Abhängigkeit sowie Explainability als vermeintlicher Fakten-Owner.  
**Fachliche Konsistenzregeln:** Die Evidence Admissibility and Provenance Policy und ADR-0006 gelten. Evidence bleibt unverändert; Konsumenten dürfen Herkunft und Aussage nicht überschreiben.  
**Reihenfolge/Kausalität:** Evidence-Qualifikation folgt auf eine vorhandene Source-Aussage und geht ihrer Nutzung durch Decision oder Incident voraus. Sie löst weder Decision noch Response automatisch aus.  
**Fachliche Begründung:** REL-025 und REL-030 belegen die gerichtete Nutzung qualifizierter Evidence.

## EVT-014 – Decision Completed

**Produzierende Domain:** Cyber Decision  
**Auslösendes Aggregate:** Decision Aggregate  
**Fachliche Bedeutung:** Eine Cyber Decision ist abgeschlossen und besitzt genau ein kanonisches `DecisionResult` mit dem exakt verwendeten Evidence-Snapshot.  
**Fachlicher Auslöser:** Das Decision Aggregate hat seinen Decision-Lifecycle gemäß der Canonical Decision Basis Policy konsistent abgeschlossen.  
**Betroffene Aggregate:** Security Incident Aggregate; Enterprise Risk Aggregate.  
**Zulässige fachliche Konsumenten:** Incident Response und Enterprise Risk.  
**Ausdrücklich unzulässige Konsumenten:** Vorgelagerte Source- und Evidence-Domains als Rückschreibeziel sowie jede Komponente, die ein paralleles Decision-Ergebnis erzeugen würde.  
**Fachliche Konsistenzregeln:** ADR-0001 bis ADR-0004 gelten: `DecisionResult` bleibt Single Source of Truth; Explainability ist read-only; Execution Trace und Evidence bleiben getrennt.  
**Reihenfolge/Kausalität:** Das Event folgt auf die abgeschlossene Decision und ihre qualifizierte Evidence-Basis. Incident Response oder Enterprise Risk können es anschließend berücksichtigen, werden aber nicht automatisch verändert.  
**Fachliche Begründung:** REL-031 und REL-032 belegen die fachliche Relevanz einer abgeschlossenen Decision für Response und langfristige Risikosteuerung.

## EVT-015 – Authorization Rule Changed

**Produzierende Domain:** Identity and Access  
**Auslösendes Aggregate:** Authorization Rule Aggregate  
**Fachliche Bedeutung:** Eine verbindliche Autorisierungsregel besitzt eine fachlich wirksame, konsistente Aussage innerhalb ihres organisatorischen Geltungsbereichs.  
**Fachlicher Auslöser:** Das Authorization Rule Aggregate hat eine Änderung seiner Regel-Aussage abgeschlossen.  
**Betroffene Aggregate:** Platform Configuration Aggregate; Background Job Aggregate.  
**Zulässige fachliche Konsumenten:** Platform Operations für kontrollierte Konfigurations- und betriebliche Verantwortung.  
**Ausdrücklich unzulässige Konsumenten:** Workspaces als Autorisierungs-Owner sowie alle Domains ohne definierte Abhängigkeit zu Identity and Access.  
**Fachliche Konsistenzregeln:** Die Contextual Authorization Policy gilt. Identity and Access bleibt Owner; Platform Operations definiert oder verändert keine Authorization Rule.  
**Reihenfolge/Kausalität:** Die wirksame Regel geht ihrer Berücksichtigung durch Platform Operations voraus. Sie löst keine Konfigurationsänderung und keinen Background Job automatisch aus.  
**Fachliche Begründung:** REL-037 und REL-038 belegen die einzige zulässige fachliche Cross-Domain-Wirkung einer Authorization Rule.

## EVT-016 – Incident Response Phase Changed

**Produzierende Domain:** Incident Response  
**Auslösendes Aggregate:** Security Incident Aggregate  
**Fachliche Bedeutung:** Ein Security Incident ist konsistent in eine andere fachliche Response-Phase übergegangen.  
**Fachlicher Auslöser:** Das Security Incident Aggregate hat den Phasenwechsel unter Berücksichtigung seiner Response Actions, Communications und Reviews abgeschlossen.  
**Betroffene Aggregate:** Keine außerhalb des Security Incident Aggregate.  
**Zulässige fachliche Konsumenten:** Ausschließlich Incident Response innerhalb des Security Incident Aggregate.  
**Ausdrücklich unzulässige Konsumenten:** Alle anderen Domains; keine Domain besitzt eine erlaubte Abhängigkeit von Incident Response.  
**Fachliche Konsistenzregeln:** Response Phase, Actions, Communication und Review bleiben in einer Aggregate-Grenze. Das Event ersetzt keine Aggregate-Invariante und ändert weder Finding, Evidence noch Decision.  
**Reihenfolge/Kausalität:** Phasenwechsel sind innerhalb des Incident-Lifecycles kausal geordnet. Der Katalog definiert keine technische Reihenfolge.  
**Fachliche Begründung:** Die Phasenänderung ist für die koordinierte Response fachlich bedeutsam, besitzt aber gemäß Domain Dependencies keine domänenübergreifende Wirkung.

## EVT-017 – Enterprise Risk Treatment Decided

**Produzierende Domain:** Enterprise Risk  
**Auslösendes Aggregate:** Enterprise Risk Aggregate  
**Fachliche Bedeutung:** Für ein Enterprise Risk ist eine fachlich konsistente Treatment- oder Acceptance-Entscheidung getroffen worden.  
**Fachlicher Auslöser:** Das Enterprise Risk Aggregate hat die Entscheidung innerhalb seiner Risk-Ownership und seines Lebenslaufs abgeschlossen.  
**Betroffene Aggregate:** Keine außerhalb des Enterprise Risk Aggregate.  
**Zulässige fachliche Konsumenten:** Ausschließlich Enterprise Risk innerhalb des Enterprise Risk Aggregate und der Enterprise Risk Assessment Service für domäneninterne vergleichende Bewertung.  
**Ausdrücklich unzulässige Konsumenten:** Alle anderen Domains; insbesondere dürfen Cyber Decision und Governance and Compliance die Risikobehandlung nicht rückwirkend übernehmen.  
**Fachliche Konsistenzregeln:** Die Risk Ownership and Treatment Authority Policy gilt. Treatment und Acceptance verbleiben beim Enterprise Risk Aggregate; konsumierte Decisions, Contexts und Policies bleiben unverändert.  
**Reihenfolge/Kausalität:** Die Entscheidung folgt auf eine vorhandene Risk-Bewertung. Eine besondere Kausalität außerhalb des Risk-Lifecycles ist nicht freigegeben.  
**Fachliche Begründung:** Die abgeschlossene Treatment- oder Acceptance-Entscheidung ist innerhalb der langfristigen Risikosteuerung bedeutsam, ohne eine erlaubte Rückabhängigkeit zu begründen.

## Domains ohne veröffentlichte Domain Events

### Platform Operations

**Ergebnis:** Keine fachlichen Domain Events im aktuellen Katalog.

**Begründung:** Die bestehenden Platform-Operations-Aggregate beschreiben voneinander unabhängige technische Betriebszustände. Für keinen ihrer Zustandswechsel ist eine fachliche Konsumption durch eine andere Domain belegt; keine Domain darf von Platform Operations abhängen. Ein vermeintliches Health-, Job-, Notification-, Audit-, Feature- oder License-Event würde im aktuellen Scope entweder nur eine Aggregate-interne technische Zustandsänderung wiederholen oder eine nicht freigegebene technische Event- beziehungsweise Infrastruktursemantik einführen.

Alle übrigen elf Domains besitzen mindestens ein fachlich begründetes Event. Diese Abdeckung bedeutet nicht, dass jede Aggregate-Änderung veröffentlicht wird.

## Aggregates ohne eigenständiges Domain Event

Für folgende Aggregates ist kein zusätzliches kanonisches Event erforderlich:

* **Threat Actor Aggregate und Threat Campaign Aggregate:** Keine bestehende Aggregate Relationship weist einen fachlichen Konsumenten ihrer Zustandsänderungen aus. Ihre Bewertung bleibt innerhalb der jeweiligen Aggregate-Grenze und der Koordination des Threat Intelligence Assessment Service.
* **Principal Aggregate, Access Role Aggregate und Permission Aggregate:** Ihre unabhängigen Lebensläufe werden nicht als Cross-Domain-Tatsachen konsumiert. Nur die fachlich wirksame Authorization Rule besitzt eine belegte Wirkung auf Platform Operations.
* **Synchronization Run Aggregate und Import Run Aggregate:** Ihre Zustände bleiben innerhalb ihrer jeweiligen Aggregate-Grenzen. Die Data Intake Coordination begründet keine zusätzliche veröffentlichte Tatsache und keine andere Domain referenziert diese Runs.
* **Alle Platform-Operations-Aggregates:** Begründung gemäß dem vorstehenden Domain-Abschnitt.

Diese Nicht-Aufnahme verhindert künstliche Ereignisse und verändert keine Aggregate-Verantwortung.

## Konsistenz mit Domain Services und Domain Policies

| Domain Service | Zugeordnete fachliche Events | Abgrenzung |
|---|---|---|
| Data Intake Coordination Service | Integration Context Established | Das Event bestätigt Integration Context; der Service koordiniert weiterhin Intake-Zuordnung. |
| Enterprise Context Classification Service | Asset Context Classified; Business Service Context Classified; Organizational Context Established | Events bestätigen abgeschlossene Context-Aussagen; der Service koordiniert deren domänenweite Einordnung. |
| Threat Intelligence Assessment Service | Threat Indicator Assessed; Threat Technique Assessed | Events bestätigen Aggregate-Aussagen; der Service koordiniert weiterhin die domänenweite Bewertung. |
| Security Observation Correlation Service | Finding Established; Alert Established; Exposure Established | Events bestätigen einzelne Observations; der Service entscheidet weiterhin über Korrelation. |
| Governance Compliance Evaluation Service | Governance Policy Changed; Compliance Requirement Assessed | Events bestätigen Policy- beziehungsweise Assessment-Aussagen; der Service koordiniert Geltung und Bewertung. |
| Decision Evidence Qualification Service | Evidence Qualified | Das Event bestätigt das Ergebnis; der Service verantwortet weiterhin die Qualifikationskoordination. |
| Cyber Decision Evaluation Service | Decision Completed | Das Event bestätigt den Abschluss; der Service koordiniert weiterhin die Decision-Bewertung. |
| Authorization Decision Service | Authorization Rule Changed | Das Event bestätigt eine Regeländerung und ersetzt keine Autorisierungsentscheidung. |
| Enterprise Risk Assessment Service | Enterprise Risk Treatment Decided | Das Event bestätigt eine Risk-Entscheidung und ersetzt keine vergleichende Bewertung. |

Hunt Concluded und Incident Response Phase Changed entstehen vollständig innerhalb ihrer jeweiligen Aggregate-Verantwortung; für diese Domains ist gemäß `DOMAIN-SERVICES.md` kein zusätzlicher Domain Service erforderlich.

Alle Events respektieren die zugehörigen Policies aus `DOMAIN-POLICIES.md`. Ein Event ist das Ergebnis einer bereits abgeschlossenen fachlichen Änderung; eine Policy begrenzt deren Zulässigkeit, und ein Domain Service koordiniert gegebenenfalls die fachliche Entscheidung. Keine dieser Verantwortungen wird durch das Event ersetzt.

## Konsistenz mit ADR-0001 bis ADR-0007

* ADR-0001: Nur Decision Completed bestätigt ein kanonisch abgeschlossenes `DecisionResult`; kein anderes Event erzeugt eine parallele Decision.
* ADR-0002: Execution Trace bleibt ein getrenntes Application-/Audit-Artefakt und ist kein Domain Event.
* ADR-0003 und ADR-0004: Explainability und Completeness bleiben read-only und konsumieren keine Events als neue fachliche Faktenquelle.
* ADR-0005: Workspaces und Mission Consoles sind keine Event-Produzenten oder fachlichen Konsumenten.
* ADR-0006: Evidence Qualified bewahrt Unveränderlichkeit, Provenance und die Trennung von Source, Evidence und Decision.
* ADR-0007: Produzenten behalten Ownership; Konsumenten nutzen ausschließlich definierte fachliche Beziehungen und interne Modelle überschreiten keine Domain Boundary.

## Nicht Bestandteil

Dieses Dokument definiert keinen Produktcode, keine Implementierung, Klassen, Interfaces, Methoden, Event Bus, Messaging, Kafka, RabbitMQ, Azure Service Bus, Outbox Pattern, Event Sourcing, APIs, DTOs, Repositorys, Persistenz, Datenbanken, Infrastruktur, Payloads, Schemas, Topics, Queues, Zustellgarantien, Retries oder technische Reihenfolge. Es verändert keine Domain, Entity, Value Object, Aggregate, Relationship, Dependency Rule, Domain Service, Domain Policy oder ADR.

## Statische Konsistenzprüfung

* Siebzehn Domain Events besitzen jeweils einen eindeutigen Namen, genau eine produzierende Domain und genau ein auslösendes Aggregate.
* Alle auslösenden und betroffenen Aggregate stammen aus `AGGREGATE-BOUNDARIES.md`.
* Alle referenzierten Domain Services stammen aus `DOMAIN-SERVICES.md`.
* Alle vierzehn domänenübergreifenden Events folgen belegten Aggregate Relationships und erlaubten Domain Dependencies.
* Drei Events sind ausdrücklich ausschließlich domänenintern relevant.
* Platform Operations ist als einzige Domain ohne fachliches Domain Event begründet.
* Kein Event ordnet eine Änderung eines fremden Aggregates an oder überträgt Ownership.
* Kausalität ist ausschließlich fachlich beschrieben; technische Reihenfolge und Transport bleiben offen.

## Referenzen

* `.ai/architecture/CANONICAL-DOMAIN-BOUNDARIES.md`
* `.ai/architecture/DOMAIN-OWNERSHIP-AND-RESPONSIBILITIES.md`
* `.ai/architecture/CANONICAL-ENTITIES.md`
* `.ai/architecture/CANONICAL-VALUE-OBJECTS.md`
* `.ai/architecture/AGGREGATE-BOUNDARIES.md`
* `.ai/architecture/AGGREGATE-RELATIONSHIPS.md`
* `.ai/architecture/DOMAIN-DEPENDENCIES.md`
* `.ai/architecture/DOMAIN-SERVICES.md`
* `.ai/architecture/DOMAIN-POLICIES.md`
* ADR-0001 bis ADR-0007
* AIDP TASK-0039

## Architektur-Review

Status: APPROVED  
Bewertung: PASS  
Bemerkungen: Inhaltliche Vollständigkeit und Konsistenz durch das APPROVED Architecture Gap Assessment aus TASK-0042 bestätigt; Governance-Abschluss durch TASK-0043 formalisiert.  
Freigabe: Architect via TASK-0042, formalisiert 2026-08-14
