FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/backend/api.py /app/
COPY apps/backend/orch.py /app/
COPY apps/backend/mcp_client.py /app/
COPY apps/backend/retriever.py /app/
COPY apps/backend/guardrails.py /app/
EXPOSE 8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
