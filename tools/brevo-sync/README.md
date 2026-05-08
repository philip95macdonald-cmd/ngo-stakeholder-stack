# brevo-sync

Synchronisiert ein Stakeholder-CSV (Schema: `tools/_shared/csv_schema.py`)
mit Brevo-Listen. Idempotent über E-Mail als Schlüssel: mehrfaches Laufen
erzeugt keine Duplikate.

Zwei Kernfeatures gegenüber einem simplen CSV-Import:

1. **Multi-Tag-Schema** — eine Person kann gleichzeitig Journalistin,
   Spenderin und Petitions-Unterzeichnerin sein.
2. **Konfigurierbares Field-Mapping** über `configs/brevo.yaml`.

## CLI

```bash
# Listen-Inventar
python sync.py list-lists

# Field-Inventar (welche Custom-Fields existieren bereits?)
python sync.py list-fields

# Fehlende Custom-Fields anlegen (basierend auf brevo.yaml)
python sync.py ensure-fields

# Trockendurchlauf — zeigt nur, was passieren würde
python sync.py sync ../../output/politiker/bundestag.csv \
    --list-id 3 --dry-run

# Echter Sync
python sync.py sync ../../output/politiker/bundestag.csv \
    --list-id 3
```

## Auth

`BREVO_API_KEY` in `.env`. Schlüssel-Generierung:
[https://app.brevo.com/security/api-keys](https://app.brevo.com/security/api-keys).

IP-Allowlist im Brevo-Dashboard: nicht vergessen, sonst gibt es 401er
trotz richtigem Key.

## Globale Suppression

Brevo hat eine globale Suppression-Liste (Bounces, Beschwerden, Opt-Outs).
Dieser Sync respektiert sie ausnahmslos — keine Möglichkeit zum Override.
Das ist DSGVO-Pflicht und wird auch im Code nicht aufgeweicht.
