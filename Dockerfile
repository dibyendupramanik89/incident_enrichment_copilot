# Root Dockerfile — builds the Copilot Backend service by default.
#
# This repo is primarily packaged via docker-compose.yml, which builds all 5
# services (alarm-api, alarm-management-mcp, ticketing-mcp, backend, frontend)
# from per-service Dockerfiles using this repo root as build context.
#
# This root Dockerfile is provided so the project can also be built/run as a
# single image (e.g. `docker build -t copilot-backend .`) per the assignment's
# required repository layout. It builds the backend orchestration service.
FROM python:3.12-slim
WORKDIR /workspace
COPY . /workspace
RUN pip install --no-cache-dir -r /workspace/requirements.txt
WORKDIR /workspace/apps/backend
EXPOSE 8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
