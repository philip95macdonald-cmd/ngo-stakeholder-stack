"""
Persistierter Crawl-State fuer Resumable Crawls.

Speichert, welche Domains bereits gecrawlt wurden, sodass ein
abgebrochener Crawl (Ctrl+C, Netzwerkfehler, etc.) an der
richtigen Stelle fortgesetzt werden kann.

Format: JSON-Datei neben der Output-CSV.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class CrawlState:
    def __init__(self, state_path: str | Path) -> None:
        self.path = Path(state_path)
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                with self.path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                log.info("Resumed crawl state: %d domains done", len(data.get("done", [])))
                return data
            except Exception as exc:
                log.warning("Could not load state file %s: %s — starting fresh", self.path, exc)
        return {"done": [], "errors": {}}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    def mark_done(self, domain: str) -> None:
        if domain not in self._data["done"]:
            self._data["done"].append(domain)
        self.save()

    def mark_error(self, domain: str, error: str) -> None:
        self._data["errors"][domain] = error
        self.save()

    def is_done(self, domain: str) -> bool:
        return domain in self._data["done"]

    def done_count(self) -> int:
        return len(self._data["done"])

    def error_count(self) -> int:
        return len(self._data["errors"])

    def reset(self) -> None:
        self._data = {"done": [], "errors": {}}
        if self.path.exists():
            self.path.unlink()
        log.info("Crawl state reset.")

    @property
    def errors(self) -> dict[str, str]:
        return dict(self._data.get("errors", {}))
