"""
Krisen-Detektor — Anomalie-Erkennung im Mention-Strom.

Trigger:
  • Volume-Spike: Tagesvolumen > volume_spike_factor x Median der Vortage
  • Sentiment-Drift: Tages-Sentiment > sentiment_drift_zscore Standardabweichungen
                     unter dem 30-Tage-Mittel
  • Hashtag-Cluster: NEU-Hashtags die plotzlich von >5 Accounts gleichzeitig
                     genutzt werden (TODO Phase 3.5)
"""

from __future__ import annotations

import statistics
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.crisis")


def _aggregate_today(items: list[dict]) -> dict:
    """Aggregiert die Items von heute zu (mentions, sentiment_avg)."""
    today_items = [i for i in items if (i.get("published_at") or "")[:10] == date.today().isoformat()]
    if not today_items:
        return {"mentions": 0, "sentiment": 0.0}
    sentiments = [i.get("sentiment", 0.0) for i in today_items]
    return {
        "mentions": len(today_items),
        "sentiment": statistics.fmean(sentiments) if sentiments else 0.0,
    }


def _load_history() -> list[dict]:
    """
    Stub: laed die Tageswerte der letzten N Tage aus Persistenz.
    Persistenz-Backend muss noch entschieden werden — vorgeschlagen:
    SQLite-File unter output/themen-monitor/history.db.

    Aktuell liefert dieser Stub eine kleine synthetische History,
    sodass die Anomalie-Logik testbar bleibt.
    """
    return [
        {"mentions": 5, "sentiment": 0.1},
        {"mentions": 6, "sentiment": 0.05},
        {"mentions": 4, "sentiment": 0.12},
        {"mentions": 7, "sentiment": 0.08},
        {"mentions": 5, "sentiment": 0.0},
        {"mentions": 8, "sentiment": -0.05},
    ]


def check(items: list[dict]) -> list[dict]:
    """Liefert eine (moeglicherweise leere) Liste von Alert-Dicts."""
    cfg = get("themen_monitor.crisis_detector", default={})
    if not cfg.get("enabled", True):
        return []

    today = _aggregate_today(items)
    history = _load_history()
    alerts: list[dict] = []

    # Volume-Spike
    spike_factor = cfg.get("volume_spike_factor", 3.0)
    median_vol = statistics.median([h["mentions"] for h in history]) if history else 0
    if today["mentions"] > spike_factor * max(median_vol, 5):
        alerts.append({
            "type": "volume_spike",
            "today": today["mentions"],
            "median": median_vol,
            "factor": today["mentions"] / max(median_vol, 1),
        })

    # Sentiment-Drift
    drift_z = cfg.get("sentiment_drift_zscore", 1.5)
    if len(history) >= 10:
        mean_s = statistics.fmean(h["sentiment"] for h in history)
        sd_s = statistics.stdev(h["sentiment"] for h in history)
        if sd_s > 0 and (today["sentiment"] - mean_s) / sd_s < -drift_z:
            alerts.append({
                "type": "sentiment_drift",
                "today_sentiment": today["sentiment"],
                "baseline": mean_s,
                "z_score": (today["sentiment"] - mean_s) / sd_s,
            })

    return alerts


def send_alerts(alerts: list[dict]) -> None:
    """Sendet Krisen-Alerts per Mail und/oder Slack-Webhook."""
    import json
    import os
    import smtplib
    from email.mime.text import MIMEText

    for a in alerts:
        log.error("KRISEN-ALERT: %s", a)

    subject = f"KRISEN-ALERT: {len(alerts)} Anomalie(n) erkannt"
    body_lines = [f"Themen-Monitor hat {len(alerts)} Krisen-Indikator(en) ausgeloest:\n"]
    for a in alerts:
        if a["type"] == "volume_spike":
            body_lines.append(
                f"  VOLUME-SPIKE: {a['today']} Mentions heute "
                f"(Faktor {a['factor']:.1f}x ueber Median {a['median']:.0f})"
            )
        elif a["type"] == "sentiment_drift":
            body_lines.append(
                f"  SENTIMENT-DRIFT: {a['today_sentiment']:+.2f} "
                f"(Z-Score {a['z_score']:.1f}, Baseline {a['baseline']:+.2f})"
            )
        else:
            body_lines.append(f"  {a}")
    body_lines.append("\nBitte Lage pruefen.")
    body = "\n".join(body_lines)

    # --- SMTP ---
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    from_addr = os.getenv("SMTP_FROM", user)
    to_addr = os.getenv("SMTP_TO", "")

    if all([host, user, password, to_addr]):
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        try:
            with smtplib.SMTP(host, port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(user, password)
                smtp.sendmail(from_addr, [to_addr], msg.as_string())
            log.info("Krisen-Alert per Mail versandt an %s", to_addr)
        except Exception as exc:
            log.error("Alert-Mail fehlgeschlagen: %s", exc)

    # --- Slack ---
    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    if webhook:
        try:
            import requests
            requests.post(
                webhook,
                json={"text": f":rotating_light: *{subject}*\n```{body}```"},
                timeout=10,
            )
            log.info("Krisen-Alert per Slack versandt")
        except Exception as exc:
            log.error("Slack-Alert fehlgeschlagen: %s", exc)
