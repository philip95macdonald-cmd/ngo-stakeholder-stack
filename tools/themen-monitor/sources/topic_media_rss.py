"""
Topic-Media-RSS (Themen-spezifische Medien wie klimareporter, taz Klimakurs, ...).
"""

from __future__ import annotations

import sys
from pathlib import Path

import feedparser

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.topic-media")


def fetch(mock: bool = False) -> list[dict]:
    if mock:
        return [{
            "source": "klimareporter (mock)",
            "title": "Mock: Erneuerbare-Anteil steigt",
            "url": "https://example.org/mock-klimareporter",
            "published_at": "2026-05-04T07:45:00",
            "snippet": "Ein neuer Bericht zeigt einen Rekord-Anteil erneuerbarer Energien...",
        }]
    media = get("themen_monitor.topic_media", default=[])
    items: list[dict] = []
    for m in media:
        try:
            feed = feedparser.parse(m["rss"])
            for entry in feed.entries[:10]:
                items.append({
                    "source": m.get("name", "Topic-Medium"),
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "snippet": entry.get("summary", ""),
                })
        except Exception as e:
            log.warning("RSS %s fehlgeschlagen: %s", m.get("name"), e)
    return items
