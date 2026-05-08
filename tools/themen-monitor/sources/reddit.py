"""
Reddit JSON-API (anonym, kein Auth noetig fuer Public-Subreddits).
"""

from __future__ import annotations

import sys
from pathlib import Path

from datetime import datetime, timezone

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.reddit")
UA = "ngo-stakeholder-stack/0.1"
_KEYWORDS: list[str] = []  # optional keyword filter, populated from config


def fetch(mock: bool = False) -> list[dict]:
    if mock:
        return [{
            "source": "r/Umweltschutz (mock)",
            "title": "Mock: Diskussion zur Energiewende",
            "url": "https://reddit.com/r/Umweltschutz/comments/abc",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "snippet": "Die Diskussion zeigt geteilte Meinungen zur Energiewende.",
        }]

    subs = get("themen_monitor.social.reddit_subreddits", default=[])
    keywords = [k.lower() for k in get("themen_monitor.google_news.keywords", default=[])]
    items: list[dict] = []

    for sub in subs:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/new.json?limit=25",
                headers={"User-Agent": UA},
                timeout=15,
            )
            r.raise_for_status()
            for child in r.json().get("data", {}).get("children", []):
                d = child.get("data", {})
                title: str = d.get("title", "")
                text: str = d.get("selftext", "")

                # Optional keyword filter — only include if no keywords set or one matches
                if keywords:
                    combined = (title + " " + text).lower()
                    if not any(kw in combined for kw in keywords):
                        continue

                epoch = d.get("created_utc", 0)
                pub = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat() if epoch else ""
                items.append({
                    "source": f"r/{sub}",
                    "title": title,
                    "url": "https://reddit.com" + d.get("permalink", ""),
                    "published_at": pub,
                    "snippet": text[:280],
                })
        except Exception as e:
            log.warning("Reddit r/%s fehlgeschlagen: %s", sub, e)

    return items
