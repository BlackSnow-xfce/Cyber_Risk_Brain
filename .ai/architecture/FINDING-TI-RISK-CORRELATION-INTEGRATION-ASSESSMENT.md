# Finding + Threat Intelligence → Risk/Correlation Integration Assessment

Version: 1.0  
Scope: TASK-0062  
Status: PROPOSED FOR ARCHITECTURE REVIEW  
Datum: 2026-08-17

## 1. Executive Summary

Der produktive Pfad `Finding → CVE → Threat Intelligence Contract 1.0` ist technisch und fachlich ausreichend, um autoritative Finding- und TI-Source-Facts bereitzustellen. Er ist jedoch noch nicht direkt kompatibel mit einer produktiven Kette `Correlation → Risk → Decision`.

Der wichtigste Befund ist: Im Python-Backend existiert keine produktive `CorrelationEngine`, kein kanonischer Correlation-Input/-Output-Vertrag und keine Runtime-Implementierung des in den Architekturartefakten vorgesehenen `Security Observation Correlation Service`. Frontend-`Correlation`-Typen und synthetische Workspace-Repositories sind Presentation-/Mock-Artefakte und dürfen nicht als Backend-Vertrag verwendet werden.

Zusätzlich kann der reale DistCC-Host `172.18.0.19` mit dem vorhandenen Asset-Context-Bestand nicht auf eine kanonische Asset-ID abgebildet werden. Der vorhandene kontrollierte Asset-Kontext enthält ausschließlich `172.18.0.18 → asset-lab-dvwa-001 / LOW`. Der reale Walkthrough stoppt deshalb deterministisch nach TI und vor Correlation. Es werden weder Asset Criticality, Correlation, Risk noch Decision hypothetisch erzeugt.

Empfohlen wird kein direkter Anschluss an `FindingThreatIntelligenceUseCase`, RiskEngine oder API. Die freigegebene Zielboundary ist der bereits architektonisch benannte `Security Observation Correlation Application Service`, implementiert als neuer Application-Orchestrator über klar versionierte Integration Contracts. Er muss Finding, TI und Asset Context lesen, einen separat definierten Correlation-Domain-Service aufrufen und dessen Derived Evidence an die `Decision Evidence Qualification` weiterreichen. Cyber Decision darf Finding oder TI gemäß bestehenden Dependency Rules nicht direkt konsumieren.

## 2. Analysierter Bestand

### 2.1 Finding / Security Observation

`core.models.UniversalFinding` enthält:

* `id: str`
* `source: str`
* `title: str`
* `vendor_severity: str`
* `business_criticality: str`
* `asset: str`
* Legacy-/Placeholder-Felder `exposed`, `detection_available`, `threat_intel_match`, `mitre_tactic`, `owner`, `remediation`
* `cve_identifiers: tuple[str, ...]`

Bewertung:

* Finding-ID, Source, Titel, Vendor Severity, observed Asset Identifier und mehrere CVEs sind vorhanden.
* Das Asset-Feld ist ein beobachteter Scanner-Identifier, keine kanonische Asset-ID.
* Das Modell enthält keine Finding-spezifische Provenance-Struktur, keinen Observation Timestamp und keine Source Reference je Feld. `source` identifiziert nur die Scannerfamilie.
* `business_criticality`, `exposed`, `detection_available` und `threat_intel_match` dürfen nach dem freigegebenen `RiskAssessmentInput.from_universal_finding` nicht als autoritative Werte behandelt werden. Die Projection setzt entsprechende Risk Inputs bewusst auf `UNKNOWN` beziehungsweise `NOT_EVALUATED`.
* Greenbone unterstützt null, eine oder mehrere CVEs. Die Reihenfolge ist deterministisch; Duplikate werden ohne Priorisierung entfernt.

### 2.2 Threat Intelligence

`FindingThreatIntelligenceUseCase`:

* selektiert genau ein Finding über `FindingsQueryService`;
* kanonisiert und dedupliziert dessen CVEs;
* ruft pro eindeutiger CVE den bestehenden `ThreatIntelligenceReader` auf;
* liefert geordnete `FindingThreatIntelligence`-Beziehungen;
* liefert bei fehlender CVE `not_applicable` ohne Reader-/Provideraufruf;
* erzeugt keine Correlation-, Risk- oder Decision-Aussage.

Threat Intelligence Contract 1.0 liefert pro CVE:

* `CveIdentifier`
* NVD Summary und Zeitpunkte
* CVSS Version, Base Score, Vector und optionale Severity
* EPSS Probability und optionales Percentile
* CISA-KEV-Mitgliedschaft und optionale Katalogfelder
* optionale Exploitation Evidence
* Fact-lokale `ExplanationCompleteness`
* Fact-lokale `ExplanationProvenance`
* optionale timezone-aware Observation-/Retrieval-Timestamps

Availability unterscheidet `available`, `no_data`, `source_unavailable`, `not_evaluated`, `not_applicable`, `not_part_of_execution` und `unknown`. Nicht verfügbare Facts besitzen `value=None`; ein autoritatives KEV `False` ist ausschließlich bei `available` zulässig.

### 2.3 Asset Context

`AssetContextQueryService` löst einen expliziten `ObservedAssetIdentifier` gegen eine konfigurierte JSON-Quelle auf.

Unterstützter Identifier-Typ:

* ausschließlich `ip_address`

Ergebnis `AssetContext`:

* normalisierter observed Identifier
* `canonical_asset_id`
* `AssetCriticality`: `CRITICAL | HIGH | MEDIUM | LOW`
* `source_reference`

Semantik:

* unbekannter Identifier → `None`, kein LOW-Default;
* mehrere Treffer → kontrollierter Datenfehler;
* fehlende/ungültige Quelle → kontrollierter Konfigurations-/Datenfehler;
* `RiskAssessmentInput.with_asset_context` übernimmt ausschließlich autoritative Criticality und prüft den observed Identifier;
* Canonical Asset ID und Asset Source Reference werden aktuell nicht in `RiskAssessmentInput` transportiert.

Aktueller Realbestand:

* vorhandener Asset-Context-Eintrag: `172.18.0.18 → asset-lab-dvwa-001`, Criticality `LOW`;
* kein Eintrag für DistCC/Metasploitable2 `172.18.0.19`.

### 2.4 Correlation

#### Produktiver Runtime-Bestand

Im Python-Backend existiert keine `CorrelationEngine`-Implementierung und kein kanonischer Correlation-Contract.

Folglich existieren aktuell nicht:

* typisierter Correlation Input;
* typisierter Correlation Output;
* produktive Correlation Rules;
* definierte Nutzung von CVSS, EPSS, KEV oder Exploitation Evidence;
* definierte Nutzung von Canonical Asset ID, Criticality oder Exposure;
* Partial-/Missing-Data-Policy für Correlation;
* Correlation Provenance oder Observation Timestamp;
* Persistenz-, Seiteneffekt- oder Fehlervertrag;
* produktive Aufrufstellen.

#### Architekturvorgabe

`.ai/architecture/DOMAIN-SERVICES.md` definiert den `Security Observation Correlation Service` in der Owner Domain `Security Observation`. Er darf autoritative Security Observations korrelieren und gemäß erlaubten Richtungen Enterprise Context und Threat Intelligence verwenden. Er darf Findings, Alerts, Exposure, Asset Context oder TI nicht besitzen oder verändern.

`.ai/architecture/APPLICATION-SERVICES.md` definiert entsprechend den `Security Observation Correlation Application Service` als Orchestrierungsboundary.

#### Nicht wiederverwendbare Artefakte

Frontend-`Correlation`-Typen, Frontend Rule Packs und SOC Mock Repositories sind Presentation-/synthetische Artefakte. Sie sind weder Backend-Single-Source-of-Truth noch produktive Correlation-Implementierung.

Legacy-Reasoning-Code nennt Signale wie `known_exploited`, `public_exploit`, `high_epss`, `high_cvss` und `crown_jewel`. Diese Signale besitzen keinen freigegebenen Producer-Contract, keine Availability-Semantik und keine Verbindung zu Contract 1.0. Sie dürfen nicht als vorhandener Correlation Contract interpretiert werden.

### 2.5 Risk

Es existieren zwei technisch ähnliche Risk-Implementierungen:

1. `analysis.risk_engine.RiskEngine`, konsumiert durch `RiskReadinessService`;
2. `core.decision.risk_engine.RiskEngine`, intern durch `DecisionEngine` konsumiert.

Beide arbeiten mit untypisierten Node-Dictionaries und derselben Kerngewichtung:

| Input | Gewicht |
|---|---:|
| Criticality CRITICAL / HIGH / MEDIUM / sonst | 40 / 30 / 20 / 10 |
| exposed = true | +20 |
| detection = false | +15 |
| threat_intel = true | +15 |
| mitre vorhanden | +10 |
| Maximum | 100 |

`RiskReadinessService` stellt eine wichtige Guardrail-Boundary dar:

* typisierter `RiskAssessmentInput`;
* Zustände `AUTHORITATIVE`, `UNKNOWN`, `NOT_EVALUATED`;
* RiskEngine wird nur aufgerufen, wenn Criticality, Exposure, Detection, Threat-Intelligence-Match und MITRE vollständig autoritativ sind;
* bei fehlenden Inputs: `INSUFFICIENT_CONTEXT`, `score=None`, kein RiskEngine-Aufruf;
* Vendor Severity wird als beobachteter Input dokumentiert, beeinflusst den Score aber nicht;
* CVSS, EPSS, KEV, Exploitation Evidence, Provenance und Timestamps sind keine Risk Inputs;
* `threat_intelligence_match: bool` ist fachlich nicht ausreichend definiert, um Contract-1.0-Facts deterministisch darauf abzubilden.

Die parallelen Risk-Klassen und untypisierten Dictionaries sind bestehende Migration Debt. TASK-0062 entscheidet keine Konsolidierung.

Seiteneffekte/Persistenz:

* `calculate_risk_score` selbst ist deterministisch und ohne Persistenz;
* `analysis.RiskEngine` konstruiert zusätzlich einen `DecisionEngine`, obwohl `RiskReadinessService` nur Scoring nutzt;
* keine produktive Finding→TI→Risk-Aufrufstelle existiert.

### 2.6 Decision, Evidence und Explainability

`core.decision.models.DecisionResult` ist gemäß ADR-0001 der einzige kanonische abgeschlossene Decision Contract. Er enthält Finding-ID, Priority, Action, Decision, Attack Reasoning, Business Impact, Confidence, Recommendations, Evidence und Metadata.

`DecisionEngine` konsumiert aktuell ein untypisiertes Node-Dictionary, berechnet intern erneut Risk, Priority und Action und erzeugt anschließend `DecisionResult`. Es gibt keinen typisierten Eingang für Correlation Result, Contract-1.0-TI oder `RiskAssessmentResult`.

ADR-0006 verlangt:

* Source Evidence aus autoritativen Quellen;
* Derived Evidence für freigegebene deterministische Correlation-/Risk-Ergebnisse;
* Provenance und Referenzen von Derived auf Input Evidence;
* einen unveränderlichen Decision Evidence Snapshot;
* Evidence Collection/Qualification vor Decision;
* keine nachträglich plausibilisierte Evidence.

Der aktuelle `EvidenceBuilder` ist nicht als TI-/Correlation-Bridge geeignet: Er baut Evidence aus bereits erzeugtem Attack Reasoning, verwendet teilweise veraltete Feldannahmen und erfüllt den in ADR-0006 beschriebenen zukünftigen Evidence-Lifecycle noch nicht.

`core.explainability.DecisionTrace` und sein Builder sind die kanonische read-only Decision-Explainability-Projektion gemäß ADR-0003. Sie können nur vorhandene `DecisionResult`-Felder und Evidence projizieren. Sie dürfen fehlende TI-/Correlation-Evidence nicht nachträglich erzeugen.

Die ältere `core.decision.DecisionTrace`-/`DecisionContext`-Familie enthält untypisierte Listen für `threat_intelligence` und `correlations`, ist laut ADR-0001/0003 aber weder kanonisches Decision Result noch kanonische Explainability Projection.

## 3. Contract Compatibility Matrix

Legende: `YES` direkt semantisch kompatibel; `PARTIAL` technisch vorhanden, aber fachlicher Vertrag/Provenance fehlt; `NO` kein kompatibler Consumer oder keine zulässige Transformation.

| Feld | Producer | Aktueller Consumer | Typ / Semantik | Kompatibel | Notwendige Transformation | Art | Verantwortliche Schicht |
|---|---|---|---|---|---|---|---|
| Finding ID | UniversalFinding | RiskAssessmentInput, DecisionResult | `str`, stabile Finding-Referenz | YES | strukturelle Projektion | technisch | Application Boundary |
| Finding Source | UniversalFinding | RiskAssessmentInput available inputs | `str`, Scannerfamilie | YES | strukturelle Projektion | technisch | Application Boundary |
| Vendor Severity | UniversalFinding | RiskAssessmentInput nur Audit, Legacy Decision Node liest `severity` | unkontrollierter Source-String | PARTIAL | normalisierte Source-Evidence; keine Risk-Gewichtung ohne Policy | fachlich | Security Observation / Evidence Qualification |
| CVE Identifier(s) | UniversalFinding / CveIdentifier | FindingThreatIntelligenceUseCase | geordnetes Tuple kanonischer IDs | YES für TI; NO für Risk | pro CVE Beziehung erhalten | technisch | bestehender Finding-TI Use Case |
| Observed Asset Identifier | UniversalFinding | AssetContextQueryService nach expliziter Typbildung | `str`, faktisch IP im Greenbone-Slice | PARTIAL | `ObservedAssetIdentifier(IP_ADDRESS, value)` | technisch, solange Source-Typ garantiert | Application Boundary |
| Canonical Asset ID | AssetContext | kein RiskAssessmentInput-Feld | `str`, Enterprise-Context-Identität | NO | neuen Integration-Contract transportieren | technisch/fachlich | Enterprise Context Contract |
| Finding Provenance | nur `source`; keine Feld-Provenance | Evidence benötigt Provenance | unvollständig | NO | Source Reference und Observation Context definieren | fachlich | Security Observation Contract |
| CVSS Score | TI Contract 1.0 / NVD | kein Correlation-/Risk-Consumer | `float 0..10`, Source Severity | NO | keine Schwelle ohne freigegebene Policy | fachlich | künftiger Correlation Domain Service |
| CVSS Severity | TI Contract 1.0 / NVD | Legacy Node `severity` bedeutet Finding Severity | `str`, CVSS-Sourcewert | NO | strikt getrennt von Vendor Severity halten | fachlich | künftiger Correlation Contract |
| EPSS Score | TI Contract 1.0 / FIRST | kein produktiver Consumer | `float 0..1`, Probability | NO | keine High/Low-Klassifikation ohne Policy | fachlich | künftiger Correlation Domain Service |
| EPSS Percentile | TI Contract 1.0 / FIRST | kein produktiver Consumer | optional `float 0..1`, Rank | NO | Availability erhalten; keine Priorisierung | fachlich | künftiger Correlation Domain Service |
| KEV Membership | TI Contract 1.0 / CISA | kein produktiver Consumer | `bool` nur bei `available` autoritativ | PARTIAL | available `False` von unknown/unavailable trennen | technisch + fachlich | Correlation Contract / Domain Service |
| Exploitation Evidence | TI Contract 1.0 | kein produktiver Consumer | optionales Evidence Tuple | PARTIAL | Source Evidence qualifizieren, nicht zu Boolean reduzieren | fachlich | Decision Evidence Qualification |
| TI Availability | ExplanationCompleteness | RiskInputState hat anderes, gröberes Enum | verschiedene Zustandsräume | PARTIAL | explizite, verlustfreie Mapping-Policy | fachlich | Integration Contract, nicht UI/Provider |
| TI Provenance | ExplanationProvenance | Decision Evidence verlangt Provenance konzeptionell | source type + reference | PARTIAL | unverändert in Source Evidence übernehmen; Version ergänzen | technisch | Evidence Collection Boundary |
| TI Observation Timestamp | IntelligenceFact | kein Risk-/Decision-Input | optional timezone-aware datetime | NO | Snapshot-/Freshness-Vertrag erforderlich | fachlich | Correlation/Evidence Contract |
| Asset Criticality | AssetContext | RiskAssessmentInput | enum mit Source Reference | YES | `with_asset_context` | bestehend technisch | Application Boundary |
| Exposure | kein autoritativer Producer im Live-Pfad | RiskAssessmentInput | `RiskInputValue[bool]` | NO | separaten Source Contract integrieren | fachlich | Security Observation / Enterprise Context gemäß Ownership |
| Detection Coverage | kein autoritativer Producer im Live-Pfad | RiskAssessmentInput | `RiskInputValue[bool]` | NO | separaten Source Contract integrieren | fachlich | Security Observation |
| Threat Intelligence Match | kein definierter Producer | RiskAssessmentInput | Boolean | NO | semantischen Derived-Signal-Contract definieren oder Feld ersetzen | fachlich | Security Observation Correlation Service |
| MITRE Context | kein autoritativer Producer im Live-Pfad | RiskAssessmentInput | optionaler String | NO | separaten Contract integrieren | fachlich | zuständige Source Domain |
| Correlation Result | kein Runtime Producer | kein typisierter Consumer | nicht vorhanden | NO | kanonischen Derived-Evidence-Contract definieren | fachlich | Security Observation Domain |
| Risk Result | RiskReadinessService | DecisionEngine konsumiert es nicht | status, inputs, missing, score | PARTIAL | Decision-Evaluation-Input / qualified Risk Evidence definieren | fachlich | Decision Evidence / Cyber Decision Boundary |

## 4. Integration Boundary Evaluation

### A. FindingThreatIntelligenceUseCase → CorrelationEngine

Vorteile:

* Finding und TI liegen bereits gemeinsam vor.

Nachteile / Verletzungen:

* Use Case würde von reiner Finding↔TI-Beziehung zu Correlation-/Asset-/Risk-Orchestrierung anwachsen;
* verletzt Single Responsibility und erschwert No-CVE-/TI-Read-Wiederverwendung;
* kein Asset Context;
* kein Correlation Contract oder Engine vorhanden;
* Gefahr, TI-Facts im Use Case fachlich zu interpretieren.

Testbarkeit/Explainability:

* Source-Read und Derived-Signal-Regeln würden gekoppelt;
* Evidence-Snapshot wäre nicht sauber abgrenzbar.

Bewertung: **NICHT EMPFOHLEN**.

### B. Neuer Application Service orchestriert Finding, TI, Asset Context, Correlation und Risk

Vorteile:

* klare Workflow-Boundary;
* bestehende Reader/Queries bleiben unverändert;
* Fehler, Availability und Call Counts können kontrolliert werden;
* Multi-CVE und Partial Failure sind testbar;
* erlaubt Evidence Collection vor Decision.

Nachteile/Risiken:

* darf fachliche Correlation-/Risk-Regeln nicht selbst implementieren;
* benötigt zuerst typisierte Input-/Output-Contracts und einen Domain Service;
* ein einziger Mega-Service über Correlation, Evidence, Risk und Decision würde erneut Verantwortlichkeiten vermischen.

Bewertung: **EMPFOHLEN ALS ORCHESTRIERUNGSMUSTER**, aber in freigegebene Stufen getrennt. Der fachliche Name und Owner sollen dem bereits dokumentierten `Security Observation Correlation Application Service` entsprechen.

### C. Bestehender Application Service

Bestand:

* `FindingThreatIntelligenceUseCase` liest Finding+TI, korreliert aber nicht.
* `RiskReadinessService` prüft Risk-Vollständigkeit, lädt aber weder Finding, TI noch Asset Context.
* `AssetContextQueryService` löst ausschließlich Asset Context.
* Der dokumentierte `Security Observation Correlation Application Service` existiert nur als Architekturartefakt, nicht als Runtime-Service.

Bewertung: **KEIN BESTEHENDER RUNTIME-SERVICE IST AUSREICHEND**. Die dokumentierte Application-Service-Boundary ist jedoch wiederzuverwenden und darf nicht durch eine anders benannte Parallelboundary ersetzt werden.

### D. Direkte Integration in RiskEngine

Nachteile/Verletzungen:

* RiskEngine müsste Provider-/TI-/Asset-Contracts kennen;
* Availability und Provenance würden wahrscheinlich in Booleans/Sentinelwerte kollabieren;
* doppelte Interpretation von CVSS/EPSS/KEV;
* untypisiertes Node-Dictionary verstärkt Kopplung;
* Correlation- und Evidence-Stufe würden übersprungen;
* widerspricht Domain Integration Principles und Evidence Architecture.

Bewertung: **ABGELEHNT**.

### E. Direkte Integration in API

Nachteile/Verletzungen:

* Businesslogik in Delivery Layer;
* schlechte Wiederverwendung und Testbarkeit;
* API würde Domain Ownership, Partial Failure und Evidence entscheiden;
* Backend-interne Contracts würden zu Transportdetails degradiert.

Bewertung: **ABGELEHNT**.

## 5. Real Data Walkthrough – DistCC

### Schritt 1: Finding

Vorhanden:

* Finding-ID: `6d3167e9-002c-4b76-a5a7-ce47f81b78b1`
* Source: `greenbone`
* Titel: `DistCC RCE Vulnerability (CVE-2004-2687)`
* CVE: `CVE-2004-2687`
* observed Asset Identifier: `172.18.0.19`

Ergebnis: **COMPLETE** für Finding→TI; Finding-Provenance und Observation Timestamp bleiben unvollständig.

### Schritt 2: Threat Intelligence

Vorhanden aus Contract 1.0:

* CVSS 2.0 / 9.3 / HIGH / Vector vorhanden;
* EPSS 0.88195 / Percentile 0.99755;
* CISA KEV `available`, Membership `False`;
* Exploitation Evidence `not_evaluated`;
* Source References und Observation Timestamps je Source.

Ergebnis: **COMPLETE** als autoritative TI-Facts. Daraus folgt ausdrücklich noch keine Relevance-, Exploitability-, Risk- oder Priority-Aussage.

### Schritt 3: Asset Context

Der vorhandene Asset Context enthält ausschließlich den observed Identifier `172.18.0.18`. Für `172.18.0.19` existiert kein Eintrag.

Deterministisches Ergebnis:

* `AssetContextQueryService.resolve(172.18.0.19)` → `None`;
* Canonical Asset ID: nicht vorhanden;
* Asset Criticality: `UNKNOWN`, kein Default;
* Asset Source Reference: nicht vorhanden.

### STOP

Der Walkthrough stoppt hier gemäß Task-Vorgabe. Es fehlen:

1. autoritatives Asset Mapping für `172.18.0.19`;
2. kanonischer Correlation Input/Output Contract;
3. produktiver Security Observation Correlation Domain Service;
4. definierte Transformation von Correlation Derived Evidence zu Risk Inputs;
5. vollständige autoritative Risk Inputs für Exposure, Detection und MITRE;
6. Decision-Evaluation-Input aus qualifiziertem Evidence Snapshot und Risk Result.

Nicht erzeugt:

* keine Criticality;
* kein `crown_jewel`;
* kein `high_epss`;
* kein `known_exploited`-Derived-Signal (KEV Fact bleibt autoritatives `False`);
* kein Correlation Output;
* kein Risk Score/Level;
* keine Priority;
* keine Decision;
* keine Recommendation.

## 6. Gap Assessment

| Nr. | Bereich | Status | Begründung |
|---:|---|---|---|
| 1 | Finding→TI Contract | COMPLETE | produktiv, Multi-/No-CVE, Contract 1.0, Provenance je TI Fact |
| 2 | Finding→Asset Context | PARTIAL | Resolver vorhanden; observed IP muss explizit typisiert werden; reales `.19` fehlt; Canonical ID nicht weitertransportiert |
| 3 | TI→Correlation Mapping | MISSING | keine Regeln, kein Contract, keine Runtime-Engine |
| 4 | Asset Context→Correlation | MISSING | Architekturbeziehung erlaubt, technischer/fachlicher Correlation Input fehlt |
| 5 | Correlation→Risk | MISSING | kein Correlation Result; Risk erwartet groben Boolean `threat_intelligence_match` |
| 6 | Risk→Decision | PARTIAL | beide existieren, aber DecisionEngine konsumiert `RiskAssessmentResult` nicht und berechnet Risk erneut |
| 7 | Evidence Provenance | PARTIAL | TI/Asset Provenance vorhanden; Finding/Correlation/Risk Evidence Snapshot fehlt |
| 8 | Observation Timestamp Propagation | PARTIAL | TI timestamps vorhanden; Finding/Asset/Correlation/Risk Snapshot-Propagation fehlt |
| 9 | Availability / Missing Data | PARTIAL | TI und Risk haben getrennte Semantiken; verlustfreies Mapping fehlt |
| 10 | Multi-CVE Handling | PARTIAL | Finding-TI vollständig; Correlation Aggregations-/Konfliktpolicy fehlt |
| 11 | No-CVE Handling | COMPLETE bis TI | `not_applicable`, 0 Providercalls; Downstream-Policy fehlt, darf aber kein Fehler sein |
| 12 | Unknown Asset Handling | PARTIAL | Resolver/RiskReadiness fail safe; Correlation Output dafür fehlt |
| 13 | Multi-provider TI | COMPLETE als Source Read | Composite erhält Source Authority/Partial Failure; Correlation-Verwendung fehlt |
| 14 | Explainability | PARTIAL | kanonische Projection vorhanden; qualifizierte Source-/Derived-Evidence fehlt |
| 15 | Deterministic Execution | PARTIAL | Reads und RiskReadiness deterministisch; Correlation Rules/Snapshot fehlen |
| 16 | Error Handling | PARTIAL | Finding/TI/Asset kontrolliert; Workflow-, Correlation- und Downstream-Fehlervertrag fehlt |

## 7. Architecture Recommendation

### 7.1 Orchestrierende Komponente

Die Orchestrierung soll durch eine Runtime-Implementierung des bereits freigegebenen **Security Observation Correlation Application Service** erfolgen. Kein vorhandener Use Case soll dafür erweitert und kein universeller „Enrichment/Risk“-Service parallel eingeführt werden.

Der Application Service koordiniert ausschließlich:

1. Finding lesen;
2. bestehende Finding-TI-Beziehungen lesen;
3. observed Asset Identifier über Enterprise Context auflösen;
4. einen typisierten Correlation Input Snapshot erstellen;
5. den Security Observation Correlation Domain Service aufrufen;
6. Source- und Derived-Evidence an die Decision Evidence Qualification Boundary übergeben.

Fachliche Regeln bleiben im Correlation Domain Service. Risk- und Decision-Regeln bleiben bei ihren Ownern.

### 7.2 Notwendige Contracts

Unverändert wiederverwendbar:

* `UniversalFinding` als bestehende Finding-Quelle, jedoch nicht als Cross-Domain-Universalvertrag;
* `CveIdentifier`;
* `FindingThreatIntelligence` und `VulnerabilityThreatIntelligence` Contract 1.0;
* `IntelligenceFact`, Completeness und Provenance;
* `ObservedAssetIdentifier`, `AssetContext`, `AssetContextQueryService`;
* `RiskInputValue`, `RiskAssessmentStatus`, `RiskReadinessService` als Fail-safe-Grundlage;
* `DecisionResult`;
* kanonische Explainability Projection aus `core.explainability`.

Vor produktiver Integration neu zu definieren oder kontrolliert zu erweitern:

1. Security Observation Correlation Input Contract;
2. Correlation Result / Derived Evidence Contract mit Version, Inputs, Provenance, Observed-/Evaluated-at und Completeness;
3. Multi-CVE-Policy, die pro CVE Source Facts erhält und keine implizite Priorisierung vornimmt;
4. verlustfreie Availability-Übersetzung zwischen TI/Asset/Correlation/Risk;
5. Finding Source Evidence mit Source Reference und Observation Timestamp;
6. Risk Assessment Input Contract für qualifizierte Correlation-/Evidence-Signale oder explizite Ablösung des mehrdeutigen `threat_intelligence_match`-Booleans;
7. Risk→Decision-Evaluation-Input, damit Decision Risk nicht erneut aus einem Raw Dictionary berechnet;
8. unveränderlicher Decision Evidence Snapshot gemäß ADR-0006.

Keine Contract-Version 2.0 für Threat Intelligence ist allein für diese Integration erforderlich. Correlation muss Contract 1.0 konsumieren, nicht TI um Correlation-Felder erweitern.

### 7.3 Verbotene Datenwege

Folgende Daten dürfen niemals direkt in Correlation/Risk/Decision gelangen:

* UI-formatierte Werte;
* direkte NVD-/FIRST-/CISA-Providerantworten;
* Providerwerte ohne Contract-1.0-Validierung;
* `null`, `false` oder `0` als Ersatz für unavailable/not evaluated;
* synthetische Frontend-Correlations;
* aus CVSS/EPSS/KEV heuristisch erzeugte Risk-/Priority-Werte;
* Asset Criticality aus Scanner Severity;
* Finding Severity als CVSS Severity oder umgekehrt.

### 7.4 Correlation, Risk und Decision Ownership

* Correlation gehört in den `Security Observation Correlation Service` und erzeugt nachvollziehbare Derived Evidence, keine Risk Decision.
* Technisches Risk Scoring darf erst hinter `RiskReadinessService` oder einem freigegebenen Nachfolgevertrag stattfinden, wenn alle erforderlichen Inputs autoritativ sind.
* Cyber Decision konsumiert qualifizierte Decision Evidence und erlaubten Enterprise-/Governance-Kontext, nicht Finding/TI direkt.
* Enterprise Risk bleibt nachgelagert zu Cyber Decision und darf nicht als Ersatz für das technische Finding-Risk-Scoring verwendet werden.

### 7.5 Explainability und doppelte Interpretation

Vollständige Explainability erfordert eine gerichtete Evidence Chain:

`Finding/TI/Asset Source Evidence`
→ `Correlation Derived Evidence` mit Input-Referenzen
→ `Risk Derived Evidence` mit Correlation-/Source-Referenzen
→ unveränderlicher `Decision Evidence Snapshot`
→ `DecisionResult`
→ read-only Explainability Projection.

Jeder fachliche Schwellenwert oder Mapping-Schritt hat genau einen Owner. EPSS wird beispielsweise nur im Correlation Domain Service klassifiziert, falls eine solche Policy separat freigegeben wird; RiskEngine und UI dürfen denselben Wert nicht erneut klassifizieren.

### 7.6 Backend Single Source of Truth

Der komplette Workflow bleibt backendseitig. API und UI erhalten ausschließlich versionierte Projektionen abgeschlossener Backend-Ergebnisse. Provideradapter bleiben Source Adapter; Application Services orchestrieren; Domain Services entscheiden; Explainability projiziert read-only.

## 8. Proposed Minimal Follow-up Work Slices

Diese Liste ist eine Architektur-Roadmap und erstellt keine AIDP-Tasks oder Task-IDs.

1. **Correlation Contract Slice**  
   Definiert Security Observation Correlation Input, Result, Source-/Derived-Evidence, Availability, Multi-CVE und Zeitsemantik. Keine Scoring-Implementierung.

2. **Metasploitable2 Asset Context Slice**  
   Stellt eine Product-Owner-autorisierte kanonische Asset-Zuordnung für `172.18.0.19` bereit und validiert unknown/ambiguous Verhalten. Keine erfundene Criticality.

3. **Correlation Domain Service Slice**  
   Implementiert ausschließlich freigegebene deterministische Regeln gegen den Correlation Contract. Keine Risk-/Decision-Logik.

4. **Decision Evidence Qualification Slice**  
   Qualifiziert Finding-, TI-, Asset- und Correlation-Aussagen als unveränderliche Source-/Derived-Evidence mit Provenance und Snapshot-ID.

5. **Risk Input Contract Slice**  
   Entscheidet fachlich, welche qualifizierten Signale Risk konsumiert, beseitigt die Mehrdeutigkeit von `threat_intelligence_match` und verhindert doppelte TI-Interpretation. Gewichtungsänderungen benötigen eigene Freigabe.

6. **Risk→Decision Boundary Slice**  
   Definiert, wie ein freigegebenes Risk Result und Evidence Snapshot in Cyber Decision eingehen, ohne Risk im DecisionEngine erneut aus Raw Dictionaries zu berechnen.

7. **Controlled Vertical Acceptance Slice**  
   Validiert erst nach Freigabe aller vorgelagerten Contracts den realen DistCC-Pfad bis `DecisionResult` und Explainability. Keine UI-Businesslogik.

## 9. Konsistenz- und Scope-Prüfung

Dieses Assessment ist konsistent mit:

* ADR-0001: `DecisionResult` bleibt kanonisch;
* ADR-0002: Execution Trace bleibt getrennt;
* ADR-0003/0004: Explainability/Completeness bleiben read-only und explizit;
* ADR-0006: Evidence ist provenance-pflichtig und vor Decision zu qualifizieren;
* ADR-0007: Domain Ownership, gerichtete Dependencies, keine Cross-Domain-Aggregate;
* `DOMAIN-SERVICES.md`: Security Observation Correlation Service als fachlicher Owner;
* `APPLICATION-SERVICES.md`: Security Observation Correlation Application Service als Orchestrator;
* Threat Intelligence Contract 1.0: Source Authority und Availability bleiben unverändert.

Keine Produkt-, Test-, Runtime-, API-, Frontend-, Provider-, Contract-, Persistenz-, Scoring- oder Weighting-Änderung ist Bestandteil dieses Dokuments.
