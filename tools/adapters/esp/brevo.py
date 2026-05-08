"""
Brevo (formerly Sendinblue) ESP adapter — full implementation.
"""

from __future__ import annotations

import os
import sys

import requests

from ._interface import Contact, ESPAdapter

API_BASE = "https://api.brevo.com/v3"


class BrevoAdapter(ESPAdapter):
    def __init__(self) -> None:
        key = os.environ.get("BREVO_API_KEY")
        if not key:
            print("✗ BREVO_API_KEY not set in .env", file=sys.stderr)
            sys.exit(2)
        self._headers = {
            "api-key": key,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def _get(self, path: str, **params) -> dict:
        r = requests.get(f"{API_BASE}{path}", headers=self._headers, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, payload: dict) -> dict:
        r = requests.post(f"{API_BASE}{path}", headers=self._headers, json=payload, timeout=30)
        if r.status_code >= 400:
            r.raise_for_status()
        return r.json() if r.content else {}

    def upsert_contact(self, contact: Contact, list_id: str) -> None:
        attributes = {
            "FIRSTNAME": contact.first_name,
            "LASTNAME": contact.last_name,
            **(contact.custom_fields or {}),
        }
        payload = {
            "email": contact.email,
            "attributes": attributes,
            "listIds": [int(list_id)],
            "updateEnabled": True,
            "ext_id": contact.email,
        }
        self._post("/contacts", payload)

    def ensure_fields(self, fields: list[dict]) -> None:
        existing = {
            a["name"]
            for a in self._get("/contacts/attributes").get("attributes", [])
        }
        for field in fields:
            name = field["name"]
            if name not in existing:
                self._post(
                    f"/contacts/attributes/normal/{name}",
                    {"type": field.get("type", "text")},
                )

    def list_lists(self) -> list[dict]:
        return self._get("/contacts/lists", limit=50, offset=0).get("lists", [])
