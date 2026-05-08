"""
ActiveCampaign ESP adapter — stub.

To implement:
  Set ACTIVECAMPAIGN_API_URL and ACTIVECAMPAIGN_API_KEY in .env.
  list_id maps to an ActiveCampaign List ID.
  Use the /contacts endpoint with contact.lists for the upsert.
  Docs: https://developers.activecampaign.com/reference/
"""

from __future__ import annotations

from ._interface import Contact, ESPAdapter


class ActiveCampaignAdapter(ESPAdapter):
    def upsert_contact(self, contact: Contact, list_id: str) -> None:
        raise NotImplementedError("ActiveCampaign adapter not yet implemented — contribute via PR")

    def ensure_fields(self, fields: list[dict]) -> None:
        raise NotImplementedError

    def list_lists(self) -> list[dict]:
        raise NotImplementedError
