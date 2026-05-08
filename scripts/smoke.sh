#!/usr/bin/env bash
# End-to-End Smoke-Test fuer den NGO Stakeholder Stack.
# Idempotent, exit-code-basiert (0 = OK, !=0 = Fehler).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0
SKIP=0

check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "[smoke] $name ✓"
    PASS=$((PASS + 1))
  else
    echo "[smoke] $name ✗"
    FAIL=$((FAIL + 1))
  fi
}

# Aktiviere venv falls vorhanden
if [ -d .venv ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

echo "─── NGO Stakeholder Stack Smoke-Test ─────────────────────────"

# 1) _shared
check "_shared imports + config-loader" \
  python3 -c "import sys; sys.path.insert(0, 'tools'); from _shared.config_loader import load_config; load_config()"

# 2) journalisten-crawler
check "journalisten-crawler config-loader" \
  bash -c "cd tools/journalisten-crawler && python3 -c 'import config_loader; config_loader.load_config()'"

# 3) politik-connector
check "politik-connector imports" \
  bash -c "cd tools/politik-connector && python3 -c 'import abgeordnetenwatch, main'"

# 4) brevo-sync (Dummy-Key)
check "brevo-sync help" \
  bash -c "cd tools/brevo-sync && BREVO_API_KEY=ci-smoke-dummy python3 sync.py --help"

# 5) themen-monitor (Mock)
check "themen-monitor mock-run" \
  bash -c "cd tools/themen-monitor && python3 main.py --mock --report-only"

# 6) impact-story-builder Self-Test
check "impact-story-builder self-test" \
  bash -c "cd tools/impact-story-builder && python3 builder.py --self-test"

echo "──────────────────────────────────────────────────────────────"
echo "[smoke] $PASS OK · $FAIL FAIL · $SKIP SKIP"
[ "$FAIL" -eq 0 ]
