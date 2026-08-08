FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp-servers/ticketing/server.py /app/
EXPOSE 9001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9001"]
