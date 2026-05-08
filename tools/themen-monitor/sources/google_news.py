"""
Google News (RSS) Source — kein API-Key noetig.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

import feedparser

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.google-news")


def fetch(mock: bool = False) -> list[dict]:
    if mock:
        return [{
            "source": "Google News (mock)",
            "title": "Mock-Headline: Klimaschutz im Bundestag",
            "url": "https://example.org/mock1",
            "published_at": "2026-05-04T08:30:00",
            "snippet": "Im Bundestag wurde heute ueber das neue Klimaschutzgesetz debattiert.",
        }]
    keywords = get("themen_monitor.google_news.keywords", default=[])
    items: list[dict] = []
    for kw in keywords:
        url = f"https://news.google.com/rss/search?q={quote_plus(kw)}&hl=de&gl=DE&ceid=DE:de"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                items.append({
                    "source": f"Google News — {kw}",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "snippet": entry.get("summary", ""),
                })
        except Exception as e:
            log.warning("Google News '%s' fehlgeschlagen: %s", kw, e)
    return items
