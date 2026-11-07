#!/usr/bin/env bash
# Start OpenSEO in a Claude Code cloud session.
#
# - Installs dependencies and prepares the local database if needed.
# - Writes open-seo/.env.local (git-ignored) with a placeholder DataForSEO key;
#   the session's network proxy swaps in the real login saved as a network
#   secret for api.dataforseo.com.
# - Points the app's DataForSEO calls at a localhost forwarder, because the
#   local Cloudflare runtime (workerd) cannot use the session's proxy. That
#   one-line change is hidden from git (skip-worktree) so it never gets committed.
# - Starts the forwarder and the dev server in the background.
#
# Usage: bash openseo-cloud/start.sh     (then open http://localhost:3001)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/open-seo"
HELPER="$ROOT/openseo-cloud"
LOGS="$APP/.logs"
FORWARDER_PORT=8789
CORE="src/server/lib/dataforseo/core.ts"

cd "$APP"
mkdir -p "$LOGS"

if [ ! -d node_modules ]; then
  corepack enable >/dev/null 2>&1 || true
  pnpm install --frozen-lockfile
fi

if [ ! -d .wrangler/state ]; then
  pnpm run db:migrate:local
fi

if [ ! -f .env.local ]; then
  {
    echo "AUTH_MODE=local_noauth"
    # Placeholder only; the proxy replaces the Authorization header.
    echo "DATAFORSEO_API_KEY=$(printf 'proxy:injected' | base64)"
  } > .env.local
fi

if grep -q 'const API_BASE = "https://api.dataforseo.com";' "$CORE"; then
  sed -i "s#const API_BASE = \"https://api.dataforseo.com\";#const API_BASE = \"http://127.0.0.1:${FORWARDER_PORT}\"; // cloud-session forwarder (openseo-cloud/start.sh)#" "$CORE"
  git -C "$ROOT" update-index --skip-worktree "open-seo/$CORE" 2>/dev/null || true
fi

if ! curl -s -o /dev/null "http://127.0.0.1:${FORWARDER_PORT}/"; then
  DFS_FORWARDER_PORT=$FORWARDER_PORT NODE_USE_ENV_PROXY=1 \
    nohup node "$HELPER/dfs-forwarder.mjs" > "$LOGS/forwarder.log" 2>&1 &
fi

if ! curl -s -o /dev/null --max-time 5 "http://localhost:3001/"; then
  nohup pnpm run dev > "$LOGS/dev-server.log" 2>&1 &
  for _ in $(seq 1 120); do
    grep -q "Local:" "$LOGS/dev-server.log" 2>/dev/null && break
    sleep 1
  done
fi

grep -a "Local:" "$LOGS/dev-server.log" || { echo "Dev server did not start; see $LOGS/dev-server.log"; exit 1; }
echo "OpenSEO is running. Forwarder log: $LOGS/forwarder.log"
