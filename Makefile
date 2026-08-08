VENV := .venv
PYTHON := $(VENV)/bin/python
UV := uv

.PHONY: install rag-index run run-alarm-api run-alarm-mcp run-ticketing-mcp run-backend run-frontend test test-unit test-int test-e2e lint clean help

help:
	@echo "Incident & Ticket Enrichment Copilot — Makefile targets"
	@echo ""
	@echo "  make install        Install all Python dependencies"
	@echo "  make rag-index      Build the BM25 retrieval index"
	@echo "  make run            Start all 5 services (requires 5 terminals or tmux)"
	@echo "  make test           Run full test suite"
	@echo "  make test-unit      Unit tests only"
	@echo "  make test-int       Integration tests only"
	@echo "  make test-e2e       End-to-end test only"
	@echo "  make lint           Run ruff linter"
	@echo "  make clean          Remove __pycache__ and RAG index"

install:
	$(UV) pip install --python $(PYTHON) -r requirements.txt

rag-index:
	$(PYTHON) rag/ingestion/ingest.py

run-alarm-api:
	ALARM_API_BASE_URL=http://localhost:8000 ALARM_API_TOKEN=demo-token \
		$(PYTHON) -m uvicorn alarm-api.main:app --port 8000 --reload

run-alarm-mcp:
	ALARM_API_BASE_URL=http://localhost:8000 ALARM_API_TOKEN=demo-token \
		$(PYTHON) -m uvicorn mcp-servers.alarm-management.server:app --port 9000 --reload

run-ticketing-mcp:
	$(PYTHON) -m uvicorn mcp-servers.ticketing.server:app --port 9001 --reload

run-backend:
	cd apps/backend && \
		MCP_ALARM_URL=http://localhost:9000 MCP_TICKETING_URL=http://localhost:9001 \
		../../$(PYTHON) main.py

run-frontend:
	cd apps/frontend && BACKEND_URL=http://localhost:8080 ../../$(PYTHON) app.py

run:
	@echo "Starting all 5 services in background..."
	@$(PYTHON) -m uvicorn alarm-api.main:app --port 8000 --log-level warning & \
	sleep 2 && \
	ALARM_API_BASE_URL=http://localhost:8000 ALARM_API_TOKEN=demo-token \
		$(PYTHON) -m uvicorn mcp-servers.alarm-management.server:app --port 9000 --log-level warning & \
	sleep 2 && \
	$(PYTHON) -m uvicorn mcp-servers.ticketing.server:app --port 9001 --log-level warning & \
	sleep 2 && \
	cd apps/backend && \
		MCP_ALARM_URL=http://localhost:9000 MCP_TICKETING_URL=http://localhost:9001 \
		../../$(PYTHON) -m uvicorn api:app --port 8080 --log-level warning & \
	sleep 3 && \
	cd apps/frontend && BACKEND_URL=http://localhost:8080 ../../$(PYTHON) app.py
	@echo "Frontend: http://localhost:7860"

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-unit:
	$(PYTHON) -m pytest tests/unit/ -v --tb=short

test-int:
	$(PYTHON) -m pytest tests/integration/ -v --tb=short

test-e2e:
	$(PYTHON) -m pytest tests/e2e/ -v --tb=short

lint:
	$(PYTHON) -m ruff check . --ignore E501

clean:
	find . -name "__pycache__" -not -path "./.venv/*" | xargs rm -rf
	rm -rf rag/.index/
	@echo "Cleaned __pycache__ and RAG index"

check-health:
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@curl -s http://localhost:9000/health | python3 -m json.tool
	@curl -s http://localhost:9001/health | python3 -m json.tool
	@curl -s http://localhost:8080/health | python3 -m json.tool
