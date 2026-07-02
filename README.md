# Cyber Risk Brain (CRB)

Cyber Risk Brain (CRB) ist eine Open-Source-Plattform zur Korrelation und Priorisierung von Cyber-Risiken.

## Vision

Die meisten Security-Tools liefern tausende einzelne Findings.

CRB geht einen Schritt weiter.

Das Ziel ist es, Informationen aus verschiedenen Sicherheitsquellen zusammenzuführen, Assets eindeutig zu identifizieren und daraus reale Cyber-Risiken abzuleiten.

Anstatt nur Schwachstellen aufzulisten, beantwortet CRB Fragen wie:

- Welche Systeme stellen aktuell das höchste Risiko dar?
- Welche Findings gehören zusammen?
- Welche Angriffspfade sind realistisch?
- Welche Risiken sollten zuerst behoben werden?

---

## Geplante Datenquellen

- Nessus
- Shodan
- Microsoft Defender XDR
- Microsoft Sentinel
- Have I Been Pwned (HIBP)
- NVD / CVE
- EPSS
- CISA KEV
- MISP
- Weitere Quellen folgen

---

## Architektur

```
Collector
      │
      ▼
Normalizer
      │
      ▼
Asset Resolver
      │
      ▼
Correlation Engine
      │
      ▼
Risk Engine
      │
      ▼
Story Generator
      │
      ▼
API
      │
      ▼
Dashboard
```

---

## Aktueller Entwicklungsstand

**Phase 2 – Correlation Engine**

Bereits umgesetzt:

- ✅ Datenmodell
- ✅ Normalizer
- ✅ Asset Resolver
- ✅ Erste Correlation Engine
- ✅ Asset Risk Engine

Aktuell in Entwicklung:

- 🚧 Pipeline
- 🚧 Story Generator

Geplant:

- Graph Engine
- Dashboard
- REST API
- PostgreSQL
- Threat Intelligence Integration
- KI-gestützte Risikoanalyse

---

## Projektziele

CRB soll Unternehmen dabei unterstützen,

- Cyber-Risiken besser zu verstehen
- Schwachstellen intelligent zu priorisieren
- Zusammenhänge zwischen Findings zu erkennen
- verständliche Risk Stories zu erzeugen
- fundierte Entscheidungen auf Basis korrelierter Sicherheitsdaten zu treffen

---

## Projektstatus

🚧 Active Development

Dieses Projekt befindet sich derzeit im aktiven Aufbau. Architektur und Funktionen entwickeln sich kontinuierlich weiter.

---

## Lizenz

Wird zu einem späteren Zeitpunkt ergänzt.
