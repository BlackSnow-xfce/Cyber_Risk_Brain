# ADR-0005 – Mission Console Workspace Architecture

## Status

ACCEPTED

## Datum

2026-08-04

## Verantwortliche

Architect: Architect  
Implementation: Codex

## Kontext

PredatorAI stellt rollenbezogene Arbeitsbereiche innerhalb einer gemeinsamen Plattform bereit. Der aktuelle Frontend-Stand enthält mit `PlatformLayout`, `Topbar`, `Sidebar` und `WorkspaceOutlet` einen globalen Plattform-Rahmen. Eine Registry beschreibt auswählbare Workspaces; eine zweite Registry-Funktion liefert rollenbezogene Navigation. `WorkspaceOutlet` rendert gegenwärtig SOC oder Executive und fällt für andere registrierte Rollen auf SOC zurück.

Der SOC-Workspace besitzt eine eigene Layoutgrenze, eine Page-Registry und einen `SOCWorkspaceContext`. Der Context hält ausgewählte Findings, Assets, Investigations, Threat-Intelligence-Einträge und Exposures über Fokuswechsel innerhalb des gemounteten SOC-Workspace hinweg. Die Sidebar verändert dafür eine aktive Navigation-ID; die aktive Page wird innerhalb des Workspace gewählt. Die vorhandenen `route`-Werte der Navigation und der installierte Browser-Router bilden diesen Fokuspfad derzeit nicht vollständig als URL-Routing ab. Der Executive-Workspace besitzt Navigation und Layouts, aber noch keinen vergleichbaren langlebigen Workspace-Kontext oder vollständigen Fokuspfad.

Damit existieren bereits Teile einer persistenten Arbeitsumgebung, jedoch noch kein einheitlicher Vertrag für Plattformzustand, Workspacezustand, Seitenzustand, Routing und Isolation. Ein klassisches Seitenmodell würde jeden Funktionswechsel als weitgehend unabhängige Ansicht behandeln. Das gefährdet den Arbeitskontext operativer Rollen und begünstigt unterschiedliche Composition Roots je Rolle. Umgekehrt darf eine Mission Console weder zu globalem, unkontrolliertem UI-Zustand noch zu einer Verlagerung fachlicher Berechnung ins Frontend führen.

ADR-0001 bis ADR-0004 legen `DecisionResult` als fachliche Single Source of Truth sowie Explainability als read-only Projektion fest. Das Workspace-Modell muss diese Verträge konsumieren, darf sie aber nicht ersetzen, ergänzend berechnen oder rollenabhängig neu interpretieren.

## Entscheidung

PredatorAI verwendet das **Mission-Console-Modell** als verbindliches Interaktions- und Composition-Prinzip für alle Rollen-Workspaces.

Ein **Workspace** ist die isolierte, rollenbezogene Arbeitsgrenze innerhalb der Plattform. Er besitzt genau eine **Mission Console** als langlebigen Composition Root für seine Darstellung und Interaktion. Die Mission Console hält den gemeinsamen Arbeitskontext des aktiven Workspace und komponiert mindestens logisch folgende Flächen, soweit sie für die Rolle erforderlich sind:

```text
Platform
└── Active Workspace
    └── Mission Console
        ├── Primary Work Area
        ├── Context Panels
        ├── Decision Surface
        ├── Timeline
        ├── Evidence
        └── Intelligence
```

Die Aufzählung definiert Verantwortungsflächen, keine verpflichtende sichtbare Panel-Anzahl und kein konkretes Layout. Nicht benötigte Flächen dürfen für einen Rollen-Workflow entfallen oder anders angeordnet werden. Eine Rolle erhält dennoch keine zweite Mission Console und keinen parallelen Workspace-Composition-Root.

### Plattform und Workspace

Die Plattform verantwortet ausschließlich globale Presentation- und Session-Belange: authentifizierte Identität, verfügbare Workspaces, aktiven Workspace, globale Shell, übergreifende Navigationseinstiege sowie technisch notwendige globale Einstellungen. Sie besitzt keine rollenbezogenen Entitätsauswahlen und keine fachlichen Decision-Invarianten.

Der Workspace verantwortet die rollenbezogene Navigation, Darstellung, KPIs, Workflows, lokale Auswahl- und Fokuszustände sowie die Composition seiner Mission Console. Er darf kanonische Backend-Ergebnisse für die Rolle darstellen, aber keine fachlichen Berechnungen oder konkurrierenden Modelle erzeugen.

### State Ownership

Zustand wird nach Lebensdauer und Verantwortungsgrenze geteilt:

1. **Plattformzustand** gehört zur Plattformgrenze. Dazu zählen authentifizierte Benutzeridentität, autorisierte Workspace-Verfügbarkeit, aktiver Workspace und globale Presentation-Einstellungen. Er darf Workspace-Details nur über stabile Identitäten referenzieren.
2. **Workspacezustand** gehört genau einer Mission Console. Dazu zählen aktive Arbeitsauswahl, rollenbezogene Filter, Panelzustände, lokale Zeitbereiche und der aktuelle Arbeitskontext. Er bleibt bei Fokuswechseln innerhalb desselben Workspace erhalten und wird beim Verlassen nicht automatisch in einen anderen Workspace übertragen.
3. **Fokuszustand** bezeichnet die aktuell sichtbare Arbeitsfläche innerhalb der Mission Console. Er darf über Navigation und Routing adressierbar sein, ist aber kein eigener fachlicher Zustand.
4. **Seiten- oder Komponentenstatus** ist kurzlebiger Presentation-Zustand einer konkreten Fläche, etwa ein offenes Menü oder ein noch nicht übernommener Eingabewert. Er bleibt lokal und wird nicht ohne begründete Lebensdauer in den Workspacezustand gehoben.
5. **Serverzustand** umfasst fachliche Daten und autoritative Workflow-Ergebnisse. Er verbleibt im Backend beziehungsweise in der kontrollierten Client-Cache-Schicht und wird nicht als veränderliche Kopie im Workspace-Context zur zweiten Wahrheit.

State wird am engsten sinnvollen Owner gehalten. Die Architektur schreibt keine konkrete State-Management-Bibliothek vor.

### Workspace Isolation

Jeder aktive Workspace besitzt eine eigene Mission-Console-Instanz und einen eigenen Zustandsscope. Ein Workspace darf weder Contexts noch veränderlichen Auswahlzustand eines anderen Workspace importieren. Gemeinsame UI-Komponenten und strikt typisierte, unveränderliche Presentation-Verträge dürfen wiederverwendet werden; rollenbezogene Orchestrierung bleibt am jeweiligen Workspace.

Beim Workspace-Wechsel werden keine nicht autorisierten Daten, Filter oder Entitätsauswahlen in den Ziel-Workspace übernommen. Ein kontrollierter Deep Link darf stabile Identitäten weitergeben, sofern das Backend die Zielrolle und den Zugriff erneut autorisiert. Rollenbezogene Verantwortung bleibt gemäß `AGENTS.md` getrennt:

* **SOC Analyst:** Live Incidents, Investigations und Alerts.
* **Threat Hunter:** Threat Hunting, MITRE-Bezug und Pivoting.
* **Incident Response:** Containment, Timeline und Evidence.
* **Risk Manager:** Business Impact und Priorisierung.
* **Executive:** KPIs, Business Risk und Executive Summary.
* **CISO:** Governance, Compliance und Enterprise Risk.
* **Administrator:** Plattform, AI Models und Integrationen.

Die Rolle bestimmt Arbeitsauftrag und Darstellung, nicht die fachliche Wahrheit. Rollen dürfen unterschiedliche autorisierte Ausschnitte derselben kanonischen Daten sehen; daraus folgt kein Anspruch auf identischen Datenzugriff.

### Persistenzgrenzen

Persistenz ist explizit und datensparsam:

* URL beziehungsweise Router dürfen Workspace-Identität, Fokusziel und sichere, stabile Ressourcenreferenzen tragen, damit Navigation, Refresh, Deep Links und Browser-Historie nachvollziehbar bleiben.
* Kurzlebiger Komponentenstatus wird nicht persistiert.
* Workspacezustand bleibt standardmäßig im Speicher der Mission-Console-Instanz. Eine Persistenz über Reload oder Sitzung hinaus benötigt einen separat freigegebenen Vertrag mit Zweck, Ablaufzeit, Schema-Version und Datenschutzbewertung.
* Browser-Speicher darf keine Secrets, Tokens, Evidence-Inhalte, vollständigen Decisions oder andere sensible fachliche Daten als Komfortzustand persistieren.
* Dauerhafte fachliche oder auditrelevante Daten werden ausschließlich über autorisierte Backend-Verträge gespeichert.

Dieser ADR entscheidet weder eine konkrete Storage-Technologie noch eine Offline-Fähigkeit.

### Navigation, Routing und Fokussteuerung

**Navigation** beschreibt die autorisierten, rollenbezogenen Möglichkeiten, den Arbeitsfokus zu verändern. **Routing** bildet einen adressierbaren Fokus auf URL und Browser-Historie ab. **Fokussteuerung** aktiviert innerhalb der bestehenden Mission Console die zugehörige Primary Work Area und ihre Context Panels.

Navigation ersetzt die Mission Console nicht und mountet nicht für jeden Fokus einen unabhängigen Rollen-Workspace. Routing ist die adressierbare Projektion des Fokus und darf nicht als zweiter Zustandsowner neben der Mission Console auftreten. Route und Workspacezustand müssen über eine eindeutige, zentral definierte Abbildung synchronisiert werden. Nicht adressierbare, kurzlebige UI-Details bleiben lokaler Zustand.

### Autorisierung und Verantwortungsgrenzen

Workspace-Registry, Navigationseinträge, ausgeblendete Komponenten und clientseitige Route Guards sind Presentation- und Bedienmechanismen, keine Sicherheitsgrenzen. Authentifizierung, Autorisierung, Mandantenisolation, Feld- und Ressourcenfreigaben werden bei jedem Backend-Zugriff serverseitig durchgesetzt. Das Frontend zeigt ausschließlich den autorisierten Ausschnitt.

`DecisionResult` bleibt gemäß ADR-0001 die fachliche Single Source of Truth. Execution Trace bleibt gemäß ADR-0002 vom Decision-Ergebnis getrennt. Explainability bleibt gemäß ADR-0003 ein read-only Read Model und ihre Vollständigkeit folgt ADR-0004. Workspaces dürfen diese Verträge auswählen, anordnen, filtern und darstellen, jedoch keine fehlenden Fakten erzeugen, Entscheidungen verändern oder Explainability plausibilisieren.

## Begründung

Das Mission-Console-Modell passt zum vorhandenen Plattform-Shell- und Workspace-Ansatz und entwickelt den bereits im SOC-Context erkennbaren gemeinsamen Arbeitskontext weiter. Es reduziert Kontextverlust zwischen zusammengehörigen Tätigkeiten, ermöglicht rollenbezogene Workflows auf gemeinsamen Backend-Verträgen und verhindert, dass jede Page oder Rolle eine eigene Plattformarchitektur etabliert.

Die explizite Trennung der Zustandsowner begrenzt zugleich das Hauptrisiko langlebiger Workspaces: unkontrollierten globalen Zustand. URL-adressierbarer Fokus unterstützt Accessibility, Deep Links und Browser-Navigation, während fachlicher Zustand und Autorisierung im Backend verbleiben. Die Entscheidung legt Verantwortungsgrenzen fest, ohne ein Framework, eine Komponentenstruktur oder eine Migration vorwegzunehmen.

## Konsequenzen

### Positiv

* Arbeitskontext bleibt bei Fokuswechseln innerhalb eines Workspace erhalten.
* Alle Rollen folgen demselben Composition-Prinzip, ohne ihre Verantwortlichkeiten zu vermischen.
* Plattform-, Workspace-, Fokus-, Komponenten- und Serverzustand besitzen überprüfbare Owner.
* Gemeinsame UI-Bausteine sowie Decision-, Explainability-, Evidence- und Timeline-Darstellungen können kontrolliert wiederverwendet werden.
* Deep Links, Browser-Historie und Accessibility können auf einen stabilen Fokusvertrag ausgerichtet werden.
* Neue Rollen benötigen keine neue Plattformarchitektur.

### Negativ

* Langlebige Mission Consoles erhöhen Anforderungen an State-Lifecycle, Speicherverbrauch und Render-Performance.
* URL, aktive Navigation und Workspace-Fokus müssen konsistent synchronisiert werden.
* Workspace-Wechsel und Berechtigungsänderungen benötigen explizite Bereinigung sensibler Zustände.
* Die heterogenen bestehenden SOC- und Executive-Strukturen benötigen eine schrittweise Migration.
* Einheitliche Composition-Regeln begrenzen lokale, page-spezifische Sonderlösungen.

## Alternativen

### Klassisches Seitenmodell

Jede Navigation öffnet eine unabhängige Page mit eigenem Composition Root und lokalem Zustand. Dies ist einfach zu routen und ermöglicht kleine initiale Komponenten. Es wurde nicht gewählt, weil zusammenhängende Analystenarbeit bei jedem Seitenwechsel Kontext verliert, Auswahlzustand dupliziert wird und Rollen leicht voneinander abweichende Daten- und Layoutpfade entwickeln.

### Unbegrenzte Single-Page-Konsole mit globalem State

Alle Rollen und Funktionen teilen eine dauerhaft gemountete Oberfläche und einen globalen Store. Dies maximiert unmittelbare Kontextverfügbarkeit, verletzt jedoch Workspace Isolation, erschwert Autorisierung und Lifecycle, erhöht Performance-Risiken und vermischt Rollenverantwortlichkeiten. Diese Alternative wurde verworfen.

### Rollenspezifische, unabhängige Anwendungen

Jede Rolle erhält eine eigene Shell, Navigation und Datenintegration. Dadurch könnten einzelne Rollen autonom entwickelt werden. Die Folge wären parallele Plattformarchitekturen, duplizierte Komponenten und driftende Decision- und Explainability-Darstellungen. Dies widerspricht dem Prinzip „No Parallel Architectures“.

### Hybrides Mission-Console-Modell ohne adressierbaren Fokus

Eine persistente Konsole wechselt ausschließlich lokalen Zustand; URLs bleiben unverändert. Dies reduziert Routing-Aufwand, beeinträchtigt aber Deep Links, Browser-Historie, Wiederherstellung und Accessibility. Es wurde zugunsten einer Mission Console mit klar abgegrenztem, adressierbarem Fokus abgelehnt.

## Abgrenzung

Dieser ADR definiert weder konkrete React-Komponenten noch Layoutmaße, Breakpoints, Panel-Anordnung, State-Bibliothek, Router-Konfiguration, API-Endpunkte oder Backend-Services. Er führt keine neuen Domainmodelle, Rollenberechtigungen, Datenverträge, KPIs oder fachlichen Workflows ein. Er entscheidet nicht über Multi-Workspace-Tabs, Offline-Betrieb, kollaborative Echtzeitsitzungen oder dauerhafte Workspace-Snapshots.

## Migration

Die Einführung erfolgt in separat freigegebenen, kleinen AIDP-Tasks und ohne parallelen zweiten Workspace-Pfad:

1. Bestehende Plattform-Shell, Workspace-Registry und `WorkspaceOutlet` bleiben der Composition-Einstieg.
2. Pro Rolle wird die vorhandene Workspace-Komponente schrittweise zur einzigen Mission-Console-Grenze weiterentwickelt; vorhandene Pages werden zunächst als Fokusflächen wiederverwendet.
3. Navigation-ID, Route und Fokus werden über einen einzigen, versionierbaren Mapping-Vertrag vereinheitlicht. Bestehende URLs erhalten Weiterleitungen oder kompatible Zuordnungen, bevor alte Pfade entfallen.
4. Bestehender SOC-Auswahlzustand wird nach Lebensdauer klassifiziert und innerhalb der SOC-Grenze weiterverwendet oder enger lokalisiert; er wird nicht globalisiert.
5. Executive und weitere Rollen erhalten ihre Mission Console erst in eigenen Tasks. Der aktuelle SOC-Fallback für nicht implementierte Rollen darf nicht als Zielarchitektur gelten und muss vor produktiver Freigabe dieser Rollen kontrolliert ersetzt werden.
6. Autorisierung und Backend-Verträge werden nicht durch UI-Migration verändert. Jede migrierte Fläche muss weiterhin ausschließlich autorisierte kanonische Daten verwenden.

Rückwärtskompatibilität bedeutet, dass bestehende freigegebene Workspace-Einstiege und adressierbare URLs während der Migration funktionsfähig oder eindeutig weitergeleitet bleiben. Dieser ADR selbst ändert kein Laufzeitverhalten.

## Qualitäts- und Sicherheitsauswirkungen

### Security und Datenschutz

Die Workspace-Grenze reduziert unbeabsichtigte Datenweitergabe, ersetzt jedoch keine serverseitige Autorisierung. Zustände müssen bei Logout, Mandantenwechsel, Rollenverlust und nicht kompatiblem Workspace-Wechsel verworfen werden. Sensible Daten dürfen nicht unkontrolliert in URLs, Logs oder Browser-Speicher gelangen. Deep Links müssen Ressourcen serverseitig erneut autorisieren.

### Auditierbarkeit

Adressierbarer Fokus und eindeutige State-Owner verbessern die technische Nachvollziehbarkeit. Audit-Ereignisse entstehen weiterhin im Backend; UI-Navigation ist nicht automatisch ein fachliches Audit-Ereignis. Eine spätere Telemetrie benötigt einen eigenen freigegebenen Scope.

### Performance

Eine Mission Console darf nicht pauschal alle Fokusflächen gleichzeitig rendern oder Daten laden. Implementierungen müssen selektives Laden, stabile Context-Werte, begrenzte Cache-Lebensdauer und kontrolliertes Unmounting großer Teilflächen prüfen. Performancebudgets werden durch diesen ADR nicht festgelegt.

### Accessibility

Fokuswechsel müssen programmatisch nachvollziehbar sein, sinnvolle Überschriften und Landmarks erhalten und Tastatur- sowie Screenreader-Navigation unterstützen. URL und Browser-Historie sollen wesentliche Fokuswechsel abbilden. Visuelle Panels dürfen keine notwendige Lesereihenfolge voraussetzen.

### Kompatibilität und Tests

Der Architekturvorschlag ist additiv und ändert keine bestehenden Verträge. Spätere Implementierungstasks benötigen fokussierte Tests für Workspace Isolation, Route/Fokus-Synchronisation, Zustandsbereinigung, Berechtigungsgrenzen und bestehende Deep Links sowie Typecheck und UI-Smoke-Tests gemäß ihrem Scope.

## Referenzen

* `TASK-0020`
* `AGENTS.md`
* `ARCHITECTURE.md`
* ADR-0001 – DecisionResult as Canonical Decision Contract
* ADR-0002 – Canonical Execution Trace Contract
* ADR-0003 – Canonical Explainability Projection Contract
* ADR-0004 – Explainability Completeness Contract
* `frontend/src/platform/layout/PlatformLayout.tsx`
* `frontend/src/platform/workspace/WorkspaceOutlet.tsx`
* `frontend/src/workspaces/registry/WorkspaceRegistry.ts`
* `frontend/src/workspaces/registry/WorkspaceNavigation.ts`
* `frontend/src/workspaces/soc/SOCWorkspace.tsx`
* `frontend/src/workspaces/soc/SOCWorkspaceContext.tsx`
* `frontend/src/workspaces/executive/ExecutiveWorkspace.tsx`

## Architektur-Review

Status: APPROVED  
Bemerkungen: Architecture Review für TASK-0020 mit `PASS` abgeschlossen. Der Scope wurde eingehalten; ADR-0005 ergänzt ADR-0001 bis ADR-0004 ohne Widerspruch. Die dokumentierten Risiken zu Navigation/Fokus-Synchronisation, Workspace-Persistenz und dem Fallback nicht implementierter Rollen sind keine Blocker und verbleiben für separat freizugebende Implementierungs-Tasks.  
Freigabe: Architect, 2026-08-04
