"""
brevo-sync — sync a stakeholder CSV into any supported ESP/CRM.

Set ESP_PROVIDER in .env to switch backends:
  brevo (default) | mailchimp | mailerlite | activecampaign | civicrm
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

load_dotenv()
log = get_logger("brevo-sync")


def _get_adapter():
    provider = os.environ.get("ESP_PROVIDER", "brevo").lower()
    if provider == "brevo":
        from adapters.esp.brevo import BrevoAdapter
        return BrevoAdapter()
    if provider == "mailchimp":
        from adapters.esp.mailchimp import MailchimpAdapter
        return MailchimpAdapter()
    if provider == "mailerlite":
        from adapters.esp.mailerlite import MailerLiteAdapter
        return MailerLiteAdapter()
    if provider == "activecampaign":
        from adapters.esp.activecampaign import ActiveCampaignAdapter
        return ActiveCampaignAdapter()
    if provider == "civicrm":
        from adapters.esp.civicrm import CiviCRMAdapter
        return CiviCRMAdapter()
    click.echo(f"✗ Unknown ESP_PROVIDER: {provider}", err=True)
    sys.exit(2)


@click.group()
def cli() -> None:
    """brevo-sync — Stakeholder-CSV → ESP/CRM."""


@cli.command("list-lists")
def list_lists() -> None:
    """List all available contact lists in the configured ESP."""
    adapter = _get_adapter()
    lists = adapter.list_lists()
    print(f"{'ID':>4}  Name")
    print("-" * 40)
    for lst in lists:
        print(f"{lst.get('id', '?'):>4}  {lst.get('name', '?')}")
    print(f"\n{len(lists)} lists")


@cli.command("list-fields")
def list_fields() -> None:
    """List custom fields configured in the ESP (Brevo only for now)."""
    provider = os.environ.get("ESP_PROVIDER", "brevo").lower()
    if provider != "brevo":
        click.echo("list-fields is currently only supported for Brevo.")
        return
    from adapters.esp.brevo import BrevoAdapter
    adapter = BrevoAdapter()
    data = adapter._get("/contacts/attributes")
    for attr in data.get("attributes", []):
        if attr.get("category") == "normal":
            print(f"  {attr['name']:<24} {attr.get('type', '?')}")


@cli.command("ensure-fields")
def ensure_fields() -> None:
    """Create missing custom fields from configs/brevo.yaml in the ESP."""
    fields = get("brevo.custom_fields", default=[])
    _get_adapter().ensure_fields(fields)
    click.echo(f"ensure-fields done ({len(fields)} fields checked).")


@cli.command("sync")
@click.argument("csv_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--list-id", required=True, help="List/group ID in your ESP")
@click.option("--dry-run/--live", default=True)
def sync(csv_path: str, list_id: str, dry_run: bool) -> None:
    """Sync a stakeholder CSV into the configured ESP."""
    from adapters.esp._interface import Contact

    with open(csv_path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    provider = os.environ.get("ESP_PROVIDER", "brevo")
    log.info("Sync %d rows from %s → list %s via %s (%s)",
             len(rows), csv_path, list_id, provider, "DRY-RUN" if dry_run else "LIVE")

    adapter = _get_adapter()
    upserted = 0

    for row in rows:
        email = (row.get("email") or "").strip().lower()
        if not email:
            continue
        custom = json.loads(row.get("custom_fields") or "{}")
        tags = [t for t in (row.get("tags") or "").split("|") if t]
        contact = Contact(
            email=email,
            first_name=row.get("first_name", ""),
            last_name=row.get("last_name", ""),
            tags=tags,
            custom_fields={k: v for k, v in custom.items() if v not in (None, "")},
        )
        if dry_run:
            log.debug("DRY: %s", email)
            upserted += 1
            continue
        adapter.upsert_contact(contact, list_id)
        upserted += 1

    click.echo(f"✓ {upserted} contacts {'simulated' if dry_run else 'synced'} to list {list_id}.")


if __name__ == "__main__":
    cli()
