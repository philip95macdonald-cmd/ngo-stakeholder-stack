"""
journalisten-crawler — CLI-Entrypoint.

Crawlt Medien-Domains und extrahiert Journalist:innen-Kontaktdaten
in das einheitliche Stakeholder-CSV-Schema.

Usage:
  python main.py crawl [--resume] [--dry-run] [--output PATH]
  python main.py list-domains
  python main.py smoke-test
  python main.py reset-state
"""

from __future__ import annotations

import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click

# Resolve _shared from parent tools/ directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402
from _shared.csv_schema import StakeholderRow, write_csv  # noqa: E402
from _shared.http_client import Client  # noqa: E402
from _shared.logging_setup import setup as setup_logging  # noqa: E402

from config_loader import load_config  # noqa: E402
from crawl_state import CrawlState  # noqa: E402
from ner_extractor import extract_contacts  # noqa: E402
from page_discoverer import discover_pages  # noqa: E402
from playwright_client import is_available as playwright_available  # noqa: E402
from playwright_client import render_page  # noqa: E402
from publisher_groups import PublisherGroups  # noqa: E402
from robots_checker import RobotsChecker  # noqa: E402

log = logging.getLogger("journalisten-crawler")

_DEFAULT_OUTPUT = Path(__file__).resolve().parents[3] / "output" / "journalisten" / "contacts.csv"
_DEFAULT_STATE = Path(__file__).resolve().parents[3] / "output" / "journalisten" / ".crawl_state.json"

_WORKERS = 5  # parallel domain threads


@click.group()
@click.option("--debug", is_flag=True, help="Debug-Logging aktivieren")
def cli(debug: bool) -> None:
    setup_logging(level="DEBUG" if debug else "INFO")


@cli.command()
@click.option("--resume", is_flag=True, default=False, help="Crawl fortsetzen (State laden)")
@click.option("--dry-run", is_flag=True, default=False, help="Kein CSV schreiben, nur zaehlen")
@click.option("--output", default=str(_DEFAULT_OUTPUT), show_default=True, help="Output-CSV-Pfad")
@click.option("--state-file", default=str(_DEFAULT_STATE), show_default=True, help="State-JSON-Pfad")
@click.option("--min-confidence", default=0.4, show_default=True, type=float,
              help="Minimaler Confidence-Score (0–1)")
def crawl(resume: bool, dry_run: bool, output: str, state_file: str, min_confidence: float) -> None:
    """Crawlt alle konfigurierten Domains und schreibt contacts.csv."""
    cfg = load_config()
    pg = PublisherGroups()
    state = CrawlState(state_file)

    domains_de = cfg.domains_de or []
    domains_eu = cfg.domains_eu or []
    all_domains = pg.deduplicate(domains_de + domains_eu)

    remaining = [d for d in all_domains if not state.is_done(d)] if resume else all_domains
    if not remaining:
        click.echo("Alle Domains bereits gecrawlt. Mit --resume=False neu starten.")
        return

    click.echo(
        f"Crawle {len(remaining)} Domain(s) "
        f"({'Resume' if resume else 'Neu'}, "
        f"{_WORKERS} parallel, "
        f"min_confidence={min_confidence})"
    )
    if playwright_available():
        click.echo("  Playwright verfuegbar — JS-Render-Pass aktiv")

    http = Client(
        user_agent=cfg.user_agent,
        rate_limit_seconds=cfg.rate_limit_seconds,
    )
    robots = RobotsChecker(user_agent=cfg.user_agent, default_crawl_delay=cfg.rate_limit_seconds)
    js_domains = set(get("journalisten.js_domains", default=[]))

    all_rows: list[StakeholderRow] = []

    def _crawl_domain(domain: str) -> list[StakeholderRow]:
        log.info("Starte Domain: %s", domain)
        rows: list[StakeholderRow] = []
        try:
            pages = discover_pages(domain, http)
            for url in pages:
                if not robots.is_allowed(url):
                    log.info("robots.txt: %s verboten", url)
                    continue
                html = _fetch_html(url, domain, http, js_domains)
                if not html:
                    continue
                contacts = extract_contacts(
                    html, source_url=url, domain=domain, cap=cfg.cap_per_domain
                )
                for c in contacts:
                    conf = c.confidence(domain)
                    if conf < min_confidence:
                        continue
                    rows.append(
                        StakeholderRow(
                            email=c.email,
                            first_name=c.first_name,
                            last_name=c.last_name,
                            organisation=domain,
                            role=c.role,
                            source_url=c.source_url,
                            confidence=conf,
                            tags=["stakeholder:journalist", f"region:{_guess_region(domain)}"],
                        )
                    )
        except Exception as exc:
            log.warning("Domain %s fehlgeschlagen: %s", domain, exc)
            state.mark_error(domain, str(exc))
        return rows

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        futures = {pool.submit(_crawl_domain, d): d for d in remaining}
        for future in as_completed(futures):
            domain = futures[future]
            rows = future.result()
            all_rows.extend(rows)
            state.mark_done(domain)
            click.echo(f"  {domain}: {len(rows)} Kontakt(e)")

    if dry_run:
        click.echo(f"[Dry-run] Wuerde {len(all_rows)} Zeilen schreiben nach: {output}")
    else:
        n = write_csv(all_rows, output)
        click.echo(f"Fertig: {n} Kontakte geschrieben nach {output}")
        click.echo(
            f"State: {state.done_count()} Domains OK, {state.error_count()} mit Fehler"
        )


@cli.command("list-domains")
def list_domains_cmd() -> None:
    """Zeigt alle konfigurierten Domains."""
    cfg = load_config()
    pg = PublisherGroups()
    all_domains = pg.deduplicate((cfg.domains_de or []) + (cfg.domains_eu or []))
    click.echo(f"{len(all_domains)} Domain(s) konfiguriert:\n")
    for d in all_domains:
        canonical = pg.canonical(d)
        marker = f"  → {canonical}" if canonical != d else ""
        click.echo(f"  {d}{marker}")


@cli.command("reset-state")
@click.option("--state-file", default=str(_DEFAULT_STATE), show_default=True)
@click.confirmation_option(prompt="State-Datei wirklich loeschen?")
def reset_state_cmd(state_file: str) -> None:
    """Loescht den gespeicherten Crawl-State (Neucrawl aller Domains)."""
    CrawlState(state_file).reset()
    click.echo("State geloescht.")


@cli.command("smoke-test")
def smoke_test_cmd() -> None:
    """Prueft ob alle Abhaengigkeiten und Configs vorhanden sind."""
    errors: list[str] = []

    try:
        cfg = load_config()
        n = len((cfg.domains_de or []) + (cfg.domains_eu or []))
        click.echo(f"  config-loader        OK ({n} Domains geladen)")
    except Exception as exc:
        errors.append(f"config-loader: {exc}")
        click.echo(f"  config-loader        FAIL {exc}")

    try:
        from ner_extractor import extract_contacts  # noqa: F401
        result = extract_contacts("<html><body>Max Mustermann, max@beispiel.de</body></html>",
                                  source_url="test", domain="beispiel.de")
        click.echo(f"  ner-extractor        OK ({len(result)} Kontakt(e) im Test)")
    except Exception as exc:
        errors.append(f"ner-extractor: {exc}")
        click.echo(f"  ner-extractor        FAIL {exc}")

    try:
        from robots_checker import RobotsChecker  # noqa: F401
        click.echo("  robots-checker       OK")
    except Exception as exc:
        errors.append(f"robots-checker: {exc}")
        click.echo(f"  robots-checker       FAIL {exc}")

    if playwright_available():
        click.echo("  playwright           OK (optional, verfuegbar)")
    else:
        click.echo("  playwright           -- (optional, nicht installiert)")

    if errors:
        click.echo(f"\n{len(errors)} Fehler:")
        for e in errors:
            click.echo(f"  FAIL {e}")
        sys.exit(1)
    else:
        click.echo("\n[smoke] journalisten-crawler OK")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_html(url: str, domain: str, http: Client, js_domains: set[str]) -> str | None:
    use_js = domain in js_domains or domain.removeprefix("www.") in js_domains
    if use_js:
        html = render_page(url)
        if html:
            return html
    try:
        resp = http.get(url)
        if resp.status_code == 200:
            return resp.text
    except Exception as exc:
        log.debug("Fetch failed %s: %s", url, exc)
    return None


def _guess_region(domain: str) -> str:
    tld = domain.rsplit(".", 1)[-1].lower()
    eu_tlds = {"de", "at", "ch", "fr", "nl", "be", "es", "it", "pl", "eu"}
    return "de" if tld == "de" else ("eu" if tld in eu_tlds else "intl")


if __name__ == "__main__":
    cli()
