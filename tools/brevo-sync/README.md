# brevo-sync

Syncs a stakeholder CSV into any supported ESP or CRM. Switch providers by changing one env var — no code changes needed.

```
contacts.csv  →  sync.py  →  Brevo / Mailchimp / MailerLite / ActiveCampaign / CiviCRM
```

## Quick start

```bash
cd tools/brevo-sync
pip install -r requirements.txt

# Copy and fill .env
cp ../../.env.example ../../.env

# See what lists exist in your ESP
python sync.py list-lists

# Dry-run first (default) — shows what would be synced, nothing is written
python sync.py sync contacts.csv --list-id 42

# Go live
python sync.py sync contacts.csv --list-id 42 --live
```

## Switching ESP

Set `ESP_PROVIDER` in `.env`:

| Value | Status | Notes |
|---|---|---|
| `brevo` | Full | Default. Free up to 100 000 contacts |
| `mailchimp` | Stub | Contribute via PR |
| `mailerlite` | Stub | Great free plan for small NGOs (EU data residency) |
| `activecampaign` | Stub | Contribute via PR |
| `civicrm` | Stub | Open-source nonprofit CRM — see below |

## CSV format

```csv
email,first_name,last_name,tags,custom_fields
presse@spiegel.de,Anna,Mueller,journalist|environment,"{""outlet"": ""Der Spiegel""}"
```

| Column | Required | Notes |
|---|---|---|
| `email` | yes | Used as the unique upsert key — no duplicates |
| `first_name` | no | |
| `last_name` | no | |
| `tags` | no | Pipe-separated: `journalist\|environment` |
| `custom_fields` | no | JSON string of extra attributes |

## CiviCRM — the NGO-native option

If your organisation already runs CiviCRM (used by Amnesty International, Greenpeace, and 11 000+ NGOs worldwide), point `ESP_PROVIDER=civicrm` and the sync writes directly into your existing database — no third-party service required.

CiviCRM handles donors, volunteers, event participants, and press contacts in one system, with native SEPA direct debit, membership management, and grant tracking. See `tools/adapters/esp/civicrm.py` for setup notes.

## Auth (Brevo)

Set `BREVO_API_KEY` in `.env`. Generate a key at: https://app.brevo.com/security/api-keys

Global suppression (bounces, complaints, opt-outs) is respected automatically — no override possible. This is a GDPR requirement.

## You know it worked when

- `list-lists` returns your actual lists with correct IDs
- Dry-run shows the expected number of contacts in the log output
- After `--live`, contacts appear in your ESP within seconds
- Re-running with the same CSV does not create duplicates
