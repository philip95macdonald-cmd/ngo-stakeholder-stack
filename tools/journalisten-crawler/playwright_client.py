"""
Optionaler JS-Render-Pass via Playwright.

Wird nur genutzt, wenn `playwright` installiert ist UND die Domain
in der Config als JS-rendered markiert ist (journalisten.js_domains).

Silently no-op wenn Playwright nicht verfuegbar.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def render_page(url: str, timeout_ms: int = 15_000) -> str | None:
    """
    Rendert `url` im Headless-Browser und gibt den HTML-String zurueck.
    Gibt None zurueck wenn Playwright nicht installiert oder der Render scheitert.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        log.debug("Playwright not installed — skipping JS render for %s", url)
        return None

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="ngo-stakeholder-stack-crawler/0.1"
            )
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            html = page.content()
            browser.close()
            log.debug("JS render OK: %s", url)
            return html
    except Exception as exc:
        log.warning("Playwright render failed for %s: %s", url, exc)
        return None


def is_available() -> bool:
    try:
        import playwright  # type: ignore[import-not-found]
        return True
    except ImportError:
        return False
