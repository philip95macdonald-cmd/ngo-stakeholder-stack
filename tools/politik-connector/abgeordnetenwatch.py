"""
Abgeordnetenwatch.de API v2 Adapter.

API-Doku: https://www.abgeordnetenwatch.de/api
Lizenz Daten: ODbL (Open Database License)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# Repo-Root + Geteilte Module aufnehmen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.http_client import Client  # noqa: E402
from _shared.csv_schema import StakeholderRow  # noqa: E402
from _shared.logging_setup import get_logger  # noqa: E402

log = get_logger("politik-connector.abgeordnetenwatch")

API_BASE = "https://www.abgeordnetenwatch.de/api/v2"
PAGER_LIMIT = 100


@dataclass
class Politician:
    parliament_id: int
    first_name: str
    last_name: str
    party: str
    parliament: str             # z.B. "Bundestag" oder "Landtag Baden-Wuerttemberg"
    email: str | None = None
    constituency: str | None = None
    committees: list[str] = field(default_factory=list)
    profile_url: str = ""

    def to_stakeholder_row(self) -> StakeholderRow:
        confidence = 1.0 if self.email else 0.6
        slug_party = self.party.lower().replace(" ", "-").replace("/", "-")
        slug_parl = self.parliament.lower().replace(" ", "-").replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
        tags = [
            "stakeholder:politiker",
            f"party:{slug_party}",
            f"parliament:{slug_parl}",
        ]
        return StakeholderRow(
            email=(self.email or "").strip().lower(),
            first_name=self.first_name,
            last_name=self.last_name,
            organisation=self.parliament,
            role="MdB" if self.parliament == "Bundestag" else "Abgeordnete:r",
            source_url=self.profile_url,
            confidence=confidence,
            tags=tags,
            custom_fields={
                "PARLIAMENT_ID": self.parliament_id,
                "PARTY": self.party,
                "PARLIAMENT": self.parliament,
                "CONSTITUENCY": self.constituency or "",
                "COMMITTEES": "|".join(self.committees),
            },
        )


def list_parliaments(client: Client | None = None) -> list[dict]:
    """Liefert die Liste aller Parlament-Perioden mit IDs."""
    client = client or Client()
    url = f"{API_BASE}/parliaments"
    resp = client.get_json(url, params={"pager_limit": 100})
    return resp.get("data", [])


def fetch_active_mandates(parliament_period_id: int, client: Client | None = None) -> Iterator[Politician]:
    """
    Yields Politicians mit aktivem Mandat fuer die angegebene Parlament-Periode.

    parliament_period_id ist NICHT die Parlament-ID, sondern die Wahlperioden-ID.
    Beispiel: Bundestag 20. WP hat parliament_period_id=128 (Stand 2026,
    bitte via list_parliaments() verifizieren).
    """
    client = client or Client(rate_limit_seconds=0.6)  # Abgeordnetenwatch erlaubt 100/min
    page = 0
    seen = 0
    while True:
        params = {
            "parliament_period[entity.id]": parliament_period_id,
            "type": "mandate",
            "range_end": "null",   # nur aktuell laufende Mandate
            "page": page,
            "pager_limit": PAGER_LIMIT,
            "related_data": "politician,electoral_data,committee_memberships",
        }
        data = client.get_json(f"{API_BASE}/candidacies-mandates", params=params)
        rows = data.get("data", [])
        if not rows:
            log.info("Fertig nach %d Mandaten (Page %d)", seen, page)
            break
        for entry in rows:
            seen += 1
            politician = entry.get("politician") or {}
            party_obj = politician.get("party") or {}
            electoral = entry.get("electoral_data") or {}
            constituency = (electoral.get("constituency") or {}).get("label")
            committees = [
                (cm.get("committee") or {}).get("label", "")
                for cm in entry.get("committee_memberships") or []
            ]
            yield Politician(
                parliament_id=politician.get("id", 0),
                first_name=politician.get("first_name", ""),
                last_name=politician.get("last_name", ""),
                party=party_obj.get("label", "") if isinstance(party_obj, dict) else "",
                parliament=(entry.get("parliament_period") or {}).get("parliament", {}).get("label", ""),
                email=politician.get("email") or None,
                constituency=constituency,
                committees=[c for c in committees if c],
                profile_url=politician.get("abgeordnetenwatch_url", ""),
            )
        page += 1
