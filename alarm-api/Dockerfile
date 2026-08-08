FROM python:3.12-slim
WORKDIR /workspace
COPY . /workspace
RUN pip install --no-cache-dir -r /workspace/requirements.txt
WORKDIR /workspace/alarm-api
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
