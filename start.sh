#!/usr/bin/env bash
#
# start.sh — start the Stock Analytics service.
#
# One script for both environments:
#   - Local dev:  ./start.sh   (sets up venv, installs deps, dev creds, browser)
#   - Railway:    bash start.sh (invoked via railway.json / Procfile)
#
# Railway is detected via $RAILWAY_ENVIRONMENT (injected by the platform).
#
# Auth credentials are required (the app refuses to start without them).
# Locally they default to me/secret; override by exporting first:
#   APP_USERNAME=me APP_PASSWORD=secret ./start.sh
# On Railway, set APP_USERNAME / APP_PASSWORD in the dashboard (Variables tab).
#
set -euo pipefail

# Resolve the project root so the script works from any directory.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ -n "${RAILWAY_ENVIRONMENT:-}" ]; then
  IS_LOCAL=0
else
  IS_LOCAL=1
fi

# --- Local-only setup -------------------------------------------------------
# On Railway deps are installed at build time (Railpack) and creds come from
# the dashboard, so this block runs only for local dev.
if [ "$IS_LOCAL" -eq 1 ]; then
  if [ ! -d "venv" ]; then
    echo "==> Creating virtualenv (venv)..."
    python3 -m venv venv
  fi
  # shellcheck disable=SC1091
  source venv/bin/activate

  echo "==> Installing dependencies..."
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt

  # Default to dev creds if unset.
  export APP_USERNAME="${APP_USERNAME:-me}"
  export APP_PASSWORD="${APP_PASSWORD:-secret}"
  echo "==> Login: user='${APP_USERNAME}' password='${APP_PASSWORD}'"

  # Bring up a local PostgreSQL container and point the app at it.
  # On Railway, DATABASE_PUBLIC_URL is provided by the dashboard instead.
  echo "==> Starting local PostgreSQL (Docker)..."
  docker compose up -d postgres
  echo "==> Waiting for PostgreSQL to be ready..."
  until docker compose exec -T postgres pg_isready -U stocks -d stocks >/dev/null 2>&1; do
    sleep 1
  done
  export DATABASE_PUBLIC_URL="${DATABASE_PUBLIC_URL:-postgresql://stocks:stocks@localhost:5432/stocks}"
fi

# Ensure imports from src/ resolve in both environments.
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
export PORT="${PORT:-8501}"

# --- Crawler ----------------------------------------------------------------
# Start the data crawler in the background (populates data/stocks.db every 5 min).
echo "==> Starting crawler (background)..."
python src/crawler.py &
CRAWLER_PID=$!
# Stop the crawler when this script exits (mainly useful for local Ctrl-C).
trap 'kill "${CRAWLER_PID}" 2>/dev/null || true' EXIT

# --- Dashboard --------------------------------------------------------------
# Local: bind to localhost and let the browser open.
# Railway: bind to 0.0.0.0 in headless mode on the injected $PORT.
if [ "$IS_LOCAL" -eq 1 ]; then
  echo "==> Starting Streamlit dashboard on http://localhost:${PORT}"
  exec streamlit run src/app.py \
    --server.port "${PORT}" \
    --server.address localhost
else
  exec streamlit run src/app.py \
    --server.port "${PORT}" \
    --server.address 0.0.0.0 \
    --server.headless true
fi
