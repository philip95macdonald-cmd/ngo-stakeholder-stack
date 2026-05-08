# themen-monitor

Tägliche Übersicht: was passiert in unseren Themen, bei unseren Allianz-
Partnern, in der Politik, bei Förderern, in der Krise. Versand als
HTML-Report per E-Mail (oder Slack als Alternative).

Basiert auf einem erprobten Presse-Monitor-Stack, erweitert für NGO-Anforderungen:

- ✓ Google News Quelle bleibt
- ✓ Social-Quellen (Twitter, YouTube, Reddit) bleiben
- ✓ Mock-Modus für CI bleibt
- — Wettbewerber-Crawl entfernt
- + **Allianz-Monitor** ergänzt
- + **Politik-Themen-Monitor** ergänzt (Bundestags-Drucksachen)
- + **Förder-Watch** ergänzt
- + **Krisen-Detektor** ergänzt (Anomalie-Erkennung)
- + Mastodon + Bluesky vorbereitet

## CLI

```bash
# Mock-Lauf, nur Report bauen
python main.py --mock --report-only

# Live-Lauf, Report bauen + per E-Mail an SMTP_TO senden
python main.py --live

# Nur Krisen-Check (für Cron alle 15 Min)
python main.py --crisis-only
```

## Quellen-Stubs

Jede Quelle ist ein eigenes Modul unter `sources/`. Das gemeinsame
Interface ist:

```python
from typing import Protocol

class Source(Protocol):
    name: str

    def fetch(self) -> list[dict]:
        """Liefert Items als [{title, url, published_at, snippet, sentiment?}]"""
```

Implementierungs-Status der Quellen:

| Quelle | Datei | Status |
|---|---|---|
| Google News | `sources/google_news.py` | Skeleton mit Beispiel |
| Topic Media (RSS) | `sources/topic_media_rss.py` | Skeleton |
| Allianzen | `sources/alliances.py` | Skeleton |
| Bundestag-Drucksachen | `sources/bundestag_topics.py` | TODO |
| Förderer | `sources/funding_calls.py` | TODO |
| Twitter | `sources/twitter.py` | Skeleton (auth-pflichtig) |
| YouTube | `sources/youtube.py` | TODO |
| Reddit | `sources/reddit.py` | Skeleton |
| Mastodon | `sources/mastodon.py` | TODO |
| Bluesky | `sources/bluesky.py` | TODO |

## Krisen-Detektor

Sucht Anomalien in den letzten 30 Tagen:

- **Volume-Spike:** Tagesvolumen &gt; 3 × Median der Vortage
- **Sentiment-Drift:** Tages-Sentiment &gt; 1.5 σ unter Mittelwert
- **Hashtag-Cluster:** neue, koordinierte Hashtag-Verwendung

Bei Trigger sofort Mail/Slack-Alert. Implementierung in
`crisis_detector.py`.
