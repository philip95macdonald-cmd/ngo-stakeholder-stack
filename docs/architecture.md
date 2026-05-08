# Architektur (Kurzfassung)

> Architektur-Überblick als Plain-Markdown.

## Datenfluss

```
        ┌────────────────────────┐
        │ journalisten-crawler   │ ─┐
        │  Output: contacts.csv  │  │
        └────────────────────────┘  │   ┌────────────────┐    ┌────────┐
                                    ├──▶│  brevo-sync    │───▶│ Brevo  │
        ┌────────────────────────┐  │   │  Multi-Tag     │    │ Listen │
        │ politik-connector      │ ─┘   │  Custom-Fields │    └────────┘
        │  Output: contacts.csv  │      └────────────────┘
        └────────────────────────┘

        ┌────────────────────────┐      ┌────────────────────────────┐
        │ themen-monitor         │ ───▶ │ HTML-Report + Krisen-Alert │
        │  Sources/* (Mock+Live) │      │ E-Mail / Slack             │
        └────────────────────────┘      └────────────────────────────┘

        ┌────────────────────────┐      ┌────────────────────────────┐
        │ impact-story-builder   │ ───▶ │ Markdown / HTML / Brevo    │
        │  Proof Chain (YAML)    │      │ Newsletter-Template        │
        └────────────────────────┘      └────────────────────────────┘
```

## Komponenten

| Tool | Sprache | Externe Deps | API/Auth |
|---|---|---|---|
| `_shared/` | Python 3.10+ | `requests`, `pyyaml` | — |
| `journalisten-crawler/` | Python | + `bs4`, `lxml`, optional `spacy`, `playwright` | — |
| `politik-connector/` | Python | + `click` | Abgeordnetenwatch (keine Auth) |
| `brevo-sync/` | Python | + `click`, `python-dotenv` | Brevo API-Key |
| `themen-monitor/` | Python | + `feedparser`, `bs4` | Twitter Bearer (opt), YouTube Key (opt), SMTP |
| `impact-story-builder/` | Python | + `click` | — |

## Datenmodell

Alle Tools schreiben/lesen das **Stakeholder-CSV-Schema** aus
`tools/_shared/csv_schema.py`:

| Spalte | Typ | Beispiel |
|---|---|---|
| email | str (PK) | `kontakt@beispiel.de` |
| first_name, last_name | str | `Anna`, `Beispiel` |
| organisation | str | `Bundestag` / `taz` / — |
| role | str | `MdB` / `Redakteur:in` |
| source_url | str | `https://...` |
| confidence | float [0,1] | `0.85` |
| tags | str (pipe-separiert) | `stakeholder:politiker\|party:gruene` |
| custom_fields | str (JSON) | `{"PARLIAMENT_ID": 12345}` |

## Konfiguration

Drei YAML-Files zentral:

- `configs/ngo.yaml` — NGO-Stamm (Name, Themen, Regionen, Tonalität)
- `configs/sources.yaml` — Quellen-Listen (Crawler-Domains, Parlamente, Monitor-Quellen)
- `configs/brevo.yaml` — Listen-IDs, Custom-Fields, Tag-Konvention

Geheimnisse in `.env` (gitignored).

## Tests

| Tool | Test-Status | Coverage |
|---|---|---|
| `_shared/` | Skeleton | Manuell |
| `journalisten-crawler/` | TBD | 28 Tests Referenz |
| `politik-connector/` | 5 Pytest-Tests aktiv | API-Parsing + CSV-Schema |
| `brevo-sync/` | TBD | — |
| `themen-monitor/` | TBD | — |
| `impact-story-builder/` | 5 Pytest-Tests aktiv | Render + Validate |

## CI

GitHub Actions mit zwei Stages:

1. **smoke** — 5 Jobs, einer pro Tool, prüft Imports + `--help`
2. **test** — pytest pro Tool, läuft nach erfolgreichem smoke

## DSGVO-Defaults

- Doppel-Opt-In bei jedem Newsletter-Signup, jeder Petition
- Granulare Consent-Tags pro Kommunikations-Kanal
- Audit-Log auf allen Schreib-Operationen (geplant Phase 7)
- Lösch-Konzept: 24 Monate Inaktivität → automatische Bereinigung
- Brevo-Suppression-Liste wird ausnahmslos respektiert
