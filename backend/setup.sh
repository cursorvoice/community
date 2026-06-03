#!/usr/bin/env bash
# Cursor Voice community backend — guided deploy.
#
# Run from the repo's backend/ folder:   bash setup.sh
# Prereqs: Node 18+ (you have it if `node -v` works). Uses npx, no global install.
#
# It automates everything it can. Three things only YOU can do (your accounts):
#   1. Approve the Cloudflare login in the browser (wrangler login).
#   2. Paste your Google "Web application" OAuth client ID.
#   3. Paste a GitHub token (fine-grained, Issues: read/write on cursorvoice/community).
set -euo pipefail
cd "$(dirname "$0")"
WR="npx --yes wrangler@3"

echo "==> 1/6  Cloudflare login (approve in the browser)…"
$WR whoami >/dev/null 2>&1 || $WR login

echo "==> 2/6  Creating KV namespace 'KNOWN'…"
KV_OUT="$($WR kv namespace create KNOWN 2>&1 || true)"
echo "$KV_OUT"
KV_ID="$(printf '%s' "$KV_OUT" | grep -oE '[0-9a-f]{32}' | head -1)"
if [ -n "$KV_ID" ]; then
  sed -i '' "s/PASTE_KV_NAMESPACE_ID_HERE/$KV_ID/" wrangler.toml
  echo "    wrote KV id $KV_ID into wrangler.toml"
else
  echo "    Couldn't auto-detect the KV id. Paste it into wrangler.toml manually, then re-run."
fi

echo "==> 3/6  Google Web OAuth client"
echo "    In Google Cloud Console (same project as the app) → Credentials →"
echo "    Create OAuth client → Web application → Authorized JS origin:"
echo "      https://community.cursorvoice.app"
read -r -p "    Paste the Web client ID (…apps.googleusercontent.com): " WEB_ID
if [ -n "$WEB_ID" ]; then
  sed -i '' "s/WEB_CLIENT_ID.apps.googleusercontent.com/$WEB_ID/" wrangler.toml
  echo "    set GOOGLE_AUDS web client."
fi

echo "==> 4/6  GitHub token (Issues: read/write on cursorvoice/community)"
echo "    Create at github.com/settings/tokens (fine-grained). You'll paste it next."
$WR secret put GITHUB_TOKEN

echo "==> 5/6  Deploying (also creates the api.cursorvoice.app route + DNS)…"
$WR deploy

echo "==> 6/6  Point the site at the backend"
if [ -n "${WEB_ID:-}" ]; then
  CFG="../config.js"
  sed -i '' "s#API_BASE: \"\"#API_BASE: \"https://api.cursorvoice.app\"#" "$CFG"
  sed -i '' "s#GOOGLE_CLIENT_ID: \"\"#GOOGLE_CLIENT_ID: \"$WEB_ID\"#" "$CFG"
  echo "    Updated ../config.js. Now commit & push to switch the site to real login:"
  echo "      git add -A && git commit -m 'enable community backend' && git push"
else
  echo "    Add API_BASE + GOOGLE_CLIENT_ID to ../config.js, then commit & push."
fi
echo
echo "Done. The backend is live at https://api.cursorvoice.app"
