"""
Sentiment-Analyse + HTML-Report-Builder.

Skeleton — die Sentiment-Berechnung ist bewusst minimal (Keyword-Listen).
Fuer Produktivbetrieb empfohlen: VADER (englisch) + germansentiment
(deutsches BERT-Modell) als Drop-in in analyze_text().
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("themen-monitor.analyzer")


# NGO-relevanter Wortschatz — produktiv durch VADER oder germansentiment ersetzen
POS = {
    "erfolg", "fortschritt", "gewonnen", "erfolgreich", "wirkung", "hilfreich",
    "durchbruch", "einigung", "verabschiedet", "beschlossen", "positiv",
    "unterstützung", "foerderung", "förderung", "meilenstein", "rekord",
    "gerettet", "geschützt", "gesichert", "erreicht", "bewilligt",
    "solidarität", "zusammenhalt", "spende", "ehrenamt", "engagement",
    "nachhaltig", "klimaschutz", "erneuerbar", "transformation",
    "verbesserung", "zunahme", "anstieg", "wachstum",
}
NEG = {
    "krise", "skandal", "scheitert", "kritik", "vorwurf", "betrug",
    "greenwashing", "manipulation", "korruption", "versagen", "blockiert",
    "abgelehnt", "gescheitert", "verloren", "rueckschritt", "rückschritt",
    "katastrophe", "desaster", "anklage", "ermittlung", "insolvenz",
    "missbrauch", "vorwuerfe", "vorwürfe", "falsch", "luege", "lüge",
    "desinformation", "hetze", "angriff", "hass",
}


def analyze_text(text: str) -> float:
    """Liefert ein Sentiment in [-1, 1] basierend auf einer Mini-Wortliste."""
    if not text:
        return 0.0
    tokens = text.lower().split()
    pos = sum(1 for t in tokens if t.strip(".,;:!?-") in POS)
    neg = sum(1 for t in tokens if t.strip(".,;:!?-") in NEG)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def analyze_batch(items: list[dict]) -> list[dict]:
    for it in items:
        it["sentiment"] = analyze_text(f"{it.get('title', '')} {it.get('snippet', '')}")
    return items


def write_html_report(items: list[dict], alerts: list[dict], out_path: Path) -> None:
    """Sehr einfacher HTML-Report. Produktiv mit Jinja-Template ersetzen."""
    parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'>"]
    parts.append("<title>themen-monitor Report</title>")
    parts.append("<style>body{font-family:system-ui;margin:32px;max-width:900px}"
                 "h1,h2{margin-top:32px} .alert{background:#ffe5e5;padding:12px;border-radius:8px}"
                 ".item{padding:12px;border-bottom:1px solid #eee} .pos{color:#2a8} .neg{color:#c33}</style>")
    parts.append("</head><body>")
    parts.append(f"<h1>themen-monitor — Tagesbericht</h1>")

    if alerts:
        parts.append("<div class='alert'><h2>🚨 Krisen-Alerts</h2>")
        for a in alerts:
            parts.append(f"<p>{a}</p>")
        parts.append("</div>")

    by_source: dict[str, list[dict]] = {}
    for it in items:
        by_source.setdefault(it.get("source", "Sonstige"), []).append(it)

    for source, group in sorted(by_source.items()):
        parts.append(f"<h2>{source} ({len(group)})</h2>")
        for it in group:
            sent = it.get("sentiment", 0.0)
            cls = "pos" if sent > 0.1 else "neg" if sent < -0.1 else ""
            parts.append(f"<div class='item'><strong>{it.get('title', '')}</strong>")
            parts.append(f" <a href=\"{it.get('url', '')}\">↗</a>")
            parts.append(f" <span class='{cls}'>(sentiment {sent:+.2f})</span>")
            parts.append(f"<p>{it.get('snippet', '')[:240]}</p></div>")

    parts.append("</body></html>")
    out_path.write_text("".join(parts), encoding="utf-8")


def send_report_mail(report_path: Path) -> None:
    """Sendet den HTML-Report per SMTP. Konfiguration aus .env (SMTP_*)."""
    import os
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import date

    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    from_addr = os.getenv("SMTP_FROM", user)
    to_addr = os.getenv("SMTP_TO", "")

    if not all([host, user, password, to_addr]):
        log.warning(
            "Mail-Versand uebersprungen — SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_TO in .env pruefen."
        )
        return

    html_body = report_path.read_text(encoding="utf-8")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Themen-Monitor — {date.today().isoformat()}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(from_addr, [to_addr], msg.as_string())
        log.info("Report per Mail versandt an %s", to_addr)
    except Exception as exc:
        log.error("Mail-Versand fehlgeschlagen: %s", exc)
