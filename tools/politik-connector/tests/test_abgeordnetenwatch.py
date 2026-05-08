"""
Tests fuer den Abgeordnetenwatch-Adapter.

Bewusst keine echten Live-Calls — Mocks zeigen, wie die API-Antworten
geparst werden.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# politik-connector und _shared importierbar machen
HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))   # politik-connector/
sys.path.insert(0, str(HERE.parents[2]))   # tools/

import abgeordnetenwatch as aw  # noqa: E402
from _shared.csv_schema import StakeholderRow  # noqa: E402


def _client_with(payload: dict) -> MagicMock:
    """Bauen eines Client-Mocks, das bei get_json() das Payload zurueckgibt."""
    client = MagicMock()
    client.get_json.return_value = payload
    return client


def test_politician_to_stakeholder_row_with_email() -> None:
    p = aw.Politician(
        parliament_id=12345,
        first_name="Anna",
        last_name="Beispiel",
        party="Bündnis 90/Die Grünen",
        parliament="Bundestag",
        email="anna@beispiel.de",
        constituency="Karlsruhe",
        committees=["Ausschuss für Umwelt", "Ausschuss für Verkehr"],
        profile_url="https://www.abgeordnetenwatch.de/profile/anna-beispiel",
    )
    row = p.to_stakeholder_row()
    assert isinstance(row, StakeholderRow)
    assert row.email == "anna@beispiel.de"
    assert row.organisation == "Bundestag"
    assert row.role == "MdB"
    assert row.confidence == 1.0
    assert "stakeholder:politiker" in row.tags
    assert any(t.startswith("party:") for t in row.tags)
    assert row.custom_fields["PARLIAMENT_ID"] == 12345
    assert row.custom_fields["CONSTITUENCY"] == "Karlsruhe"
    assert "Ausschuss für Umwelt" in row.custom_fields["COMMITTEES"]


def test_politician_without_email_has_lower_confidence() -> None:
    p = aw.Politician(
        parliament_id=11,
        first_name="Bert",
        last_name="Beispielo",
        party="SPD",
        parliament="Landtag NRW",
    )
    row = p.to_stakeholder_row()
    assert row.confidence == 0.6
    assert row.email == ""


def test_role_is_mdb_only_for_bundestag() -> None:
    p_bundestag = aw.Politician(parliament_id=1, first_name="A", last_name="B", party="X", parliament="Bundestag", email="x@y.de")
    p_landtag = aw.Politician(parliament_id=2, first_name="C", last_name="D", party="X", parliament="Landtag BW", email="x@y.de")
    assert p_bundestag.to_stakeholder_row().role == "MdB"
    assert p_landtag.to_stakeholder_row().role == "Abgeordnete:r"


def test_fetch_active_mandates_pages_until_empty() -> None:
    payload_first = {
        "data": [
            {
                "politician": {"id": 1, "first_name": "A", "last_name": "B", "email": "a@b.de", "abgeordnetenwatch_url": "u1"},
                "parliament_period": {"parliament": {"label": "Bundestag"}},
                "electoral_data": {"constituency": {"label": "Hamburg-Mitte"}},
                "committee_memberships": [{"committee": {"label": "Innen"}}],
            }
        ]
    }
    payload_empty = {"data": []}

    client = MagicMock()
    client.get_json.side_effect = [payload_first, payload_empty]

    results = list(aw.fetch_active_mandates(parliament_period_id=128, client=client))
    assert len(results) == 1
    assert results[0].first_name == "A"
    assert results[0].constituency == "Hamburg-Mitte"
    assert "Innen" in results[0].committees


def test_fetch_handles_missing_optional_fields() -> None:
    payload = {
        "data": [
            {
                "politician": {"id": 99, "first_name": "X", "last_name": "Y"},
                "parliament_period": {"parliament": {"label": "Bundestag"}},
            }
        ]
    }
    client = MagicMock()
    client.get_json.side_effect = [payload, {"data": []}]
    results = list(aw.fetch_active_mandates(128, client=client))
    assert len(results) == 1
    assert results[0].email is None
    assert results[0].constituency is None
    assert results[0].committees == []
