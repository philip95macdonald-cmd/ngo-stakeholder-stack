"""
brevo-sync — synchronisiert ein Stakeholder-CSV in eine Brevo-Liste.

Skeleton mit funktionsfaehigen list-lists / list-fields / ensure-fields
Befehlen. Der eigentliche Sync-Pfad ist als deutlich strukturiertes
Skelett angelegt — Tests + zusaetzliche Edge-Cases (Bulk-Updates,
Suppression-Diff, Tag-Removal) sind Aufgabe der naechsten Iteration.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import click
import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

load_dotenv()
log = get_logger("brevo-sync")

API_BASE = "https://api.brevo.com/v3"


def _key() -> str:
    k = os.environ.get("BREVO_API_KEY")
    if not k:
        click.echo("✗ BREVO_API_KEY nicht in .env gesetzt.", err=True)
        sys.exit(2)
    return k


def _headers() -> dict[str, str]:
    return {
        "api-key": _key(),
        "accept": "application/json",
        "content-type": "application/json",
    }


def _api_get(path: str, **params: Any) -> dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", headers=_headers(), json=payload, timeout=30)
    if r.status_code >= 400:
        log.error("Brevo POST %s → %d: %s", path, r.status_code, r.text)
        r.raise_for_status()
    return r.json() if r.content else {}


def _api_put(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    r = requests.put(f"{API_BASE}{path}", headers=_headers(), json=payload, timeout=30)
    if r.status_code >= 400 and r.status_code != 404:
        log.error("Brevo PUT %s → %d: %s", path, r.status_code, r.text)
        r.raise_for_status()
    return r.json() if r.content else {}


@click.group()
def cli() -> None:
    """brevo-sync — Stakeholder-CSV → Brevo-Liste."""


@cli.command("list-lists")
def list_lists() -> None:
    """Listet alle Brevo-Listen mit ID + Anzahl Kontakte."""
    data = _api_get("/contacts/lists", limit=50, offset=0)
    print(f"{'ID':>4}  {'Total':>6}  Name")
    print("-" * 60)
    for lst in data.get("lists", []):
        print(f"{lst['id']:>4}  {lst.get('totalSubscribers', 0):>6}  {lst['name']}")
    print(f"\n{data.get('count', 0)} Listen")


@cli.command("list-fields")
def list_fields() -> None:
    """Listet alle Custom-Fields, die im Brevo-Account konfiguriert sind."""
    data = _api_get("/contacts/attributes")
    for attr in data.get("attributes", []):
        if attr.get("category") == "normal":
            print(f"  {attr['name']:<24} {attr.get('type', '?')}")


@cli.command("ensure-fields")
def ensure_fields() -> None:
    """Legt fehlende Custom-Fields aus configs/brevo.yaml in Brevo an."""
    target = get("brevo.custom_fields", default=[])
    existing = {a["name"] for a in _api_get("/contacts/attributes").get("attributes", [])}
    created = 0
    for field in target:
        name = field["name"]
        if name in existing:
            continue
        _api_post(
            f"/contacts/attributes/normal/{name}",
            {"type": field.get("type", "text")},
        )
        log.info("✓ Field %s angelegt", name)
        created += 1
    click.echo(f"{created} neue Custom-Fields, {len(existing)} existieren bereits.")


@cli.command("sync")
@click.argument("csv_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--list-id", type=int, required=True)
@click.option("--dry-run/--live", default=True)
def sync(csv_path: str, list_id: int, dry_run: bool) -> None:
    """Sync eines Stakeholder-CSV in eine Brevo-Liste."""
    with open(csv_path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    log.info("Sync %d Zeilen aus %s nach Liste %d (%s)",
             len(rows), csv_path, list_id, "DRY-RUN" if dry_run else "LIVE")

    upserted = 0
    for row in rows:
        email = (row.get("email") or "").strip().lower()
        if not email:
            continue
        custom = json.loads(row.get("custom_fields") or "{}")
        tags = [t for t in (row.get("tags") or "").split("|") if t]
        attributes = {
            "FIRSTNAME": row.get("first_name", ""),
            "LASTNAME": row.get("last_name", ""),
            **{k: v for k, v in custom.items() if v not in (None, "")},
        }
        payload = {
            "email": email,
            "attributes": attributes,
            "listIds": [list_id],
            "updateEnabled": True,
            "ext_id": email,
        }
        if dry_run:
            log.debug("DRY: %s → %s", email, json.dumps(payload, ensure_ascii=False)[:120])
            upserted += 1
            continue
        _api_post("/contacts", payload)
        # Tags via separater Endpoint (Brevo-API erlaubt Tags nur ueber attributes —
        # wenn deine Brevo-Instanz "tags" als Custom-Field nutzt, oben in attributes
        # einfach reinpacken).
        upserted += 1

    click.echo(f"✓ {upserted} Kontakte {'simuliert' if dry_run else 'gesynced'} in Liste {list_id}.")


if __name__ == "__main__":
    cli()
