"""
MailerLite ESP adapter — stub.

Popular with small German and European NGOs: generous free plan (1 000 contacts,
12 000 emails/month), GDPR-compliant EU data residency.

To implement:
  pip install mailerlite-python
  Set MAILERLITE_API_KEY in .env.
  list_id maps to a MailerLite Group ID (found under Subscribers → Groups).
  Docs: https://developers.mailerlite.com/docs/
"""

from __future__ import annotations

from ._interface import Contact, ESPAdapter


class MailerLiteAdapter(ESPAdapter):
    def upsert_contact(self, contact: Contact, list_id: str) -> None:
        raise NotImplementedError("MailerLite adapter not yet implemented — contribute via PR")

    def ensure_fields(self, fields: list[dict]) -> None:
        raise NotImplementedError

    def list_lists(self) -> list[dict]:
        raise NotImplementedError
