"""
Twitter / X — API v2 Recent-Search.

Auth: TWITTER_BEARER_TOKEN in .env.
Graceful skip (leere Liste) wenn Token nicht gesetzt.

Kosten: Free-Tier erlaubt 500k Tweets/Monat (Stand 2026),
        reicht fuer NGO-Monitoring gut aus.
API-Doku: https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.twitter")

_API_BASE = "https://api.twitter.com/2/tweets/search/recent"
_MAX_RESULTS = 25  # pro Keyword-Query, max 100
_LOOKBACK_HOURS = 25  # etwas mehr als 24h, um Luecken zu vermeiden


def fetch(mock: bool = False) -> list[dict]:
    if mock:
        return [
            {
                "source": "Twitter/X (mock)",
                "title": "@beispiel_ngo: Klimaschutz heisst Handeln, nicht Reden.",
                "url": "https://twitter.com/beispiel_ngo/status/123",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "snippet": "Wir fordern: jetzt das Klimaschutzgesetz verabschieden. #klimaschutz",
            }
        ]

    token = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
    if not token:
        log.info("Kein TWITTER_BEARER_TOKEN gesetzt — Twitter-Quelle uebersprungen.")
        return []

    keywords = get("themen_monitor.social.twitter_keywords", default=[])
    if not keywords:
        log.info("Keine twitter_keywords konfiguriert.")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    since = (datetime.now(timezone.utc) - timedelta(hours=_LOOKBACK_HOURS)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Alle Keywords in eine ODER-Query zusammenfassen (weniger API-Calls)
    query_terms = " OR ".join(f'"{kw}"' for kw in keywords[:10])
    query = f"({query_terms}) lang:de -is:retweet"

    params = {
        "query": query,
        "max_results": _MAX_RESULTS,
        "start_time": since,
        "tweet.fields": "created_at,author_id,text,public_metrics",
        "expansions": "author_id",
        "user.fields": "name,username",
    }

    items: list[dict] = []
    try:
        resp = requests.get(_API_BASE, headers=headers, params=params, timeout=20)

        if resp.status_code == 401:
            log.error("Twitter 401 Unauthorized — Bearer-Token ungueltig.")
            return []
        if resp.status_code == 403:
            log.error("Twitter 403 Forbidden — kein Zugriff auf Search-Endpoint (Free-Tier?).")
            return []
        if resp.status_code == 429:
            log.warning("Twitter Rate-Limit erreicht — naechster Run in > 15 Min.")
            return []
        resp.raise_for_status()

        data = resp.json()
        tweets = data.get("data", [])

        # Nutzernamen-Lookup aus den Expansions
        users: dict[str, str] = {}
        for u in data.get("includes", {}).get("users", []):
            users[u["id"]] = f"@{u['username']}"

        for t in tweets:
            author = users.get(t.get("author_id", ""), "")
            title = f"{author}: {t['text'][:120]}" if author else t["text"][:140]
            pub_raw = t.get("created_at", "")
            try:
                pub = datetime.fromisoformat(pub_raw.replace("Z", "+00:00")).isoformat()
            except Exception:
                pub = pub_raw
            metrics = t.get("public_metrics", {})
            items.append({
                "source": "Twitter/X",
                "title": title,
                "url": f"https://twitter.com/i/web/status/{t['id']}",
                "published_at": pub,
                "snippet": (
                    f"Likes: {metrics.get('like_count', 0)}, "
                    f"Retweets: {metrics.get('retweet_count', 0)}"
                ),
            })

        log.info("Twitter: %d Tweets geladen (Query: %s)", len(items), query[:60])

    except requests.RequestException as exc:
        log.warning("Twitter-Fetch fehlgeschlagen: %s", exc)

    return items
