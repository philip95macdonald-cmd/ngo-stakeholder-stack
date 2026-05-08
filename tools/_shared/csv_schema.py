"""
Einheitliches CSV-Schema fuer Stakeholder-Kontakte.

Alle Tools (journalisten-crawler, politik-connector, ...) muessen ihre
Outputs in dieses Schema schreiben, damit brevo-sync sie ohne Anpassung
verarbeiten kann.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path


# Pflicht-Spalten in fester Reihenfolge
HEADERS: list[str] = [
    "email",
    "first_name",
    "last_name",
    "organisation",   # Medium fuer Journalisten, Bundestag/Landtag fuer Politiker
    "role",           # Redakteur:in / MdB / Spender:in / ...
    "source_url",
    "confidence",     # 0.0 bis 1.0
    # Stakeholder-Tags als Pipe-separierte Liste
    "tags",           # z.B. "stakeholder:journalist|topic:klimaschutz|region:de"
    # Custom-Fields als JSON-String fuer Flexibilitaet
    "custom_fields",  # z.B. '{"PARLIAMENT_ID": 12345, "PARTY": "Gruene"}'
]


@dataclass
class StakeholderRow:
    email: str
    first_name: str = ""
    last_name: str = ""
    organisation: str = ""
    role: str = ""
    source_url: str = ""
    confidence: float = 0.0
    tags: list[str] = field(default_factory=list)
    custom_fields: dict[str, str | int | float] = field(default_factory=dict)

    def to_csv_dict(self) -> dict[str, str]:
        import json

        return {
            "email": self.email.strip().lower(),
            "first_name": self.first_name.strip(),
            "last_name": self.last_name.strip(),
            "organisation": self.organisation.strip(),
            "role": self.role.strip(),
            "source_url": self.source_url,
            "confidence": f"{self.confidence:.2f}",
            "tags": "|".join(t.strip() for t in self.tags if t.strip()),
            "custom_fields": json.dumps(self.custom_fields, ensure_ascii=False),
        }


def write_csv(rows: list[StakeholderRow], path: str | Path) -> int:
    """Schreibt Rows nach CSV. Gibt die Anzahl tatsaechlich geschriebener Zeilen zurueck."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADERS)
        writer.writeheader()
        for row in rows:
            if not row.email:
                continue
            writer.writerow(row.to_csv_dict())
            n += 1
    return n


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Liefert die Zeilen als Dicts mit den Standard-Headern."""
    with Path(path).open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)
