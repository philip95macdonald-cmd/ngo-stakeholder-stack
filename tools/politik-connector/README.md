# politik-connector

Pollt die [Abgeordnetenwatch.de API v2](https://www.abgeordnetenwatch.de/api)
und produziert ein CSV-File im Stakeholder-Schema (`tools/_shared/csv_schema.py`),
das vom `brevo-sync` direkt synchronisiert werden kann.

Optional: bundestag-api (offizielle Bundestag-API) für Drucksachen,
Plenarprotokolle, Ausschuss-Sitzungen — wird in Phase 2.5 ergänzt.

## Quellen

| Quelle | Auth | Zweck |
|---|---|---|
| Abgeordnetenwatch v2 | keine, fair-use | MdB/MdL/MdEP Stamm- und Kontaktdaten |
| Bundestag API | keine | Drucksachen, Antworten auf Anfragen |

## CLI

```bash
# Listen, welche Parlamente gerade aktiv sind
python main.py list-parliaments

# Bundestag (Mandate aktiv) einlesen
python main.py fetch --parliament bundestag --output ../../output/politiker/bundestag.csv

# Mehrere Parlamente in einem Lauf
python main.py fetch --parliament bundestag --parliament landtag-bw \
    --output ../../output/politiker/all.csv
```

## Output-Schema

Genau das Stakeholder-CSV-Schema aus `tools/_shared/csv_schema.py`:

| Spalte | Beispielwert |
|---|---|
| email | `kontakt@beispiel-mdb.de` |
| first_name | `Anna` |
| last_name | `Beispiel` |
| organisation | `Bundestag` |
| role | `MdB` |
| source_url | `https://www.abgeordnetenwatch.de/profile/anna-beispiel` |
| confidence | `1.00` (mit E-Mail) / `0.60` (ohne) |
| tags | `stakeholder:politiker\|party:gruene\|parliament:bundestag` |
| custom_fields | `{"PARLIAMENT_ID":12345,"PARTY":"Bündnis 90/Die Grünen","CONSTITUENCY":"Karlsruhe"}` |

## Rate-Limit-Verhalten

- Default 100 req/min (Abgeordnetenwatch fair-use)
- Per-Host Throttle aus `tools/_shared/http_client.py`
- Bei `429` Backoff via Retry-Adapter (3 Versuche, exponential)

## Tests

```bash
python -m pytest tests/ -v
```

12 Tests implementiert, deckt API-Parsing und CSV-Schreiben ab.
