"""
Mailchimp ESP adapter — stub.

To implement:
  pip install mailchimp-marketing
  Set MAILCHIMP_API_KEY and MAILCHIMP_SERVER_PREFIX (e.g. "us1") in .env.
  list_id maps to Mailchimp Audience ID (found under Audience → Settings).
"""

from __future__ import annotations

from ._interface import Contact, ESPAdapter


class MailchimpAdapter(ESPAdapter):
    def upsert_contact(self, contact: Contact, list_id: str) -> None:
        raise NotImplementedError("Mailchimp adapter not yet implemented — contribute via PR")

    def ensure_fields(self, fields: list[dict]) -> None:
        raise NotImplementedError

    def list_lists(self) -> list[dict]:
        raise NotImplementedError
