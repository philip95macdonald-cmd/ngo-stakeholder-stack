# Quickstart — NGO Stakeholder Stack

Vom `git clone` bis zum ersten erfolgreichen Smoketest in 15 Minuten. Keine
Vorkenntnisse über den Code nötig — Claude oder ein anderer Engineer kann
das hier direkt durchgehen.

## 0 · Voraussetzungen

| Was | Check |
|---|---|
| macOS oder Linux | — |
| Python 3.10+ | `python3 --version` |
| Git | `git --version` |
| (Optional) Brevo-Account | Anmeldung unter `brevo.com` (kostenlos für die ersten 300 Mails/Tag) |

## 1 · Repo klonen + Installer

```bash
git clone <repo-url> ngo-stakeholder-stack
cd ngo-stakeholder-stack
bash install.sh --with-deps
```

`install.sh --with-deps` macht:

- Python venv anlegen unter `.venv/`
- Top-level Requirements installieren
- Pro Tool die `requirements.txt` installieren
- `.env` aus `.env.example` ableiten falls fehlend
- Ausgabe-Verzeichnisse anlegen (`output/`, `logs/`)

## 2 · Konfiguration

Drei Configs müssen existieren, alle mit `.example`-Vorlagen mitgeliefert:

```bash
cp .env.example .env
cp configs/ngo.example.yaml      configs/ngo.yaml
cp configs/sources.example.yaml  configs/sources.yaml
cp configs/brevo.example.yaml    configs/brevo.yaml
```

### `.env`

```ini
# Pflicht für brevo-sync
BREVO_API_KEY=xkeysib-...

# Pflicht für themen-monitor (mindestens eine Quelle)
TWITTER_BEARER_TOKEN=
YOUTUBE_API_KEY=

# Pflicht für Krisen-Mail-Versand
SMTP_HOST=
SMTP_USER=
SMTP_PASS=
SMTP_FROM=alerts@deine-ngo.org
SMTP_TO=team@deine-ngo.org
```

### `configs/ngo.yaml`

```yaml
ngo:
  name: "Deine NGO e.V."
  legal_name: "Deine NGO eingetragener Verein"
  domain: "deine-ngo.org"
  legal_form: "e.V."  # oder gGmbH, Stiftung, gAG
  themes:
    - klimaschutz
    - energiewende
    - mobilitaetswende
  regions:
    - "DE"
    - "EU"
  brand:
    primary_color: "#00A86B"
    tone: "informal"   # oder "formal" für Sie-Form
    salutation: "Du"   # oder "Sie"
```

### `configs/sources.yaml`

Quellen für Crawler und Monitor — siehe [`configs/sources.example.yaml`](configs/sources.example.yaml)
für die volle Struktur.

### `configs/brevo.yaml`

Listen-IDs (in Brevo anlegen, IDs hier eintragen) und Tag-Schema.

## 3 · Smoketest

```bash
bash scripts/smoke.sh
```

Erwartete Ausgabe (gekürzt):

```
[smoke] _shared imports        ✓
[smoke] journalisten-crawler   ✓
[smoke] politik-connector      ✓
[smoke] brevo-sync             ✓ (Dry-Run, kein API-Call)
[smoke] themen-monitor         ✓ (Mock-Modus)
[smoke] impact-story-builder   ✓
─────────────────────────────────
[smoke] 6/6 OK
```

Wenn alle Checks grün sind: Setup ist sauber.

## 4 · Erste Live-Operationen

### a) Politik-Connector live

```bash
cd tools/politik-connector
python main.py fetch --parliament bundestag --output ../../output/politiker.csv
```

Ergebnis: CSV mit allen aktuellen Bundestagsabgeordneten, ihrer
E-Mail-Adresse (sofern öffentlich), Partei, Wahlkreis und
Ausschuss-Mitgliedschaften.

### b) Brevo-Sync (Dry-Run!)

```bash
cd tools/brevo-sync
python sync.py list-lists                     # zeigt deine Brevo-Listen
python sync.py sync ../../output/politiker.csv \
    --list-id <bundestag-list-id> --dry-run
```

Im Dry-Run werden keine Daten an Brevo geschickt. Erst wenn das Output
plausibel aussieht, ohne `--dry-run` ausführen.

### c) Themen-Monitor (Mock)

```bash
cd tools/themen-monitor
python main.py --mock --report-only           # erzeugt HTML-Report ohne API-Calls
open ../../output/themen-monitor/report-*.html
```

## 5 · Häufige Stolpersteine

| Problem | Lösung |
|---|---|
| `Brevo API: 401 Unauthorized` | API-Key in `.env` prüfen. IP-Allowlist im Brevo-Dashboard ggf. erweitern. |
| `robots.txt forbidden` beim Crawlen | Crawler hält sich an robots.txt. Domain in Sources-Liste streichen oder rechtliche Klärung. |
| `Abgeordnetenwatch 429 Rate Limited` | Throttle in `tools/politik-connector/config.yaml` erhöhen (Default 1 req/s). |
| Kein Output beim Themen-Monitor | Mock-Modus aktiv? Mit `--live` nochmal. API-Keys gesetzt? |

## 6 · Automatischen Tages-Report via GitHub einrichten

Der Monitor läuft jeden Morgen um 7 Uhr automatisch über GitHub Actions —
kostenlos, kein eigener Server nötig. Dafür müssen einmalig API-Keys als
GitHub Secrets hinterlegt werden.

### Schritt 1: Repo auf GitHub forken/klonen (falls noch nicht geschehen)

Das Repo muss auf deinem GitHub-Account liegen. Dann:

### Schritt 2: GitHub Secrets setzen

Gehe zu: **Repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret-Name | Wert | Pflicht? |
|---|---|---|
| `BREVO_API_KEY` | dein Brevo API-Key | für Kontakt-Sync |
| `SMTP_HOST` | z.B. `smtp.strato.de` | für Mail-Report |
| `SMTP_PORT` | `587` | für Mail-Report |
| `SMTP_USER` | Absender-Adresse | für Mail-Report |
| `SMTP_PASS` | SMTP-Passwort | für Mail-Report |
| `SMTP_FROM` | `alerts@deine-ngo.org` | für Mail-Report |
| `SMTP_TO` | `team@deine-ngo.org` | für Mail-Report |
| `TWITTER_BEARER_TOKEN` | Bearer-Token aus X Developer Portal | optional |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | optional |

### Schritt 3: Configs committen

Die Konfigurationen in `configs/` enthalten keine Secrets und müssen
committet sein, damit der GitHub-Action-Run sie findet:

```bash
git add configs/ngo.yaml configs/sources.yaml configs/brevo.yaml
git commit -m "feat: NGO-Konfiguration"
git push
```

### Schritt 4: Workflow manuell testen

Bevor der Cron-Job läuft, einmal manuell anstoßen:

**GitHub → Actions → "Daily Themen-Monitor" → "Run workflow" → Modus: live**

Den Report findest du danach unter: **Actions → letzter Run → Artifacts → themen-monitor-report-…**

### Schritt 5: Fertig

Ab jetzt landet jeden Morgen ein Report in der Inbox. Bei Krisen-Alarm
(Volume-Spike oder Sentiment-Drift) kommt sofort eine separate Warn-Mail.

---

## 7 · Was als nächstes

Lies [`docs/briefing.html`](docs/briefing.html) für die volle
Adaption-Roadmap und Phasen-Plan. Für die ersten Schritte besonders
relevant: die "Für den nächsten Claude"-Sektion ganz unten.
