"""Tests fuer den Page-Discoverer."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_discoverer import discover_pages, _normalise_base


def _make_client(status_map: dict[str, int] | None = None) -> MagicMock:
    """Erstellt einen Mock-Client der bestimmte Status-Codes zurueckgibt."""
    status_map = status_map or {}

    def _get(url: str, **kwargs: object) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_map.get(url, 404)
        resp.text = ""
        return resp

    client = MagicMock()
    client.get.side_effect = _get
    return client


class TestNormaliseBase:
    def test_no_scheme(self):
        assert _normalise_base("spiegel.de") == "https://spiegel.de"

    def test_https(self):
        assert _normalise_base("https://spiegel.de/presse") == "https://spiegel.de"

    def test_trailing_slash(self):
        assert _normalise_base("https://spiegel.de/") == "https://spiegel.de"


class TestDiscoverPages:
    def test_finds_presse_path(self):
        client = _make_client({"https://beispiel.de/presse": 200})
        pages = discover_pages("beispiel.de", client)
        assert "https://beispiel.de/presse" in pages

    def test_finds_impressum_path(self):
        client = _make_client({"https://beispiel.de/impressum": 200})
        pages = discover_pages("beispiel.de", client)
        assert "https://beispiel.de/impressum" in pages

    def test_max_pages_respected(self):
        # All paths return 200
        client = _make_client({f"https://beispiel.de{p}": 200
                                for p in ["/presse", "/impressum", "/kontakt",
                                          "/redaktion", "/about/press"]})
        pages = discover_pages("beispiel.de", client, max_pages=3)
        assert len(pages) <= 3

    def test_empty_when_no_contact_pages(self):
        client = _make_client({})
        pages = discover_pages("ghost-site.de", client)
        assert pages == []

    def test_connection_error_handled(self):
        client = MagicMock()
        client.get.side_effect = ConnectionError("timeout")
        pages = discover_pages("offline.de", client)
        assert pages == []
