#!/usr/bin/env bash
# start.sh — Start all 5 services and open the UI
# Usage: ./start.sh
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
  echo "ERROR: .venv not found. Run: uv venv --python 3.12 && uv pip install -r requirements.txt"
  exit 1
fi

echo "Starting all services..."

# 1 — Alarm API
ALARM_API_TOKEN=demo-token \
  "$PYTHON" -m uvicorn alarm-api.main:app --port 8000 \
  > /tmp/alarm-api.log 2>&1 &

# 2 — Alarm Management MCP
ALARM_API_BASE_URL=http://localhost:8000 ALARM_API_TOKEN=demo-token \
  "$PYTHON" -m uvicorn mcp-servers.alarm-management.server:app --port 9000 \
  > /tmp/alarm-mcp.log 2>&1 &

# 3 — Ticketing MCP
"$PYTHON" -m uvicorn mcp-servers.ticketing.server:app --port 9001 \
  > /tmp/ticketing-mcp.log 2>&1 &

# 4 — Backend (wait a moment for MCP servers to be up)
sleep 2
cd "$ROOT/apps/backend"
OLLAMA_MODEL=qwen3.5:2b \
  OLLAMA_BASE_URL=http://localhost:11434/v1 \
  MCP_ALARM_URL=http://localhost:9000 \
  MCP_TICKETING_URL=http://localhost:9001 \
  "$PYTHON" -m uvicorn api:app --port 8080 \
  > /tmp/backend.log 2>&1 &
cd "$ROOT"

# 5 — Frontend
sleep 2
BACKEND_URL=http://localhost:8080 BACKEND_TIMEOUT=180 \
  "$PYTHON" apps/frontend/app.py \
  > /tmp/frontend.log 2>&1 &

# Wait for frontend to be ready
echo -n "Waiting for services"
for i in $(seq 1 20); do
  sleep 1
  echo -n "."
  if curl -s http://localhost:7860 > /dev/null 2>&1; then
    echo ""
    echo "All services running!"
    echo "  Alarm API   → http://localhost:8000"
    echo "  Alarm MCP   → http://localhost:9000"
    echo "  Ticketing   → http://localhost:9001"
    echo "  Backend     → http://localhost:8080"
    echo "  Frontend UI → http://localhost:7860"
    # Open in browser
    if command -v open &>/dev/null; then open http://localhost:7860
    elif command -v xdg-open &>/dev/null; then xdg-open http://localhost:7860
    fi
    exit 0
  fi
done

echo ""
echo "Timed out waiting for frontend. Check /tmp/frontend.log"
exit 1
