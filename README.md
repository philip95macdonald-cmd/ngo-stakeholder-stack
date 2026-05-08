# NGO Stakeholder Stack — Toolkit

Ein Open-Source Python-Toolkit für die Stakeholder-Kommunikation einer NGO.
Modulare Architektur — nimm was du brauchst. Erprobt in der Praxis, generalisiert
für den gemeinnützigen Einsatz.

Komponenten: Pressekontakt-Crawler, Politik-Connector (Abgeordnetenwatch),
Brevo-Sync, Themen-Monitor, Impact-Story-Builder.

## Was hier drin ist

```
ngo-stakeholder-stack/
├── README.md                  ← du bist hier
├── QUICKSTART.md              5-Minuten-Setup für eine neue NGO
├── docs/
│   ├── architecture.md        Architektur-Überblick
│   └── stakeholder-tags.md    Tag-Konvention
├── configs/
│   ├── ngo.example.yaml       Top-Level-Config (Name, Themen, Brand)
│   ├── sources.example.yaml   Quellen-Listen (Medien, Politik, Förderer)
│   └── brevo.example.yaml     Listen- und Field-Mapping
├── tools/
│   ├── _shared/               Geteilte Module (HTTP, Logging, Konfig-Loader)
│   ├── journalisten-crawler/  Pressekontakt-Crawler (Bestand, generalisiert)
│   ├── politik-connector/     NEU: Abgeordnetenwatch + Bundestag-API
│   ├── brevo-sync/            CSV → Brevo, Multi-Tag-Schema
│   ├── themen-monitor/        Themen + Allianzen + Krisen + Förderer
│   └── impact-story-builder/  NEU: Beneficiary-Stories mit Proof Chain
├── scripts/
│   ├── smoke.sh               End-to-End-Funktionsprüfung aller Tools
│   └── new-ngo.sh             Skript: Configs aus Templates für neue NGO ableiten
├── tests/                     Geteilte Pytest-Hilfen + Fixtures
├── .env.example               Vorlage für API-Keys
├── .gitlab-ci.yml             CI-Pipeline (Smoke + Test)
├── install.sh                 Idempotenter Installer
└── requirements.txt           Top-Level-Dependencies
```

## Tool-Reihenfolge im Workflow

```
┌────────────────────────┐    ┌────────────────────┐    ┌────────────┐
│ journalisten-crawler   │    │                    │    │            │
│  Output: contacts.csv  │───▶│   brevo-sync       │───▶│   Brevo    │
└────────────────────────┘    │   CSV → Listen     │    │   Listen   │
┌────────────────────────┐    │   Tags + Custom-   │    └────────────┘
│ politik-connector      │───▶│   Fields           │           │
│  Output: contacts.csv  │    │                    │           │
└────────────────────────┘    └────────────────────┘           │
                                                                ▼
                                                       ┌─────────────────┐
                                                       │ Newsletter,     │
                                                       │ Storytelling,   │
                                                       │ Politiker-Mails │
                                                       └─────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ themen-monitor (eigenständig)                                       │
│   Pollt: News, Allianzen, Politik, Förderer, Social, Krisen         │
│   Output: täglicher HTML-Report → E-Mail an Comms-Team              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ impact-story-builder (manuell aufgerufen)                           │
│   Input: YAML mit Beneficiary-Daten                                 │
│   Output: Markdown-Story + Brevo-Template                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Setup (lokal)

```bash
git clone <dein-fork> ngo-stakeholder-stack
cd ngo-stakeholder-stack
bash install.sh --with-deps
cp .env.example .env && $EDITOR .env
cp configs/ngo.example.yaml configs/ngo.yaml && $EDITOR configs/ngo.yaml
bash scripts/smoke.sh
```

Wenn der Smoketest grün ist, ist der Stack einsatzbereit. Detaillierte
Schritt-für-Schritt-Anleitung in [`QUICKSTART.md`](QUICKSTART.md).

## Constraints und Defaults

- **Sprache:** Python 3.10+
- **Lizenz:** MIT (Default — anpassbar)
- **DSGVO:** Doppel-Opt-In, granulare Consent-Tags, Audit-Log auf allen Schreib-Operationen
- **Open-Source-First:** vor Eigenbau prüfen, ob CiviCRM, Mautic, openPetition o.ä. die Aufgabe lösen
- **Keine generierten Beneficiary-Quotes** — Storytelling-Builder ist Strukturierungs-, kein Erzeugungs-Tool
- **Keine Crawls auf Spender-Daten** — Spender kommen nur aus eigenen Spendenformen

## Status der Komponenten

| Komponente | Status | Quelle |
|---|---|---|
| `_shared` | Skeleton | neu für diese Vorlage |
| `journalisten-crawler` | Skeleton mit Beispiel-Modulen | erprobt in der Praxis |
| `politik-connector` | Funktionsfähiger Skeleton mit Abgeordnetenwatch-Adapter | neu |
| `brevo-sync` | CLI + List-/Sync-Skeleton | adaptiert |
| `themen-monitor` | Skeleton mit Source-Stubs | erprobt in der Praxis |
| `impact-story-builder` | Voll funktionsfähig (Markdown-Output) | neu |

"Skeleton" heißt: Architektur steht, Schlüssel-Funktionen sind implementiert,
Tests-Hülle existiert, manuelle End-to-End-Tests laufen. Produktive
Härtung (Error-Handling, Retry-Logic, vollständige Test-Coverage) ist
Aufgabe der nächsten Iteration.

## Nächste Schritte

1. **Phase 0 (3–5 Tage):** Config-Werte für deine NGO setzen (`configs/ngo.yaml`), Bravo-Listen anlegen
2. **Phase 1 (3–5 Tage):** Stakeholder-Tag-Schema in `configs/brevo.yaml` verfeinern
3. **Phase 2 (5–7 Tage):** Politik-Connector aktivieren, erste Live-Daten aus Abgeordnetenwatch ziehen
4. **Phase 3 (5–7 Tage):** Themen-Monitor-Quellen anpassen (Allianzen, Förderer, Themen-Feeds)
5. **Phase 4 (3–5 Tage):** Compliance-Dokumentation, Verzeichnis von Verarbeitungstätigkeiten

Schätzung MVP: 19–28 Tage Vollzeit-Engineering.
