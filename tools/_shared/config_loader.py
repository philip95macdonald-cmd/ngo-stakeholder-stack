"""
Zentrales Config-Loading. Liest die drei YAML-Dateien aus ../../configs/
und mergt sie in ein einheitliches Dict.

Resolution-Reihenfolge fuer Pfade:
  1. NGO_STACK_CONFIG_DIR Env-Var
  2. ../../configs/ relativ zu diesem Modul
  3. /etc/ngo-stack/ (wenn sytemweit installiert — selten)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_CACHE: dict[str, Any] = {}


def _config_dir() -> Path:
    explicit = os.environ.get("NGO_STACK_CONFIG_DIR")
    if explicit:
        return Path(explicit)
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "configs"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        "configs/-Verzeichnis nicht gefunden. NGO_STACK_CONFIG_DIR setzen "
        "oder im Repo-Root von ./configs/ ausfuehren."
    )


def _load_yaml(name: str) -> dict[str, Any]:
    """Laedt configs/<name>.yaml mit Fallback auf configs/<name>.example.yaml."""
    cdir = _config_dir()
    primary = cdir / f"{name}.yaml"
    fallback = cdir / f"{name}.example.yaml"
    path = primary if primary.exists() else fallback
    if not path.exists():
        raise FileNotFoundError(
            f"Weder {primary.name} noch {fallback.name} im configs/-Verzeichnis."
        )
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_config(force_reload: bool = False) -> dict[str, Any]:
    """
    Liefert das gemergete Config-Dict mit Top-Level-Keys:
      - ngo
      - datenschutz
      - lobby
      - output
      - journalisten
      - politik
      - themen_monitor
      - brevo
    """
    if not force_reload and _CACHE:
        return _CACHE

    merged: dict[str, Any] = {}
    merged.update(_load_yaml("ngo"))
    merged.update(_load_yaml("sources"))
    merged.update(_load_yaml("brevo"))

    _CACHE.clear()
    _CACHE.update(merged)
    return merged


def get(path: str, default: Any = None) -> Any:
    """
    Punkt-Notation-Zugriff: get('ngo.brand.tone') oder get('politik.parliaments').
    """
    cfg = load_config()
    cur: Any = cfg
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


if __name__ == "__main__":
    cfg = load_config()
    print("Top-Level Keys:", sorted(cfg.keys()))
    print(f"NGO Name: {get('ngo.name')}")
