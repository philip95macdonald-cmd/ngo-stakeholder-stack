"""Tests fuer Publisher-Group-Deduplication."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from publisher_groups import PublisherGroups, _strip


_MOCK_GROUPS = [
    {"canonical": "faz.net", "members": ["faz.net", "faznet.de", "faz-net.de"]},
    {"canonical": "spiegel.de", "members": ["spiegel.de", "spiegel-online.de"]},
]


class TestStrip:
    def test_removes_www(self):
        assert _strip("www.faz.net") == "faz.net"

    def test_lowercase(self):
        assert _strip("FAZ.NET") == "faz.net"

    def test_trailing_slash(self):
        assert _strip("faz.net/") == "faz.net"


class TestPublisherGroups:
    def _pg(self) -> PublisherGroups:
        with patch(
            "publisher_groups.get",
            return_value=_MOCK_GROUPS,
        ):
            return PublisherGroups()

    def test_canonical_member(self):
        pg = self._pg()
        assert pg.canonical("faz-net.de") == "faz.net"

    def test_canonical_is_self(self):
        pg = self._pg()
        assert pg.canonical("faz.net") == "faz.net"

    def test_unknown_domain_passthrough(self):
        pg = self._pg()
        assert pg.canonical("taz.de") == "taz.de"

    def test_deduplicate_removes_alias(self):
        pg = self._pg()
        domains = ["faz.net", "faz-net.de", "taz.de"]
        deduped = pg.deduplicate(domains)
        # faz.net and faz-net.de are the same publisher
        assert len(deduped) == 2
        assert "taz.de" in deduped

    def test_empty_groups(self):
        with patch("publisher_groups.get", return_value=[]):
            pg = PublisherGroups()
            assert pg.canonical("any.de") == "any.de"
