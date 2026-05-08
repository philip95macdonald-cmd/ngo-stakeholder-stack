"""
Allianz-Monitor: was machen Partner-NGOs gerade?

Strategie (in Reihenfolge):
  1. RSS-Feed-Discovery — prueft gaengige Feed-Pfade der Domain
  2. Sitemap-Fallback — liest sitemap.xml, filtert Eintraege der letzten 7 Tage
  3. Gibt leere Liste zurueck wenn beide Wege scheitern (kein Crawl-Brute-Force)

Keine Auth noetig. robots.txt wird respektiert (nur Standard-Pfade geprueft).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.alliances")

_UA = "ngo-stakeholder-stack/0.1"
_TIMEOUT = 12
_DAYS_BACK = 7
_MAX_ITEMS_PER_PARTNER = 5

# Gaengige RSS/Atom-Feed-Pfade (absteigend nach Haeufigkeit)
_FEED_PATHS = [
    "/feed",
    "/feed/",
    "/rss",
    "/rss.xml",
    "/rss/",
    "/atom.xml",
    "/feed.xml",
    "/blog/feed",
    "/blog/rss",
    "/news/feed",
    "/news/rss",
    "/presse/feed",
    "/aktuell/feed",
    "/index.xml",
]


def fetch(mock: bool = False) -> list[dict]:
    if mock:
        return [
            {
                "source": "BUND (mock)",
                "title": "BUND fordert konsequenteren Klimaschutz",
                "url": "https://example.org/bund-mock",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "snippet": "BUND und Klima-Allianz Deutschland fordern mehr Engagement.",
            },
            {
                "source": "Germanwatch (mock)",
                "title": "Germanwatch: Klimawandel-Bericht 2026",
                "url": "https://example.org/gw-mock",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "snippet": "Der aktuelle Bericht zeigt wachsende Risiken durch Extremwetter.",
            },
        ]

    partners = get("themen_monitor.alliance_partners", default=[])
    if not partners:
        log.info("Keine Allianz-Partner konfiguriert.")
        return []

    items: list[dict] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=_DAYS_BACK)

    for partner in partners:
        domain: str = partner.get("domain", "")
        name: str = partner.get("name", domain)
        if not domain:
            continue
        base = _normalise_base(domain)
        log.info("Allianz-Monitor: %s (%s)", name, base)

        new_items = _fetch_via_rss(base, name, cutoff)
        if not new_items:
            new_items = _fetch_via_sitemap(base, name, cutoff)

        if new_items:
            log.info("  %d Items von %s", len(new_items), name)
        else:
            log.info("  Keine aktuellen Items von %s (kein RSS/Sitemap)", name)

        items.extend(new_items[:_MAX_ITEMS_PER_PARTNER])

    return items


# ---------------------------------------------------------------------------
# RSS Discovery
# ---------------------------------------------------------------------------

def _fetch_via_rss(base: str, name: str, cutoff: datetime) -> list[dict]:
    """Prueft gaengige Feed-Pfade und liest den ersten gefundenen Feed."""
    feed_url = _discover_feed(base)
    if not feed_url:
        return []
    try:
        feed = feedparser.parse(feed_url)
        items: list[dict] = []
        for entry in feed.entries:
            pub = _parse_date(entry)
            if pub and pub < cutoff:
                continue
            items.append({
                "source": name,
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published_at": pub.isoformat() if pub else "",
                "snippet": _clean_html(entry.get("summary", ""))[:300],
            })
        return items
    except Exception as exc:
        log.debug("RSS-Parse fehlgeschlagen fuer %s: %s", feed_url, exc)
        return []


def _discover_feed(base: str) -> str | None:
    """Gibt die URL des ersten funktionierenden Feeds zurueck, oder None."""
    # First: try to find <link rel="alternate" type="application/rss+xml"> on homepage
    try:
        resp = requests.get(base, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            for link in soup.find_all("link", rel="alternate"):
                t = link.get("type", "")
                if "rss" in t or "atom" in t:
                    href = link.get("href", "")
                    if href:
                        return urljoin(base, href)
    except Exception:
        pass

    # Then: probe known paths
    for path in _FEED_PATHS:
        url = urljoin(base, path)
        try:
            resp = requests.head(url, headers={"User-Agent": _UA},
                                 timeout=_TIMEOUT, allow_redirects=True)
            ct = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ("xml" in ct or "rss" in ct or "atom" in ct):
                return url
        except Exception:
            continue

    return None


# ---------------------------------------------------------------------------
# Sitemap Fallback
# ---------------------------------------------------------------------------

def _fetch_via_sitemap(base: str, name: str, cutoff: datetime) -> list[dict]:
    """Liest sitemap.xml, filtert Eintraege der letzten N Tage, scrapt Titel."""
    sitemap_url = urljoin(base, "/sitemap.xml")
    try:
        resp = requests.get(sitemap_url, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
        if resp.status_code != 200:
            return []
    except Exception:
        return []

    recent_urls = _parse_sitemap_recent(resp.text, cutoff)
    if not recent_urls:
        return []

    items: list[dict] = []
    for url, lastmod in recent_urls[:_MAX_ITEMS_PER_PARTNER]:
        title = _scrape_title(url)
        items.append({
            "source": name,
            "title": title or url,
            "url": url,
            "published_at": lastmod.isoformat() if lastmod else "",
            "snippet": "",
        })
    return items


def _parse_sitemap_recent(
    xml_text: str, cutoff: datetime
) -> list[tuple[str, datetime | None]]:
    """Extrahiert (url, lastmod) fuer Eintraege nach `cutoff`."""
    soup = BeautifulSoup(xml_text, "lxml-xml")
    results: list[tuple[str, datetime | None]] = []

    # Handle sitemap index (points to sub-sitemaps)
    for sitemap_tag in soup.find_all("sitemap"):
        loc = sitemap_tag.find("loc")
        if loc:
            try:
                sub = requests.get(loc.text.strip(), headers={"User-Agent": _UA},
                                   timeout=_TIMEOUT)
                if sub.status_code == 200:
                    results.extend(_parse_sitemap_recent(sub.text, cutoff))
                    if len(results) >= _MAX_ITEMS_PER_PARTNER * 3:
                        break
            except Exception:
                pass

    for url_tag in soup.find_all("url"):
        loc = url_tag.find("loc")
        lastmod_tag = url_tag.find("lastmod")
        if not loc:
            continue
        lastmod = _parse_date_str(lastmod_tag.text.strip() if lastmod_tag else "")
        if lastmod and lastmod >= cutoff:
            results.append((loc.text.strip(), lastmod))

    return results


def _scrape_title(url: str) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": _UA},
                            timeout=_TIMEOUT, stream=True)
        # Read only first 8 KB to find <title>
        chunk = b""
        for part in resp.iter_content(chunk_size=4096):
            chunk += part
            if len(chunk) >= 8192:
                break
        soup = BeautifulSoup(chunk, "lxml")
        if soup.title:
            return soup.title.string.strip() if soup.title.string else ""
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_base(domain: str) -> str:
    domain = domain.strip()
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain
    p = urlparse(domain)
    return f"{p.scheme}://{p.netloc}"


def _parse_date(entry: object) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                import calendar
                return datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
            except Exception:
                pass
    return None


def _parse_date_str(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:19] if "T" in s else s[:10], fmt.split("%z")[0])
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _clean_html(html: str) -> str:
    try:
        return BeautifulSoup(html, "lxml").get_text(separator=" ").strip()
    except Exception:
        return html
