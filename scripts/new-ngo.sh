#!/usr/bin/env bash
# =============================================================================
# NGO Stakeholder Stack — Einrichtungs-Assistent
#
# Fuehrt durch die Erstkonfiguration und generiert alle Config-Dateien.
# Aufruf: bash scripts/new-ngo.sh
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── Farben ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; RESET='\033[0m'

h1()  { echo -e "\n${BOLD}${CYAN}$*${RESET}"; }
h2()  { echo -e "\n${BOLD}$*${RESET}"; }
ok()  { echo -e "${GREEN}  OK  ${RESET} $*"; }
warn(){ echo -e "${YELLOW}  --  ${RESET} $*"; }

ask() {
  # ask "Prompt" "default_value" → reads into variable $REPLY
  local prompt="$1" default="${2:-}"
  if [ -n "$default" ]; then
    read -rp "  ${prompt} [${default}]: " REPLY
    REPLY="${REPLY:-$default}"
  else
    read -rp "  ${prompt}: " REPLY
  fi
}

ask_secret() {
  local prompt="$1"
  read -rsp "  ${prompt}: " REPLY
  echo
}

# ── Header ───────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}╔══════════════════════════════════════════════════════════╗"
echo -e "║   NGO Stakeholder Stack — Einrichtungs-Assistent        ║"
echo -e "╚══════════════════════════════════════════════════════════╝${RESET}"
echo
echo "Dieser Assistent erstellt:"
echo "  • configs/ngo.yaml       — Stammdaten deiner NGO"
echo "  • configs/sources.yaml   — Medien, Allianzpartner, Keywords"
echo "  • .env                   — API-Keys (nur lokal, nie commiten)"
echo
echo "Dauer: ~3 Minuten. Alle Werte lassen sich danach jederzeit in"
echo "den Dateien anpassen."
echo
read -rp "Enter druecken um zu starten..."

# ═══════════════════════════════════════════════════════════════════
h1 "Schritt 1 / 5 — Grunddaten deiner NGO"
# ═══════════════════════════════════════════════════════════════════

ask "NGO-Name (z.B. Klimaschutz Bayern e.V.)" "Meine NGO e.V."
NGO_NAME="$REPLY"

ask "Domain (ohne https://, z.B. klimaschutz-bayern.org)" "meine-ngo.org"
NGO_DOMAIN="$REPLY"

ask "Rechtliche Form (e.V. / gGmbH / Stiftung / gAG)" "e.V."
NGO_LEGAL_FORM="$REPLY"

ask "Gruendungsjahr" "2020"
NGO_FOUNDED="$REPLY"

ask "Finanzamt (fuer Spendenbescheinigungen)" "Berlin-Mitte"
NGO_FINANZAMT="$REPLY"

ask "Steuernummer (Format XX/XXX/XXXXX)" "00/000/00000"
NGO_STEUERNR="$REPLY"

# ═══════════════════════════════════════════════════════════════════
h1 "Schritt 2 / 5 — Themen & Region"
# ═══════════════════════════════════════════════════════════════════

echo
echo "  Kernthemen werden als Google-News-Keywords und Monitor-Filter"
echo "  genutzt. 3-5 Stichworte empfohlen, kommagetrennt."
echo

ask "Kernthemen" "klimaschutz,energiewende,nachhaltigkeit"
THEMES_RAW="$REPLY"

ask "Region (DE / EU / intl — Mehrere kommagetrennt)" "DE"
REGIONS_RAW="$REPLY"

ask "Bundesland-Kuerzel fuer Landtag-Connector (z.B. BW,NRW — leer = kein Landtag)" ""
LAENDER_RAW="$REPLY"

ask "Ansprache im Newsletter (Du / Sie)" "Du"
NGO_SALUTATION="$REPLY"

# ═══════════════════════════════════════════════════════════════════
h1 "Schritt 3 / 5 — Allianzpartner & Themen-Medien"
# ═══════════════════════════════════════════════════════════════════

echo
echo "  Allianzpartner werden im Themen-Monitor beobachtet"
echo "  (was machen Partner-NGOs gerade?). Domains kommagetrennt."
echo

ask "Partner-NGO Domains (z.B. bund.net,germanwatch.org)" "bund.net,germanwatch.org"
ALLIANCE_RAW="$REPLY"

echo
echo "  Themen-Medien: RSS-Feeds, die taeglich gelesen werden sollen."
echo "  Format: Name|URL, kommagetrennt."
echo "  Beispiel: klimareporter|https://www.klimareporter.de/rss"
echo

ask "Themen-Medien RSS" "klimareporter|https://www.klimareporter.de/rss"
MEDIA_RAW="$REPLY"

# ═══════════════════════════════════════════════════════════════════
h1 "Schritt 4 / 5 — API-Zugaenge"
# ═══════════════════════════════════════════════════════════════════

echo
echo "  Brevo ist das E-Mail-Marketing-Tool (frueherer Sendinblue)."
echo "  API-Key unter: https://app.brevo.com/security/api-keys"
echo

ask_secret "Brevo API-Key (xkeysib-...)"
BREVO_KEY="$REPLY"

echo
echo "  Twitter/X Bearer-Token ist optional (teuer, viele NGOs nutzen"
echo "  nur Google News + Reddit). Leer lassen = kein Twitter-Monitoring."
echo

ask_secret "Twitter/X Bearer-Token (optional, Enter fuer leer)"
TWITTER_TOKEN="$REPLY"

ask_secret "Slack-Webhook-URL fuer Krisen-Alerts (optional)"
SLACK_WEBHOOK="$REPLY"

# ═══════════════════════════════════════════════════════════════════
h1 "Schritt 5 / 5 — E-Mail-Konfiguration"
# ═══════════════════════════════════════════════════════════════════

echo
echo "  Der taeglich erstellte Monitoring-Report wird an diese Adresse"
echo "  versandt. Braucht einen SMTP-Zugang (z.B. eurer Hosting-Provider)."
echo

ask "Absender-E-Mail (SMTP_FROM)" "alerts@${NGO_DOMAIN}"
SMTP_FROM="$REPLY"

ask "Empfaenger-E-Mail (SMTP_TO, Report-Empfaenger)" "team@${NGO_DOMAIN}"
SMTP_TO="$REPLY"

ask "SMTP-Host (z.B. smtp.strato.de oder mail.hetzner.de)" "smtp.${NGO_DOMAIN}"
SMTP_HOST="$REPLY"

ask "SMTP-Port" "587"
SMTP_PORT="$REPLY"

ask "SMTP-Benutzername (oft = Absender-E-Mail)" "$SMTP_FROM"
SMTP_USER="$REPLY"

ask_secret "SMTP-Passwort"
SMTP_PASS="$REPLY"

# ═══════════════════════════════════════════════════════════════════
h1 "Generiere Konfigurationsdateien..."
# ═══════════════════════════════════════════════════════════════════

# ── Themes als YAML-Liste ─────────────────────────────────────────
themes_yaml=""
IFS=',' read -ra THEMES <<< "$THEMES_RAW"
for t in "${THEMES[@]}"; do
  t="$(echo "$t" | xargs)"
  [ -n "$t" ] && themes_yaml+="    - ${t}"$'\n'
done

# ── Regionen als YAML-Liste ───────────────────────────────────────
regions_yaml=""
IFS=',' read -ra REGIONS <<< "$REGIONS_RAW"
for r in "${REGIONS[@]}"; do
  r="$(echo "$r" | xargs | tr '[:lower:]' '[:upper:]')"
  [ -n "$r" ] && regions_yaml+="    - \"${r}\""$'\n'
done

# ── Bundeslaender als YAML-Liste ──────────────────────────────────
laender_yaml=""
if [ -n "$LAENDER_RAW" ]; then
  IFS=',' read -ra LAENDER <<< "$LAENDER_RAW"
  for l in "${LAENDER[@]}"; do
    l="$(echo "$l" | xargs | tr '[:lower:]' '[:upper:]')"
    [ -n "$l" ] && laender_yaml+="    - \"${l}\""$'\n'
  done
else
  laender_yaml="    [] # Kein Bundesland konfiguriert"$'\n'
fi

# ── Alliance-Partner als YAML ─────────────────────────────────────
alliance_yaml=""
IFS=',' read -ra ALLIANCES <<< "$ALLIANCE_RAW"
for a in "${ALLIANCES[@]}"; do
  a="$(echo "$a" | xargs)"
  if [ -n "$a" ]; then
    name="${a%%.*}"
    alliance_yaml+="    - name: \"${name}\""$'\n'
    alliance_yaml+="      domain: \"${a}\""$'\n'
  fi
done

# ── Google News Keywords aus Themen ───────────────────────────────
gn_yaml=""
for t in "${THEMES[@]}"; do
  t="$(echo "$t" | xargs)"
  [ -n "$t" ] && gn_yaml+="      - \"${t}\""$'\n'
done
gn_yaml+="      - \"${NGO_NAME}\"   # Brand-Mention fuer Krisen-Detektor"$'\n'

# ── Topic Media aus Eingabe ───────────────────────────────────────
media_yaml=""
IFS=',' read -ra MEDIAS <<< "$MEDIA_RAW"
for m in "${MEDIAS[@]}"; do
  m="$(echo "$m" | xargs)"
  if [[ "$m" == *"|"* ]]; then
    mname="${m%%|*}"
    mrss="${m##*|}"
    media_yaml+="    - name: \"${mname}\""$'\n'
    media_yaml+="      rss: \"${mrss}\""$'\n'
  fi
done

# ── configs/ngo.yaml ─────────────────────────────────────────────
cat > configs/ngo.yaml <<YAML
# Generiert von scripts/new-ngo.sh — anpassen nach Bedarf.

ngo:
  name: "${NGO_NAME}"
  legal_name: "${NGO_NAME}"
  domain: "${NGO_DOMAIN}"
  legal_form: "${NGO_LEGAL_FORM}"
  founded_year: ${NGO_FOUNDED}
  charitable_status: true
  finanzamt: "${NGO_FINANZAMT}"
  steuernummer: "${NGO_STEUERNR}"

  themes:
${themes_yaml}
  regions:
${regions_yaml}
  laender:
${laender_yaml}
  brand:
    primary_color: "#00A86B"
    secondary_color: "#1a1a1a"
    tone: "informal"
    salutation: "${NGO_SALUTATION}"
    signature: |
      Herzliche Gruesse,
      das ${NGO_NAME}-Team

datenschutz:
  retention_days_inactive: 730
  consent_double_optin: true
  audit_log_enabled: true
  audit_log_retention_months: 36

lobby:
  register_de: false
  lobbyregister_id: ""
  eu_transparency_register_id: ""

output:
  dir: "./output"
  log_level: "INFO"
YAML
ok "configs/ngo.yaml erstellt"

# ── configs/sources.yaml ──────────────────────────────────────────
cat > configs/sources.yaml <<YAML
# Generiert von scripts/new-ngo.sh — Domains und Quellen anpassen.

journalisten:
  domains_de:
    - "taz.de"
    - "klimareporter.de"
    - "spiegel.de"
    - "zeit.de"
    # Eigene themenrelevante Medien ergaenzen
  domains_eu:
    - "euractiv.com"
    - "politico.eu"
  cap_per_domain: 50
  rate_limit_seconds: 1
  user_agent: "ngo-stakeholder-stack-crawler/0.1 (+https://${NGO_DOMAIN}/bot)"
  respect_robots_txt: true
  follow_publisher_groups: true
  js_domains: []
  publisher_groups:
    - canonical: "spiegel.de"
      members: ["spiegel.de", "spiegel-online.de"]
    - canonical: "faz.net"
      members: ["faz.net", "faznet.de"]
    - canonical: "zeit.de"
      members: ["zeit.de", "zeit-online.de"]

politik:
  parliaments:
    - id: 161
      label: "Bundestag"
      active: true
  include_only_with_email: true
  rate_limit_per_minute: 100
  api_base: "https://www.abgeordnetenwatch.de/api/v2"

themen_monitor:
  schedule: "07:00"

  google_news:
    keywords:
${gn_yaml}
  topic_media:
${media_yaml}
  alliance_partners:
${alliance_yaml}
  funding_sources:
    - name: "DSEE"
      url: "https://www.deutsche-stiftung-fuer-engagement-und-ehrenamt.de/foerderung/"
    - name: "EU Funding Portal"
      url: "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home"

  politik_themen:
    bundestag_keywords:
$(for t in "${THEMES[@]}"; do t="$(echo "$t" | xargs)"; [ -n "$t" ] && echo "      - \"${t}\""; done)

  social:
    twitter_keywords:
$(for t in "${THEMES[@]}"; do t="$(echo "$t" | xargs)"; [ -n "$t" ] && echo "      - \"${t}\""; done)
    youtube_channels: []
    reddit_subreddits:
      - "de"
      - "Umweltschutz"
    mastodon_instances:
      - "https://climatejustice.social"
    bluesky_handles: []

  crisis_detector:
    enabled: true
    volume_spike_factor: 3.0
    sentiment_drift_zscore: 1.5
    history_days: 30
    alert_channels:
      - email
YAML

[ -n "$SLACK_WEBHOOK" ] && echo "      - slack" >> configs/sources.yaml
ok "configs/sources.yaml erstellt"

# ── .env ──────────────────────────────────────────────────────────
cat > .env <<ENV
# Generiert von scripts/new-ngo.sh
# NIEMALS committen — .env ist in .gitignore

BREVO_API_KEY=${BREVO_KEY}

TWITTER_BEARER_TOKEN=${TWITTER_TOKEN}
YOUTUBE_API_KEY=

SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT}
SMTP_USER=${SMTP_USER}
SMTP_PASS=${SMTP_PASS}
SMTP_FROM=${SMTP_FROM}
SMTP_TO=${SMTP_TO}

SLACK_WEBHOOK_URL=${SLACK_WEBHOOK}

LOG_LEVEL=INFO
OUTPUT_DIR=./output
ENV
ok ".env erstellt (nicht committen!)"

# ── configs/brevo.yaml aus Example ────────────────────────────────
if [ ! -f configs/brevo.yaml ]; then
  cp configs/brevo.example.yaml configs/brevo.yaml
  ok "configs/brevo.yaml aus Vorlage erstellt"
fi

# ═══════════════════════════════════════════════════════════════════
h1 "Smoke-Test laufen lassen..."
# ═══════════════════════════════════════════════════════════════════

if bash scripts/smoke.sh; then
  echo
  echo -e "${GREEN}${BOLD}Einrichtung erfolgreich!${RESET}"
else
  echo
  warn "Smoke-Test hat Fehler — bitte Abhaengigkeiten pruefen:"
  warn "  pip install -r requirements.txt"
  warn "  pip install -r tools/themen-monitor/requirements.txt"
fi

# ═══════════════════════════════════════════════════════════════════
h1 "Naechste Schritte"
# ═══════════════════════════════════════════════════════════════════

cat <<NEXT

  1. Demo-Report erstellen (kein API-Key noetig):
     cd tools/themen-monitor && python main.py --mock

  2. Echten Report erstellen (Google News + RSS + Allianzen):
     cd tools/themen-monitor && python main.py --live --report-only

  3. Mail-Versand testen:
     cd tools/themen-monitor && python main.py --live --send-mail

  4. Pressekontakte crawlen:
     cd tools/journalisten-crawler && python main.py list-domains
     cd tools/journalisten-crawler && python main.py crawl --dry-run

  5. Configs/-Verzeichnis committen (kein .env!):
     git add configs/ && git commit -m "feat: NGO config fuer ${NGO_NAME}"

  6. GitHub Secrets setzen fuer automatischen Tages-Report:
     → Repo-Einstellungen → Secrets → BREVO_API_KEY, SMTP_* etc.
     → Dann laeuft der Monitor jeden Morgen automatisch.

  Vollstaendige Doku: docs/briefing.html
  Bei Fragen: README.md → QUICKSTART.md

NEXT
