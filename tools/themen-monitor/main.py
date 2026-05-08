"""
themen-monitor — taeglicher Themen-, Allianz-, Politik-, Foerder- und Krisenreport.

Skeleton mit Stubs fuer alle Quellen. Aktiviert pro Quelle ueber configs/sources.yaml.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

import analyzer  # noqa: E402
import crisis_detector  # noqa: E402

log = get_logger("themen-monitor")


def _collect_items(mock: bool) -> list[dict]:
    """Sammelt Items aus allen aktiven Quellen."""
    items: list[dict] = []

    # Google News
    if get("themen_monitor.google_news.keywords"):
        try:
            from sources import google_news
            items.extend(google_news.fetch(mock=mock))
        except Exception as e:
            log.warning("google_news fehlgeschlagen: %s", e)

    # Topic Media via RSS
    if get("themen_monitor.topic_media"):
        try:
            from sources import topic_media_rss
            items.extend(topic_media_rss.fetch(mock=mock))
        except Exception as e:
            log.warning("topic_media_rss fehlgeschlagen: %s", e)

    # Allianzen
    if get("themen_monitor.alliance_partners"):
        try:
            from sources import alliances
            items.extend(alliances.fetch(mock=mock))
        except Exception as e:
            log.warning("alliances fehlgeschlagen: %s", e)

    # Reddit
    if get("themen_monitor.social.reddit_subreddits"):
        try:
            from sources import reddit
            items.extend(reddit.fetch(mock=mock))
        except Exception as e:
            log.warning("reddit fehlgeschlagen: %s", e)

    # Twitter (nur wenn Bearer-Token vorhanden)
    if get("themen_monitor.social.twitter_keywords"):
        try:
            from sources import twitter
            items.extend(twitter.fetch(mock=mock))
        except Exception as e:
            log.warning("twitter fehlgeschlagen: %s", e)

    log.info("Insgesamt %d Items aus allen Quellen gesammelt.", len(items))
    return items


@click.command()
@click.option("--mock/--live", default=True, help="Mock-Modus oder echte API-Calls.")
@click.option("--report-only/--send-mail", default=True, help="HTML-Report nur lokal speichern.")
@click.option("--crisis-only", is_flag=True, help="Nur Krisen-Detektor laufen lassen.")
def cli(mock: bool, report_only: bool, crisis_only: bool) -> None:
    items = _collect_items(mock=mock)

    # Krisen-Check ist immer Pflicht
    alerts = crisis_detector.check(items)
    if alerts:
        log.warning("KRISEN-ALERTS: %s", alerts)
        if not report_only:
            crisis_detector.send_alerts(alerts)

    if crisis_only:
        return

    # Normale Sentiment-Analyse + Report
    analyzed = analyzer.analyze_batch(items)
    out_dir = Path(__file__).resolve().parents[2] / "output" / "themen-monitor"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"report-{date.today().isoformat()}.html"
    analyzer.write_html_report(analyzed, alerts, report_path)
    log.info("✓ Report geschrieben: %s", report_path)

    if not report_only:
        analyzer.send_report_mail(report_path)


if __name__ == "__main__":
    cli()
