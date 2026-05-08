#!/usr/bin/env bash
# Idempotenter Installer für den NGO Stakeholder Stack.
#
# Usage:
#   bash install.sh                # nur Verzeichnisse + .env-Template
#   bash install.sh --with-deps    # zusätzlich Python-Deps in venv installieren

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WITH_DEPS=0
for arg in "$@"; do
  case "$arg" in
    --with-deps) WITH_DEPS=1 ;;
    *) echo "Unbekannte Option: $arg"; exit 1 ;;
  esac
done

echo "→ NGO Stakeholder Stack — Installer"
echo "  Repo: $ROOT"

# 1) Output- und Log-Verzeichnisse
mkdir -p "$ROOT/output"/{politiker,journalisten,themen-monitor,stories,smoke}
mkdir -p "$ROOT/logs"
echo "  ✓ output/ und logs/ angelegt"

# 2) .env aus Template
if [ ! -f "$ROOT/.env" ] && [ -f "$ROOT/.env.example" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "  ✓ .env aus .env.example angelegt — bitte editieren!"
else
  echo "  · .env existiert bereits"
fi

# 3) Configs aus Templates
for cfg in ngo sources brevo; do
  if [ ! -f "$ROOT/configs/$cfg.yaml" ] && [ -f "$ROOT/configs/$cfg.example.yaml" ]; then
    cp "$ROOT/configs/$cfg.example.yaml" "$ROOT/configs/$cfg.yaml"
    echo "  ✓ configs/$cfg.yaml aus Vorlage angelegt"
  fi
done

# 4) Optional: Python-venv + Dependencies
if [ "$WITH_DEPS" = "1" ]; then
  if [ ! -d "$ROOT/.venv" ]; then
    python3 -m venv "$ROOT/.venv"
    echo "  ✓ venv unter .venv/ angelegt"
  fi
  # shellcheck source=/dev/null
  source "$ROOT/.venv/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -r "$ROOT/requirements.txt"
  echo "  ✓ Top-Level Requirements installiert"
  for tool_req in "$ROOT"/tools/*/requirements.txt; do
    [ -f "$tool_req" ] || continue
    pip install --quiet -r "$tool_req"
  done
  echo "  ✓ Tool-Requirements installiert"
fi

echo ""
echo "Setup fertig. Nächste Schritte:"
echo "  1. \$EDITOR .env"
echo "  2. \$EDITOR configs/ngo.yaml"
echo "  3. bash scripts/smoke.sh"
