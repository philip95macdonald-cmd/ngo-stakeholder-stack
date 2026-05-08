"""
Publisher-Group-Deduplication.

Mehrere Marken eines Verlags (z.B. FAZ + FAZ.NET + F.A.S.) werden
als Gruppe behandelt und auf eine kanonische Domain gemappt.
So landen keine Duplikate aus dem gleichen Verlag im Verteiler.

Die Gruppen kommen aus sources.yaml -> publisher_groups.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402

log = logging.getLogger(__name__)


class PublisherGroups:
    def __init__(self) -> None:
        raw: list[dict] = get("journalisten.publisher_groups", default=[])
        # Build lookup: any member domain -> canonical domain
        self._map: dict[str, str] = {}
        for group in raw:
            canonical = group.get("canonical", "")
            members = group.get("members", [])
            for m in members:
                self._map[_strip(m)] = _strip(canonical)
            if canonical:
                self._map[_strip(canonical)] = _strip(canonical)

    def canonical(self, domain: str) -> str:
        """Gibt die kanonische Domain fuer `domain` zurueck (oder domain selbst)."""
        return self._map.get(_strip(domain), _strip(domain))

    def deduplicate(self, domains: list[str]) -> list[str]:
        """Entfernt Duplikate aus einer Domain-Liste (behaelt kanonische Domain)."""
        seen_canonical: set[str] = set()
        result: list[str] = []
        for d in domains:
            c = self.canonical(d)
            if c not in seen_canonical:
                seen_canonical.add(c)
                result.append(d)
        return result


def _strip(domain: str) -> str:
    return domain.lower().strip().removeprefix("www.").strip("/")
