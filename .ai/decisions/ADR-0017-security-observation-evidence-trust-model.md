# ADR-0017 – Security Observation & Evidence Trust Model

## Status

ACCEPTED

## Datum

2026-08-20

## Verantwortliche

Architect: Architect
Implementation: Codex

## Kontext

PredatorAI unterscheidet bereits Findings, Threat Intelligence, Correlation,
Evidence und Incident References. Die bestehende
`SecurityObservationCorrelationService` erzeugt deterministisch derived
Evidence aus referenzierten Inputs. Eine `EvidenceReference` ist dabei nur ein
Pointer; sie ist weder ein geladenes Evidence-Objekt noch eine Bestätigung.

Im Purple-Team-Lab wurde außerdem target-seitige Runtime-Beobachtung von
DistCC-Traffic nachgewiesen. Das bestehende Modell kann eine solche Beobachtung
nicht vollständig mit Sensoridentität, Collection Method,
Independence-Eigenschaft und Observation-Provenance ausdrücken. Zugleich darf
ein Finding oder ein offensiver Selbstbericht nicht stillschweigend als
beobachteter Exploit-Erfolg oder bestätigte Kompromittierung gelten.

## Problem

Claim, direkte Observation, deterministische Correlation, Evidence,
Verification und Incident-/Decision-State sind unterschiedliche Objekte und
Authority Boundaries. Eine lineare Truth-State-Maschine würde diese Semantiken
vermischen und könnte Herkunft, Ableitung und Bestätigung falsch gleichsetzen.

## Entscheidung

PredatorAI verwendet die folgende getrennte Semantik:

```text
Claim / Event
  + SecurityObservation
  + Finding / Asset / Threat Intelligence
        ↓
Deterministic Correlation
        ↓
Evidence (SOURCE oder DERIVED)
        ↓
Verification / Human Decision
        ↓
Incident State / Decision
```

Die Kette `ATTEMPTED → OBSERVED → CORRELATED → CONFIRMED` wird als einheitliche
State Machine verworfen. Diese Begriffe bezeichnen unterschiedliche Artefakte
oder Autoritäten, nicht zwingend aufeinanderfolgende Zustände eines Objekts.

Correlation bleibt eine deterministische Ableitung und erzeugt derived
Evidence. Sie bestätigt weder automatisch einen Angriff noch einen Exploit-
Erfolg. `CONFIRMED` ist keine Eigenschaft, die Observation oder Evidence allein
durch Existenz erhalten; sie gehört zu einem separaten Verification-/Decision-
Kontext.

## Canonical Domain Separation

- **Claim / Event:** Aussage oder Ereignisbehauptung einer Quelle. Ein Claim
  ist keine unabhängige Observation.
- **SecurityObservation:** direkt erhobenes Signal mit Herkunft und
  Erhebungsmetadaten. Es behauptet nicht automatisch Erfolg, Kompromittierung
  oder Incident-Bestätigung.
- **Finding:** festgestellter Security-/Vulnerability-Sachverhalt; kein Beweis
  beobachteter Exploitation.
- **Correlation:** reproduzierbare Regelanwendung auf explizite Inputs.
- **Evidence:** typisiertes Security-Artefakt mit `SOURCE`- oder `DERIVED`-
  Semantik und Provenance. Evidence existiert unabhängig davon, ob ein Claim
  verifiziert wurde.
- **Verification / Decision:** autorisierte fachliche Bewertung, die aus
  Evidence und Regeln eine Aussage oder einen Workflowzustand ableitet.
- **Incident State:** Workflow-/Analystenzustand; keine automatische
  Truth-Promotion durch eine Reference oder Correlation.

## SecurityObservation Semantics

Ein zukünftiges generisches `SecurityObservation` benötigt nur die minimale
Semantik, die eine direkte Erhebung nachvollziehbar macht:

- immutable Observation ID;
- typisierter Observation Type;
- `observed_at` sowie eindeutige Target-/Resource-Bindung;
- Source-/Sensor-Identity und Source Reference;
- Provenance einschließlich Collection Method und Referenz auf normalisierte
  bzw. rohe Erhebungsdaten, ohne sensible Rohdaten im Review-/Audittext zu
  vervielfältigen;
- qualitative, typisierte Independence-/Trust-Strength-Klasse;
- Contract Version.

Eine Observation darf keine globale Wahrheit, keine Confirmation und keine
Berechtigung erzeugen. Die konkrete Persistenz oder Sensorintegration ist nicht
Bestandteil dieser Entscheidung.

## Source / Sensor Trust Model

Trust ist eine Eigenschaft von Herkunft, Erhebungsmethode und Verifikation,
nicht der Überzeugungskraft des Inhalts. PredatorAI verwendet dafür qualitative,
deterministische Klassen statt Prozentwerten oder frei erfundenen
Confidence-Scores:

- **DIRECT_SOURCE:** direktes Signal einer benannten Quelle;
- **TARGET_SIDE:** target-seitig erhobenes Signal mit eindeutiger Bindung,
  aber ohne die Unabhängigkeit eines getrennten Network Sensors;
- **INDEPENDENT_SENSOR:** Signal eines organisatorisch/technisch getrennten,
  benannten Sensors;
- **SELF_ATTESTED:** Behauptung des handelnden Producers über die eigene
  Aktion; nicht unabhängige Bestätigung.

Mehrere Referenzen derselben Herkunft werden nicht automatisch als unabhängig
gezählt. Ein LLM darf keine Trust Strength festlegen oder erhöhen.

## Offensive Claim Boundary

Offensive Producers, Purple-Team-Tools und HackerAI dürfen Claims wie
`attempt sent`, `command requested` oder `exploit execution attempted` liefern.
Sie dürfen allein aufgrund ihrer eigenen Aktion nicht autoritativ `attack
observed`, `exploit successful` oder `compromise confirmed` festlegen.

Self-attestation is not independent confirmation. Offensive Claims dürfen
Inputs für Correlation sein; Producer-Identity, Methode, Zeit und Trust-
Eigenschaften bleiben dabei erhalten.

## Correlation Semantics

Correlation:

- referenziert alle verwendeten Inputs;
- verändert Observation oder Quell-Evidence nicht rückwirkend;
- erzeugt `EvidenceType.CORRELATION` mit `EvidenceKind.DERIVED`;
- bewahrt Provenance und Input References;
- erzeugt keine stärkere Aussage als Regel und Inputs rechtfertigen;
- ist keine automatische Verification oder Confirmation.

Die bestehende Contract-Version bleibt nachvollziehbar. Eine separate
Correlation Rule ID ist nur erforderlich, wenn sie für die eindeutige
Reproduzierbarkeit einer Regel nicht bereits durch den bestehenden
Contract-/Provenance-Verweis ausgedrückt wird; diese ADR führt keine neue
Registry oder Implementierung ein.

## Evidence Semantics

Das bestehende immutable Evidence-Modell wird erweitert, nicht ersetzt.
`SOURCE` und `DERIVED`, Identifier, Source, Description, Weight, Provenance
und Contract Version bleiben erhalten. Evidence darf künftig – soweit ein
akzeptierter Contract dies benötigt – referenzierbare Verification-Metadaten
tragen, ohne Evidence und Confirmation zu verschmelzen.

Observation-spezifische Felder (Sensor, Collection Method, observed_at und
Independence) gehören primär zur Observation. Verification-/Human-Validation,
Contradicting Inputs, Freshness und Gültigkeitsentscheidungen gehören in einen
separaten Verification-/Decision-Kontext, sofern sie nicht bereits als
Provenance referenziert werden. `Evidence exists` bedeutet nicht `Claim
confirmed`.

## Verification / Confirmation Authority

- Deterministischer Code darf nur explizite Regeln mit autoritativen Inputs
  auswerten.
- Ein Human Analyst darf in einem späteren Workflow Evidence bewerten und eine
  fachliche Entscheidung treffen.
- Ein LLM darf erklären, zusammenfassen und Widersprüche markieren, aber keine
  Observation erzeugen, Trust Strength erhöhen, Evidence bestätigen,
  Exploit-Erfolg oder Kompromittierung feststellen oder Aktionen autorisieren.
- Ein offensiver Producer darf seine eigene erfolgreiche Aktion nicht
  unabhängig bestätigen.

## LLM Authority Boundary

LLM-Ausgabe bleibt gemäß ADR-0010 und ADR-0015 untrusted, model-derived und
providerunabhängig klassifiziert. Sie ist standardmäßig weder Observation noch
Evidence noch Verification. Eine spätere Persistenz muss AI-generated/derived
Provenance sichtbar halten und darf keine höhere Trust-Klasse stillschweigend
promoten.

## Target-Side Observation Semantics

Target-side tcpdump kann grundsätzlich eine valide `TARGET_SIDE`-Observation
sein, wenn Source/Sensor, Collection Method, Target Binding, Timestamp und
Provenance eindeutig sind. Sie ist nicht äquivalent zu einer unabhängigen
Observation. Diese geringere Independence wird typisiert erhalten, ohne das
Signal vollständig zu verwerfen. Docker-/tcpdump-Ingestion wird hier nicht
entschieden.

## Truth-Promotion Rules

Die Architektur verwendet keinen globalen linearen Truth Score. Die zulässige
Ableitung ist explizit:

```text
Observation
  → supports / contradicts
Evidence
  → Verification
Decision / Incident State
```

`CONFIRMED` ist eine Eigenschaft des Verification-/Decision-Kontexts, nicht
automatisch von Observation oder Evidence. Availability- und Resolution-
Semantik aus ADR-0016 bleiben davon getrennt: `AVAILABLE` oder `RESOLVED`
bezeichnen weder Trust noch Verification.

## Relation zu ADR-0016

ADR-0016 bleibt verbindlich:

```text
EXISTS != REFERENCED != RESOLVED != EVALUATED != AVAILABLE
```

Diese Zustände werden nicht als Trust-, Verification- oder Truth-Stufen
interpretiert. Eine aufgelöste Observation ist nicht automatisch trusted oder
verified; verfügbare Evidence ist nicht automatisch confirmed.

## Kompatibilität mit ADR-0010–0016

Diese Entscheidung stärkt die bestehenden Grenzen:

- ADR-0010: LLM bleibt untrusted und keine Trust-Promotion durch Modelloutput;
- ADR-0011 bis ADR-0013: Authorization, Retrieval, Binding und Admission
  bleiben getrennte, vorgelagerte Grenzen;
- ADR-0014: Observation/Evidence-Verfügbarkeit autorisiert keinen Model Egress;
- ADR-0015: Output Disclosure und Guard bleiben unabhängig von Evidence-
  Verification;
- ADR-0016: Resolution/Availability bleibt von Trust/Confirmation getrennt.

Keine dieser ADRs wird abgeschwächt.

## Konsequenzen

- Correlation darf weiterhin zuverlässig derived Evidence erzeugen, ohne
  Exploit-Erfolg zu behaupten.
- Target-side und unabhängige Sensoren können künftig fachlich getrennt
  beschrieben werden.
- Ein künftiges Verification-/Decision-Modell muss Confirmation Authority
  explizit machen.
- Die Entscheidung definiert keine Sensorpipeline und ändert den eingefrorenen
  MVP nicht.

## Abgelehnte Alternativen

- `ATTEMPTED → OBSERVED → CORRELATED → CONFIRMED` als globale State Machine:
  vermischt Artefakte und Authority Boundaries.
- Correlation als Confirmation: Derived Evidence ist keine unabhängige
  Verifikation.
- EvidenceReference als vollständige Observation: Pointer und direkte
  Erhebung haben unterschiedliche Semantik.
- Self-attestation als Erfolgsbeweis: eigene Claims sind nicht unabhängig.
- Globaler Truth-/Confidence-Score: verschleiert Herkunft, Widerspruch und
  Verifikationsautorität.
- LLM als Evidence-/Trust-/Confirmation-Authority: unvereinbar mit ADR-0010
  und ADR-0015.

## Abgrenzung

Diese ADR entscheidet nicht über konkrete Sensoren, Docker-Netzwerke,
tcpdump-Ingestion, SIEM-/EDR-Connectoren, Detection Rules, automatische
Incident-Erstellung, UI-Design, Model-Egress-Erweiterungen, Grounded AI
Reasoning oder TASK-0097.

## Architektur-Review

Status: ACCEPTED

Bemerkungen: Architect Review PASS / APPROVED.

Freigabe: Architect
