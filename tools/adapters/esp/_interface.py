"""
Contract every ESP adapter must satisfy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Contact:
    email: str
    first_name: str = ""
    last_name: str = ""
    tags: list[str] | None = None
    custom_fields: dict[str, str] | None = None


class ESPAdapter(ABC):
    """Minimal interface for syncing contacts into any ESP or CRM."""

    @abstractmethod
    def upsert_contact(self, contact: Contact, list_id: str) -> None:
        """Create or update a contact and add them to list_id."""

    @abstractmethod
    def ensure_fields(self, fields: list[dict]) -> None:
        """Create missing custom fields defined in brevo.yaml (or equivalent)."""

    @abstractmethod
    def list_lists(self) -> list[dict]:
        """Return all available lists / groups / tags in the ESP."""
