#!/usr/bin/env bash
# Launches the grid API locally. No internet access needed.
#   ./launch.sh              -> venv in .venv/, config/default.json, port 8000
#   GRID_PORT=9000 ./launch.sh
#   GRID_CONFIG=config/my_scenario.json ./launch.sh
#   ./launch.sh --with-viz    -> also installs matplotlib, for GET /viz/graph
set -euo pipefail
cd "$(dirname "$0")/grid_api"

VENV=".venv"
PORT="${GRID_PORT:-8000}"
export GRID_CONFIG="${GRID_CONFIG:-config/default.json}"

if [ ! -d "$VENV" ]; then
    echo "[launch] creating venv in grid_api/$VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r requirements.txt
    if [ "${1:-}" = "--with-viz" ]; then
        "$VENV/bin/pip" install --quiet -r requirements-viz.txt
    fi
fi

echo "[launch] starting grid-api on http://127.0.0.1:$PORT  (config: $GRID_CONFIG)"
exec "$VENV/bin/uvicorn" api.main:app --host 127.0.0.1 --port "$PORT"