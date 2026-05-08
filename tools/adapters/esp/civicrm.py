"""
CiviCRM adapter — stub.

CiviCRM is the open-source CRM built for nonprofits. Used by 11 000+ NGOs worldwide,
including Amnesty International, Greenpeace, and most large German civil-society
organisations. It runs on-premise (full data sovereignty) or on low-cost managed
hosting (CiviHosting, Compucorp, etc.).

Why this matters for NGOs vs. Brevo/Mailchimp:
  - Handles donors, volunteers, event participants, and press contacts in one system
  - Native SEPA direct debit, membership management, grant tracking
  - No per-contact pricing — cost scales to €0 on self-hosted
  - DSGVO: your data stays on your server

To implement:
  1. Install CiviCRM on WordPress, Drupal, or Joomla (civicrm.org/download)
  2. Enable the REST API (Admin → System Settings → API Explorer)
  3. Create an API key for a service user
  4. Set CIVICRM_BASE_URL, CIVICRM_SITE_KEY, CIVICRM_API_KEY in .env
  5. Use the /civicrm/ajax/rest endpoint:
       POST entity=Contact&action=create&json={"email":"…","first_name":"…"}
  6. list_id maps to a CiviCRM Group ID (find via: entity=Group&action=get)

Reference: https://docs.civicrm.org/dev/en/latest/api/
"""

from __future__ import annotations

from ._interface import Contact, ESPAdapter


class CiviCRMAdapter(ESPAdapter):
    def upsert_contact(self, contact: Contact, list_id: str) -> None:
        raise NotImplementedError("CiviCRM adapter not yet implemented — contribute via PR")

    def ensure_fields(self, fields: list[dict]) -> None:
        raise NotImplementedError

    def list_lists(self) -> list[dict]:
        raise NotImplementedError
