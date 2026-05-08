[![CI](https://github.com/philip95macdonald-cmd/ngo-stakeholder-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/philip95macdonald-cmd/ngo-stakeholder-stack/actions)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)

# NGO Stakeholder Stack

Open-source Python toolkit for NGO press and stakeholder communication.
Replaces ~80% of a Meltwater or Cision subscription at zero recurring cost.

---

## For NGO decision-makers

### What it replaces

| Tool | Typical cost | This stack |
|---|---|---|
| Meltwater (monitoring + media DB) | ~€500/month | €0 |
| Cision (press database) | ~€300/month | €0 |
| Brevo/Mailchimp (contacts + email) | €0–50/month | €0 (free tiers) |
| **Total** | **~€800+/month** | **€0** |

### What it does

- **Finds journalists** — crawls publisher Impressum pages, extracts press contacts via NER, respects robots.txt
- **Monitors your topics** — daily digest of news, alliances, crises, and funding opportunities across configurable sources
- **Connects to politics** — pulls politician data from Abgeordnetenwatch (Bundestag, Landtage)
- **Syncs contacts** — pushes your stakeholder list into Brevo, MailerLite, or CiviCRM with one command
- **Builds impact stories** — structures beneficiary narratives into publication-ready Markdown

### In 3 days you can have

- Day 1: Journalist database for your beat (crawl 20–50 publishers)
- Day 2: Daily topic monitor running on GitHub Actions (free, automated)
- Day 3: Stakeholder list synced into your ESP, segmented by tag

### Who this is for

Small-to-medium NGOs with one communications person and no dedicated tech budget.
You need basic Python skills to configure it (or a volunteer developer for initial setup).

---

## For developers

### Architecture

```
ngo-stakeholder-stack/
├── tools/
│   ├── _shared/               HTTP client, logging, config loader
│   ├── adapters/esp/          ESP/CRM adapters (swap with one env var)
│   │   ├── _interface.py      Abstract contract
│   │   ├── brevo.py           Full implementation
│   │   ├── mailchimp.py       Stub — contribute via PR
│   │   ├── mailerlite.py      Stub (popular with small EU NGOs)
│   │   ├── activecampaign.py  Stub
│   │   └── civicrm.py         Stub — open-source nonprofit CRM
│   ├── journalisten-crawler/  Press contact crawler (49 tests)
│   ├── politik-connector/     Abgeordnetenwatch + Bundestag API
│   ├── brevo-sync/            CSV → ESP sync CLI
│   ├── themen-monitor/        Topic + crisis + alliance monitor
│   └── impact-story-builder/  Beneficiary story structuring
├── configs/
│   ├── ngo.example.yaml       Top-level config (name, topics, brand)
│   ├── sources.example.yaml   Source lists (media, politics, funders)
│   └── brevo.example.yaml     List and field mapping
├── .github/workflows/
│   ├── ci.yml                 Test suite on push
│   └── daily-monitor.yml      Scheduled topic monitor (runs at 06:00 UTC)
└── .env.example               API key template
```

### Setup

```bash
git clone https://github.com/philip95macdonald-cmd/ngo-stakeholder-stack
cd ngo-stakeholder-stack
bash install.sh --with-deps
cp .env.example .env && $EDITOR .env
cp configs/ngo.example.yaml configs/ngo.yaml && $EDITOR configs/ngo.yaml
bash scripts/smoke.sh
```

When `smoke.sh` exits green, the stack is ready. Each tool has its own README with step-by-step instructions.

### ESP adapter pattern

Switch contact destination by setting `ESP_PROVIDER` in `.env`:

```bash
ESP_PROVIDER=brevo          # default
ESP_PROVIDER=mailerlite     # good free plan, EU data residency
ESP_PROVIDER=civicrm        # if your NGO already runs CiviCRM
```

Each adapter implements the same 3-method interface (`upsert_contact`, `ensure_fields`, `list_lists`). To add a new provider, copy any stub and fill in the three methods.

### Automated monitoring (GitHub Actions)

`.github/workflows/daily-monitor.yml` runs the topic monitor at 06:00 UTC every day and emails the digest to your comms team. No server required — runs on GitHub's free tier.

To activate: add `MONITOR_EMAIL` and your SMTP credentials as GitHub Actions secrets.

### Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Crawling | Playwright (JS-rendered pages), requests |
| NLP | spaCy (NER for contact extraction) |
| ESP/CRM | Brevo, MailerLite, CiviCRM (via adapter) |
| CI/CD | GitHub Actions |
| Compliance | GDPR-compliant by default — consent timestamps, suppression-list respected |

### Contributing

The stub adapters (Mailchimp, MailerLite, ActiveCampaign, CiviCRM) are the easiest entry points. Each one is ~30 lines. See `tools/adapters/esp/_interface.py` for the contract.

## License

MIT
