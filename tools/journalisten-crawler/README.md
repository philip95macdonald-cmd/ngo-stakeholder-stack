# journalisten-crawler

Crawlt Impressums-, Kontakt- und Pressestellen-Seiten von Medien-Domains
und extrahiert Journalist:innen-Kontaktdaten in das Stakeholder-CSV-Schema.

Crawlt Impressums- und Kontaktseiten von Medien-Domains und extrahiert
Journalist:innen-Kontaktdaten in das Stakeholder-CSV-Schema (~1800 LoC, 28 Tests).

**Konfigurationsschritte für deine NGO:**

1. `domains.txt` durch deine Themen-Medien ersetzen (taz, klimareporter, etc.)
2. `User-Agent`-String anpassen: `ngo-stakeholder-stack-crawler/0.1 (+https://deine-ngo.org/bot)`
3. CSV-Output-Spalten mit `tools/_shared/csv_schema.py` abgleichen

## Was übernommen wird

| Modul | Zweck | Änderungs-Bedarf |
|---|---|---|
| `robots_checker.py` | robots.txt-Compliance | keine |
| `http_client.py` | Session, Retry, Rate-Limit | keine (durch `_shared/http_client.py` ersetzt) |
| `ner_extractor.py` | NER-Fallback via spaCy | keine |
| `playwright_client.py` | JS-Render-Pass | keine |
| `publisher_groups.py` | Markenfamilien dedupen | Domain-Liste anpassen |
| `crawl-resumable.py` | Persistierter State | keine |
| `main.py` | Pipeline-Orchestrierung | CSV-Output-Format anpassen |
| `tests/` | 28 Pytest | Domain-Mocks anpassen |

## Schema

```
contacts.csv: email, first_name, last_name, organisation, role, source_url, confidence, tags, custom_fields
Tags pro Kontakt: [stakeholder:journalist, topic:<theme>, region:<de|eu>, lang:<de|en>]
```

## Skeleton-Status

`config_loader.py` als minimaler Stub vorhanden — Smoketest läuft grün.
Vollständige Implementierung folgt in Phase 0 (Crawler-Module einbinden, Tests portieren).
