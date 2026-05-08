"""
CLI fuer den politik-connector.

Beispiele:
  python main.py list-parliaments
  python main.py fetch --parliament bundestag --output ../../output/politiker/bundestag.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402
from _shared.csv_schema import StakeholderRow, write_csv  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

import abgeordnetenwatch as aw  # noqa: E402

log = get_logger("politik-connector")


def _parliament_id_for(label: str) -> int | None:
    """Sucht in configs/sources.yaml die parliament_period_id zu einem Label."""
    parliaments = get("politik.parliaments", default=[])
    for p in parliaments:
        if p.get("label", "").lower().replace(" ", "-") == label.lower():
            return int(p["id"])
    return None


@click.group()
def cli() -> None:
    """politik-connector — Stakeholder-Daten aus Parlamenten."""


@cli.command("list-parliaments")
def list_parliaments() -> None:
    """Listet die Parlament-Perioden, die Abgeordnetenwatch kennt."""
    rows = aw.list_parliaments()
    print(f"{'ID':>5}  {'Label':<40}  {'Type':<14}  {'Active':<6}")
    print("-" * 80)
    for r in rows:
        active = "—" if r.get("end_date_period") else "active"
        print(f"{r.get('id'):>5}  {r.get('label', '')[:40]:<40}  {r.get('type', ''):<14}  {active:<6}")


@cli.command("fetch")
@click.option(
    "--parliament", "-p",
    multiple=True, required=True,
    help="Slug des Parlaments aus configs/sources.yaml (z.B. 'bundestag').",
)
@click.option(
    "--output", "-o",
    default="../../output/politiker/output.csv",
    help="Output-CSV-Pfad relativ zum cwd.",
)
@click.option("--include-without-email/--exclude-without-email", default=False)
def fetch(parliament: tuple[str, ...], output: str, include_without_email: bool) -> None:
    """Holt Mandate aus den angegebenen Parlamenten und schreibt sie als CSV."""
    rows: list[StakeholderRow] = []
    for slug in parliament:
        pid = _parliament_id_for(slug)
        if pid is None:
            log.error("Parlament-Slug '%s' nicht in configs/sources.yaml gefunden", slug)
            continue
        log.info("Hole Mandate aus Parliament-Period-ID %d (%s)", pid, slug)
        for politician in aw.fetch_active_mandates(pid):
            if not politician.email and not include_without_email:
                continue
            rows.append(politician.to_stakeholder_row())

    n = write_csv(rows, output)
    log.info("✓ %d Zeilen nach %s geschrieben", n, output)


if __name__ == "__main__":
    cli()
