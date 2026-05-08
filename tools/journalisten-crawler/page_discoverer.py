"""
Entdeckt relevante Kontakt-Seiten innerhalb einer Domain.

Strategie:
  1. Prueft Standard-Pfade (/impressum, /presse, /kontakt, ...)
  2. Durchsucht die Homepage nach Links mit Presse/Kontakt-Keywords
  3. Gibt eine geordnete Liste von URLs zurueck (hoehere Relevanz zuerst)

Maximal _MAX_PAGES Seiten pro Domain, um Crawl-Eskalation zu verhindern.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_MAX_PAGES = 8

# High-priority paths tried first, in order
_PRIORITY_PATHS = [
    "/presse",
    "/pressestelle",
    "/presse-kontakt",
    "/presse/kontakt",
    "/redaktion",
    "/redaktion/kontakt",
    "/impressum",
    "/kontakt",
    "/about/press",
    "/about/contact",
    "/contact",
    "/press",
    "/newsroom",
    "/media",
    "/ueber-uns/presse",
    "/ueber-uns/kontakt",
]

_LINK_KEYWORDS = [
    "presse", "press", "pressestelle", "pressekontakt", "redaktion",
    "kontakt", "contact", "impressum", "imprint", "editorial",
    "ansprechpartner", "team", "about", "ueber-uns",
]


def discover_pages(
    domain: str,
    client: object,  # _shared.http_client.Client
    max_pages: int = _MAX_PAGES,
) -> list[str]:
    """
    Liefert eine Liste von URLs innerhalb von `domain`, die wahrscheinlich
    Journalist:innen-Kontaktdaten enthalten. Sortiert nach Relevanz.
    """
    base = _normalise_base(domain)
    found: list[str] = []
    seen: set[str] = set()

    # 1. Try priority paths
    for path in _PRIORITY_PATHS:
        if len(found) >= max_pages:
            break
        url = urljoin(base, path)
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = client.get(url, allow_redirects=True)  # type: ignore[attr-defined]
            if resp.status_code == 200:
                log.debug("Found: %s", url)
                found.append(url)
        except Exception as exc:
            log.debug("HEAD %s failed: %s", url, exc)

    # 2. Scan homepage for links
    if len(found) < max_pages:
        homepage_links = _links_from_homepage(base, client, seen)
        for url in homepage_links:
            if len(found) >= max_pages:
                break
            if url not in seen:
                seen.add(url)
                found.append(url)

    return found


def _normalise_base(domain: str) -> str:
    domain = domain.strip()
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain
    parsed = urlparse(domain)
    return f"{parsed.scheme}://{parsed.netloc}"


def _links_from_homepage(
    base: str, client: object, seen: set[str]
) -> list[str]:
    try:
        resp = client.get(base)  # type: ignore[attr-defined]
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        candidates: list[tuple[int, str]] = []
        netloc = urlparse(base).netloc

        for tag in soup.find_all("a", href=True):
            href: str = tag["href"]
            full_url = urljoin(base, href)
            if urlparse(full_url).netloc != netloc:
                continue
            if full_url in seen:
                continue
            text = (tag.get_text() + " " + href).lower()
            score = sum(1 for kw in _LINK_KEYWORDS if kw in text)
            if score > 0:
                candidates.append((score, full_url))

        # Sort by relevance score, highest first
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [url for _, url in candidates]
    except Exception as exc:
        log.debug("Homepage scan failed for %s: %s", base, exc)
        return []
