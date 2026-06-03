#!/usr/bin/env bash
# One-shot runner for the Cursor Voice submission review bot.
#   1) cp .env.example .env   and fill it in
#   2) bash run.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then set -a; source .env; set +a; fi

: "${DISCORD_TOKEN:?Set DISCORD_TOKEN (copy .env.example to .env and fill it in)}"
: "${GITHUB_TOKEN:?Set GITHUB_TOKEN}"
: "${CHANNEL_ID:?Set CHANNEL_ID}"

python3 -m pip install --quiet --upgrade -r requirements.txt
exec python3 review_bot.py
